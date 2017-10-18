#!env/python3
# coding: utf-8
import ipdb

import os
import json
import datetime
import uuid
import psycopg2
import hashlib
import asyncio
import ped_parser



from config import *
from core.framework.common import *
from core.model import *










# =====================================================================================================================
# FILTER ENGINE
# =====================================================================================================================


class FilterEngine:
    op_map = {'AND': ' AND ', 'OR': ' OR ', '==': '=', '!=': '<>', '>': '>', '<': '<', '>=': '>=', '<=': '<=', '~': ' LIKE ', '!~': ' NOT LIKE ',
              # As a left join will be done on the chr+pos or chr+pos+ref+alt according to the type of the set operation (by site or by variant)
              # We just need to test if one of the "joined" field is set or not
              'IN': '{0}.chr is not null',
              'NOTIN': '{0}.chr is null'}
    sql_type_map = {'int': 'integer', 'string': 'text', 'float': 'real', 'enum': 'varchar(50)', 'range': 'int8range', 'bool': 'boolean', 'sequence': 'text', 'list' : 'varchar(250)[]'}


    def __init__(self):
        run_until_complete(self.load_annotation_metadata())


    async def load_annotation_metadata(self):
        """
            Init Annso Filtering engine.
            Init mapping collection for annotations databases and fields
        """
        self.fields_map = {}
        self.db_map = {}
        query = "SELECT d.uid AS duid, d.name AS dname, d.name_ui AS dname_ui, d.jointure, d.reference_id, d.type AS dtype, d.db_pk_field_uid, a.uid AS fuid, a.name AS fname, a.type FROM annotation_field a LEFT JOIN annotation_database d ON a.database_uid=d.uid"
        result = await execute_aio(query)
        for row in result:
            if row.duid not in self.db_map:
                self.db_map[row.duid] = {"name": row.dname, "join": row.jointure, "fields": {}, "reference_id": row.reference_id, "type": row.dtype, "db_pk_field_uid" : row.db_pk_field_uid}
            self.db_map[row.duid]["fields"][row.fuid] = {"name": row.fname, "type": row.type}
            self.fields_map[row.fuid] = {"name": row.fname, "type": row.type, "db_uid": row.duid, "db_name_ui": row.dname_ui, "db_name": row.dname, "db_type": row.dtype, "join": row.jointure}







    async def create_working_table(self, analysis):
        # retrieve analysis data
        if analysis is None:
            raise RegovarException("Analysis cannot be null")
        analysis.db_suffix = "_" + execute("SELECT table_suffix FROM reference WHERE id={}".format(analysis.reference_id)).first().table_suffix 
        samples_ids = analysis.samples_ids
        annotations_dbs = analysis.settings["annotations_db"]

        # Retrieve attributes of the analysis
        attributes = {}
        for row in execute("select sample_id, value, name from attribute where analysis_id={0}".format(analysis.id)):
            if row.name not in attributes.keys():
                attributes[row.name] = {row.sample_id: row.value}
            else:
                attributes[row.name].update({row.sample_id: row.value})

        # Retrieve saved filter's ids of the analysis
        filters_ids = []
        for row in execute("select id from filter where analysis_id={0} ORDER BY id ASC".format(analysis.id)):
            filters_ids.append(row.id)

        # We assume that we can use by default head version of all existing panels
        # TODO
        panels_ids = []

        # create wt table
        self.create_wt_schema(analysis, samples_ids, annotations_dbs, attributes, filters_ids, panels_ids)

        # insert variant
        self.insert_wt_variants(analysis, samples_ids, annotations_dbs)

        # set sample's fields (GT, DP, ...)
        self.update_wt_samples_fields(analysis, samples_ids)

        # compute stats and predefined filter (attributes, panels, trio, ...)
        await self.update_wt_stats_prefilters(analysis, samples_ids, attributes, filters_ids, panels_ids)

        # variant's indexes
        self.create_wt_variants_indexes(analysis, samples_ids)

        # insert trx annotations
        self.insert_wt_trx(analysis, samples_ids, annotations_dbs)

        # trx's indexes
        self.create_wt_trx_indexes(analysis, samples_ids)

        # Update count stat of the analysis
        query = "UPDATE analysis SET status='ready', computing_progress=1 WHERE id={}".format(analysis.id)
        log(" > wt is ready")
        execute(query)



    def create_wt_schema(self, analysis, samples_ids, annotations_dbs, attributes, filters_ids, panels_ids):
        wt = "wt_{}".format(analysis.id)
        query = "DROP TABLE IF EXISTS {0} CASCADE; CREATE TABLE {0} (\
            is_variant boolean DEFAULT False, \
            variant_id bigint, \
            bin integer, \
            chr integer, \
            pos bigint, \
            ref text, \
            alt text,\
            trx_pk_uid character varying(32), \
            trx_pk_value character varying(100), \
            is_transition boolean, \
            sample_tlist integer[], \
            sample_tcount integer, \
            sample_alist integer[], \
            sample_acount integer, \
            is_dom boolean DEFAULT False, \
            is_rec_hom boolean DEFAULT False, \
            is_rec_htzcomp boolean DEFAULT False, \
            is_denovo boolean DEFAULT False, \
            is_aut boolean DEFAULT False, \
            is_xlk boolean DEFAULT False, \
            is_mit boolean DEFAULT False, "
        query += ", ".join(["s{}_gt integer".format(i) for i in samples_ids]) + ", "
        query += ", ".join(["s{}_dp integer".format(i) for i in samples_ids]) + ", "
        query += ", ".join(["s{}_qual real".format(i) for i in samples_ids]) + ", "
        query += ", ".join(["s{}_filter JSON".format(i) for i in samples_ids]) + ", "
        query += ", ".join(["s{}_is_composite boolean".format(i) for i in samples_ids]) + ", "

        # Add annotation's columns
        for dbuid in annotations_dbs:
            for fuid in self.db_map[dbuid]["fields"]:
                query += "_{} {}, ".format(fuid, self.sql_type_map[self.fields_map[fuid]['type']])
                
        # Add attribute's columns
        # TODO

        # Add filter's columns
        # TODO

        # Add panel's columns
        # TODO

        query = query[:-2] + ");"
        log(" > create wt schema")
        execute(query.format(wt))


    def insert_wt_variants(self, analysis, samples_ids, annotations_dbs):
        wt = "wt_{}".format(analysis.id)

        # create temp table with id of variants
        query  = "DROP TABLE IF EXISTS {0}_var CASCADE; CREATE TABLE {0}_var (id bigint, trx_count integer); "
        execute(query.format(wt))
        
        query = "INSERT INTO {0}_var (id) SELECT DISTINCT variant_id FROM sample_variant{1} WHERE sample_id IN ({2}); "
        res = execute(query.format(wt, analysis.db_suffix, ",".join([str(sid) for sid in samples_ids])))
        
        # set total number of variant for the analysis
        log(" > {} variants found".format(res.rowcount))
        query = "UPDATE analysis SET total_variants={1} WHERE id={0}".format(analysis.id, res.rowcount)
        
        query += "CREATE INDEX {0}_var_idx_id ON {0}_var USING btree (id);"
        execute(query.format(wt))

        # Insert variants and their annotations
        q_fields = "is_variant, variant_id, bin, chr, pos, ref, alt, is_transition, sample_tlist"
        q_select = "True, _vids.id, _var.bin, _var.chr, _var.pos, _var.ref, _var.alt, _var.is_transition, _var.sample_list"
        q_from   = "{0}_var _vids LEFT JOIN variant{1} _var ON _vids.id=_var.id".format(wt, analysis.db_suffix)

        for dbuid in annotations_dbs:
            if self.db_map[dbuid]["type"] == "variant":
                dbname = "_db_{}".format(dbuid)
                q_from += " LEFT JOIN {0}".format(self.db_map[dbuid]['join'].format(dbname, '_var'))
                q_fields += ", " + ", ".join(["_{}".format(fuid) for fuid in self.db_map[dbuid]["fields"]])
                q_select += ", " + ", ".join(["{}.{}".format(dbname, self.fields_map[fuid]["name"]) for fuid in self.db_map[dbuid]["fields"]])

        # execute query
        query = "INSERT INTO {0} ({1}) SELECT {2} FROM {3};".format(wt, q_fields, q_select, q_from)
        execute(query)


    def update_wt_samples_fields(self, analysis, samples_ids):
        wt = "wt_{}".format(analysis.id)
        for sid in samples_ids:
            execute("UPDATE {0} SET s{2}_gt=_sub.genotype, s{2}_dp=_sub.depth, s{2}_qual=_sub.quality, s{2}_filter=_sub.filter s{2}_is_composite=_sub.is_composite FROM (SELECT variant_id, genotype, depth, is_composite FROM sample_variant{1} WHERE sample_id={2}) AS _sub WHERE {0}.variant_id=_sub.variant_id".format(wt, analysis.db_suffix, sid))


    async def update_wt_stats_prefilters(self, analysis, samples_ids, attributes, filters_ids, panels_ids):
        wt = "wt_{}".format(analysis.id)

        # Variant occurence stats
        query = "UPDATE {0} SET \
            sample_tcount=array_length(sample_tlist,1), \
            sample_alist=array_intersect(sample_tlist, array[{1}]), \
            sample_acount=array_length(array_intersect(sample_tlist, array[{1}]),1)"
        log(" > compute statistics")
        execute(query.format(wt, ",".join([str(i) for i in samples_ids])))
        
        # Attributes
        # TODO

        # Filter
        # TODO

        # Panels
        # TODO

        # Predefinied quickfilters
        if len(samples_ids) == 1:
            await self.update_wt_compute_prefilter_single(analysis, samples_ids[0], "M")
        elif analysis.settings["trio"]:
            self.update_wt_compute_prefilter_trio(analysis, samples_ids, analysis.settings["trio"])
            
        # 
        

    def create_wt_variants_indexes(self, analysis, samples_ids):
        wt = "wt_{}".format(analysis.id)

        # Common indexes for variants
        query = "CREATE INDEX {0}_idx_vid ON {0} USING btree (variant_id);".format(wt)
        query += "".join(["CREATE INDEX {0}_idx_s{1}_gt ON {0} USING btree (s{1}_gt);".format(wt, i) for i in samples_ids])
        query += "".join(["CREATE INDEX {0}_idx_s{1}_dp ON {0} USING btree (s{1}_dp);".format(wt, i) for i in samples_ids])
        query += "".join(["CREATE INDEX {0}_idx_s{1}_qual ON {0} USING btree (s{1}_qual);".format(wt, i) for i in samples_ids])
        #query += "".join(["CREATE INDEX {0}_idx_s{1}_filter ON {0} USING btree (s{1}_filter);".format(wt, i) for i in samples_ids])
        query += "".join(["CREATE INDEX {0}_idx_s{1}_is_composite ON {0} USING btree (s{1}_is_composite);".format(wt, i) for i in samples_ids])
        query = "CREATE INDEX {0}_idx_is_dom ON {0} USING btree (is_dom);".format(wt)
        query = "CREATE INDEX {0}_idx_is_rec_hom ON {0} USING btree (is_rec_hom);".format(wt)
        query = "CREATE INDEX {0}_idx_is_rec_htzcomp ON {0} USING btree (is_rec_htzcomp);".format(wt)
        query = "CREATE INDEX {0}_idx_is_denovo ON {0} USING btree (is_denovo);".format(wt)
        query = "CREATE INDEX {0}_idx_is_aut ON {0} USING btree (is_aut);".format(wt)
        query = "CREATE INDEX {0}_idx_is_xlk ON {0} USING btree (is_xlk);".format(wt)
        query = "CREATE INDEX {0}_idx_is_mit ON {0} USING btree (is_mit);".format(wt)
        execute(query)
        log(" > create index for variants random access")

        # Add indexes on attributes columns
        # TODO

        # Add indexes on filter columns
        # TODO

        # Add indexes on panel columns
        # TODO


    def insert_wt_trx(self, analysis, samples_ids, annotations_dbs):
        wt = "wt_{}".format(analysis.id)

        # Insert trx and their annotations
        q_fields  = "is_variant, variant_id, trx_pk_uid, trx_pk_value, bin, chr, pos, ref, alt, is_transition, sample_tlist, sample_tcount, sample_alist, sample_acount, "
        q_fields += "is_dom, is_rec_hom, is_rec_htzcomp, is_denovo, is_aut, is_xlk, is_mit, "
        q_fields += ", ".join(["s{}_gt".format(i) for i in samples_ids]) + ", "
        q_fields += ", ".join(["s{}_dp".format(i) for i in samples_ids]) + ", "
        q_fields += ", ".join(["s{}_is_composite".format(i) for i in samples_ids])
        
        q_select  = "False, _wt.variant_id, '{0}', {1}.regovar_trx_id, _wt.bin, _wt.chr, _wt.pos, _wt.ref, _wt.alt, _wt.is_transition, _wt.sample_tlist, "
        q_select += "_wt.sample_tcount, _wt.sample_alist, _wt.sample_acount, _wt.is_dom, _wt.is_rec_hom, _wt.is_rec_htzcomp, _wt.is_denovo, "
        q_select += "_wt.is_aut, _wt.is_xlk, _wt.is_mit, "
        q_select += ", ".join(["_wt.s{}_gt".format(i) for i in samples_ids]) + ", "
        q_select += ", ".join(["_wt.s{}_dp".format(i) for i in samples_ids]) + ", "
        q_select += ", ".join(["_wt.s{}_is_composite".format(i) for i in samples_ids])
        
        q_from   = "{0} _wt".format(wt, analysis.db_suffix)

        # first loop over "variant db" in order to set common annotation to trx
        for dbuid in annotations_dbs:
            if self.db_map[dbuid]["type"] == "variant":
                q_fields += ", " + ", ".join(["_{}".format(fuid) for fuid in self.db_map[dbuid]["fields"]])
                q_select += ", " + ", ".join(["_{}".format(fuid) for fuid in self.db_map[dbuid]["fields"]])


        # Second loop to execute insert query by trx annotation db
        for dbuid in annotations_dbs:
            if self.db_map[dbuid]["type"] == "transcript":
                dbname = "_db_{}".format(dbuid)
                q_from_db   = q_from + " INNER JOIN {0}".format(self.db_map[dbuid]['join'].format(dbname, '_wt'))
                q_fields_db = q_fields + ", " + ", ".join(["_{}".format(fuid) for fuid in self.db_map[dbuid]["fields"]])
                pk_uid = self.db_map[dbuid]["db_pk_field_uid"]
                q_select_db = q_select.format(pk_uid, dbname)
                q_select_db += ", " + ", ".join(["{}.{}".format(dbname, self.fields_map[fuid]["name"]) for fuid in self.db_map[dbuid]["fields"]])

                # execute query
                query = "INSERT INTO {0} ({1}) SELECT {2} FROM {3} WHERE _wt.is_variant;".format(wt, q_fields_db, q_select_db, q_from_db)
                res = execute(query)
                log(" > {} trx inserted for {} annotations".format(res.rowcount, self.db_map[dbuid]["name"]))


    def create_wt_trx_indexes(self, analysis, samples_ids):
        # query = "CREATE INDEX {0}_idx_vid ON {0} USING btree (variant_id);".format(w_table)
        # query += "CREATE INDEX {0}_idx_var ON {0} USING btree (bin, chr, pos, trx_pk_uid, trx_pk_value);".format(w_table)
        pass



    async def update_wt_compute_prefilter_single(self, analysis, sample_id, sex="F"):
        wt = "wt_{}".format(analysis.id)

        # Dominant
        if sex == "F":
            query = "UPDATE {0} SET is_dom=True WHERE s{1}_gt>1"
        else: # sex == "M"
            query = "UPDATE {0} SET is_dom=True WHERE chr=23 OR s{1}_gt>1"
        res = await execute_aio(query.format(wt, sample_id))
        log(" > is_dom : {} variants".format(res.rowcount))

        # Recessif Homozygous
        query = "UPDATE {0} SET is_rec_hom=True WHERE s{1}_gt=1"
        res = await execute_aio(query.format(wt, sample_id))
        log(" > is_rec_hom : {} variants".format(res.rowcount))

        # Recessif Heterozygous compoud
        query = "UPDATE {0} SET is_rec_htzcomp=True WHERE s{1}_is_composite"
        res = await execute_aio(query.format(wt, sample_id))
        log(" > is_rec_htzcomp : {} variants".format(res.rowcount))

        # Inherited and denovo are not available for single
        log(" > is_denovo & is_inherited : disabled")

        # Autosomal
        query = "UPDATE {0} SET is_aut=True WHERE chr<23"
        res = await execute_aio(query.format(wt))
        log(" > is_aut : {} variants".format(res.rowcount))

        # X-Linked
        query = "UPDATE {0} SET is_xlk=True WHERE chr=23"
        res = await execute_aio(query.format(wt))
        log(" > is_xlk : {} variants".format(res.rowcount))

        # Mitochondrial
        query = "UPDATE {0} SET is_mit=True WHERE chr=25"
        res = await execute_aio(query.format(wt))
        log(" > is_mit : {} variants".format(res.rowcount))



    def update_wt_compute_prefilter_trio(self, analysis, samples_ids, trio):
        wt  = "wt_{}".format(analysis.id)
        sex = trio["child_sex"]
        child_id = trio["child_id"]
        mother_id = trio["mother_id"]
        father_id = trio["father_id"]
        child_idx = trio["child_index"]
        mother_idx = trio["mother_index"]
        father_idx = trio["father_index"]

        # Dominant
        if sex == "F":
            query = "UPDATE {0} SET is_dom=True WHERE s{1}_gt>1"
        else: # sex == "M"
            query = "UPDATE {0} SET is_dom=True WHERE chr=23 OR s{1}_gt>1"
        res = execute(query.format(wt, child_id))
        log(" > is_dom : {} variants".format(res.rowcount))

        # Recessif Homozygous
        query = "UPDATE {0} SET is_rec_hom=True WHERE s{1}_gt=1"
        res = execute(query.format(wt, child_id))
        log(" > is_rec_hom : {} variants".format(res.rowcount))

        # Recessif Heterozygous compoud
        query = "UPDATE {0} u SET is_rec_htzcomp=True WHERE u.variant_id IN ( SELECT DISTINCT UNNEST(sub.vids) as variant_id FROM ( SELECT array_agg(w.variant_id) as vids, g.name2 FROM {0} w  INNER JOIN refgene{4} g ON g.chr=w.chr AND g.txrange @> w.pos  WHERE  s{1}_gt > 1 AND ( (s{2}_gt > 1 AND (s{3}_gt = NULL or s{3}_gt < 2)) OR (s{3}_gt > 1 AND (s{2}_gt = NULL or s{2}_gt < 2))) GROUP BY name2 HAVING count(*) > 1) AS sub )"
        res = execute(query.format(wt, child_id, mother_id, father_id, analysis.db_suffix))
        log(" > is_rec_htzcomp : {} variants".format(res.rowcount))

        # Inherited and denovo
        query = "UPDATE {0} SET is_denovo=True WHERE s{1}_gt>0 and s{2}_gt=0 and s{3}_gt=0"
        res = execute(query.format(wt, child_id, mother_id, father_id))
        log(" > is_denovo : {} variants".format(res.rowcount))        

        # Autosomal
        query = "UPDATE {0} SET is_aut=True WHERE chr<23"
        res = execute(query.format(wt))
        log(" > is_aut : {} variants".format(res.rowcount))

        # X-Linked
        query = "UPDATE {0} SET is_xlk=True WHERE chr=23 AND s{1}_gt>1 and s{2}_gt>1"
        if trio["child_sex"] == "F": query += " AND s{3}_gt>1"
        res = execute(query.format(wt, child_id, mother_id, father_id))
        log(" > is_xlk : {} variants".format(res.rowcount))

        # mitochondrial
        query = "UPDATE {0} SET is_mit=True WHERE chr=25"
        res = execute(query.format(wt))
        log(" > is_mit : {} variants".format(res.rowcount))



    def create_working_table2(self, analysis, sample_ids):
        """
            Create a working sql table for the analysis to improove speed of filtering/annotation.
            A Working table contains all variants used by the analysis, with all annotations used by filters or displayed
        """
        from core.core import core
        log("Create working table for analysis {}".format(analysis.id))
        if len(sample_ids) == 0: raise RegovarException("No sample... so not able to retrieve data")
        db_ref_suffix= "hg19"  # execute("SELECT table_suffix FROM reference WHERE id={}".format(reference_id)).first().table_suffix
        progress = {"msg": "wt_processing", "start": datetime.datetime.now().ctime(), "analysis_id": analysis.id, "step": 1}
        core.notify_all(None, data=progress)
        # Create schema
        w_table = 'wt_{}'.format(analysis.id)
        query = "DROP TABLE IF EXISTS {0} CASCADE; CREATE TABLE {0} (\
            is_variant boolean DEFAULT False, \
            annotated boolean DEFAULT False, \
            variant_id bigint, \
            bin integer, \
            chr integer, \
            pos bigint, \
            ref text, \
            alt text,\
            trx_pk_uid character varying(32), \
            trx_pk_value character varying(100), \
            is_transition boolean, \
            sample_tlist integer[], \
            sample_tcount integer, \
            sample_alist integer[], \
            sample_acount integer, \
            depth integer, "
        query += ", ".join(["s{}_gt integer".format(i) for i in sample_ids]) + ", "
        query += ", ".join(["s{}_dp integer".format(i) for i in sample_ids]) + ", "
        query += ", ".join(["s{}_is_composite boolean".format(i) for i in sample_ids]) 
        query += ", CONSTRAINT {0}_ukey UNIQUE (variant_id, trx_pk_uid, trx_pk_value));"

        log(" > create wt schema")

        execute(query.format(w_table))
        # Insert variant without annotation first
        query =  "INSERT INTO {0} (variant_id, bin, chr, pos, ref, alt, is_transition, sample_tlist) \
            SELECT DISTINCT sample_variant_{1}.variant_id, sample_variant_{1}.bin, sample_variant_{1}.chr, sample_variant_{1}.pos, sample_variant_{1}.ref, sample_variant_{1}.alt, \
                variant_{1}.is_transition, \
                variant_{1}.sample_list \
            FROM sample_variant_{1} INNER JOIN variant_{1} ON sample_variant_{1}.variant_id=variant_{1}.id \
            WHERE sample_variant_{1}.sample_id IN ({2}) \
            ON CONFLICT (variant_id, trx_pk_uid, trx_pk_value) DO NOTHING;"

        log(" > insert variants")
        execute(query.format(w_table, db_ref_suffix, ','.join([str(i) for i in sample_ids])))
        # Complete sample-variant's associations
        for sid in sample_ids:
            execute("UPDATE {0} SET s{2}_gt=_sub.genotype, s{2}_dp=_sub.depth, s{2}_is_composite=_sub.is_composite FROM (SELECT variant_id, genotype, depth, is_composite FROM sample_variant_{1} WHERE sample_id={2}) AS _sub WHERE {0}.variant_id=_sub.variant_id".format(w_table, db_ref_suffix, sid))

        query = "UPDATE {0} SET \
            is_variant=(CASE WHEN ref<>alt THEN True ELSE False END), \
            sample_tcount=array_length(sample_tlist,1), \
            sample_alist=array_intersect(sample_tlist, array[{1}]), \
            sample_acount=array_length(array_intersect(sample_tlist, array[{1}]),1), \
            depth=GREATEST({2})"
        log(" > compute statistics")
        execute(query.format(w_table, ",".join([str(i) for i in sample_ids]), ", ".join(["s{}_dp".format(i) for i in sample_ids])))
        # Create indexes
        # FIXME : do we need to create index on boolean fields ? Is partition a better way to do for low cardinality fields : http://www.postgresql.org/docs/9.1/static/ddl-partitioning.html
        # query = "CREATE INDEX {0}_idx_ann ON {0} USING btree (annotated);".format(w_table)
        query = "CREATE INDEX {0}_idx_vid ON {0} USING btree (variant_id);".format(w_table)
        query += "CREATE INDEX {0}_idx_var ON {0} USING btree (bin, chr, pos, trx_pk_uid, trx_pk_value);".format(w_table)
        query += "CREATE INDEX {0}_idx_trx ON {0} USING btree (trx_pk_uid, trx_pk_value);".format(w_table)
        query += "".join(["CREATE INDEX {0}_idx_s{1}_gt ON {0} USING btree (s{1}_gt);".format(w_table, i) for i in sample_ids])
        query += "".join(["CREATE INDEX {0}_idx_s{1}_dp ON {0} USING btree (s{1}_dp);".format(w_table, i) for i in sample_ids])
        query += "".join(["CREATE INDEX {0}_idx_s{1}_is_composite ON {0} USING btree (s{1}_is_composite);".format(w_table, i) for i in sample_ids])
        log(" > create index for variants random access")
        execute(query)
        # Update count stat of the analysis
        query = "UPDATE analysis SET total_variants=(SELECT COUNT(*) FROM {} WHERE is_variant), status='computing' WHERE id={}".format(w_table, analysis.id)
        log(" > count total variants in the analysis")
        execute(query)


    def update_working_table2(self, analysis, sample_ids, field_uids, filter_ids=[], attributes={}):
        """
            Update annotation of the working table of an analysis. The working table shall already exists
        """
        from core.core import core
        log("Check working table for analysis {}".format(analysis.id))
        # Get list of fields to add in the wt
        total = analysis.total_variants
        diff_fields = []
        diff_dbs = []
        progress = {"msg": "wt_processing", "start": datetime.datetime.now().ctime(), "analysis_id": analysis.id, "step": 2, "progress_total": total, "progress_current": 0}
        core.notify_all(None, data=progress)
        try:
            query = "SELECT column_name FROM information_schema.columns WHERE table_name='wt_{}'".format(analysis.id)
            current_fields = [row.column_name if row.column_name[0] != '_' else row.column_name[1:] for row in execute(query)]
            current_dbs = []
            for f_uid in current_fields:
                 if f_uid in self.fields_map and self.fields_map[f_uid]['db_uid'] not in current_dbs:
                    current_dbs.append(self.fields_map[f_uid]['db_uid'])
            for f_uid in field_uids:
                if f_uid not in current_fields and self.fields_map[f_uid]['db_name_ui'] != 'Variant':
                    diff_fields.append('_{}'.format(f_uid))
                    if self.fields_map[f_uid]['db_uid'] not in diff_dbs and self.fields_map[f_uid]['db_uid'] not in current_dbs:
                        diff_dbs.append(self.fields_map[f_uid]['db_uid'])
        except:
            # working table doesn't exist
            return False
        log(" > {} annotations to add ({} annotations db)".format(len(diff_fields), len(diff_dbs)))

        # Alter working table to add new fields
        pattern = "ALTER TABLE wt_{0} ADD COLUMN {1}{2} {3};"
        query = ""
        update_queries = []
        for f_uid in diff_fields:
            if f_uid[0] == '_':
                f_uid = f_uid[1:]
            query += pattern.format(analysis.id, '_', f_uid, self.sql_type_map[self.fields_map[f_uid]['type']])
        for a_name in attributes.keys():
            att_checked = []
            for sid, att in attributes[a_name].items():
                if 'attr_{}_{}'.format(a_name.lower(), att.lower()) in current_fields:
                    # We consider that if the first key_value for the attribute is define, the whole attribute's columns are defined,
                    # So break and switch to the next attribute.
                    # That's why before updating an attribute-value, we need before to drop all former columns in the wt 
                    break;
                else:
                    if att not in att_checked:
                        att_checked.append(att)
                        query += pattern.format(analysis.id, 'attr_', "{}_{}".format(a_name.lower(), att.lower()), 'boolean DEFAULT False')
                        update_queries.append("UPDATE wt_{} SET attr_{}_{}=True WHERE s{}_gt IS NOT NULL; ".format(analysis.id, a_name.lower(), att.lower(), sid))
        for f_id in filter_ids:
            if 'filter_{}'.format(f_id) not in current_fields:
                query += pattern.format(analysis.id, 'filter_', f_id, 'boolean DEFAULT False')
                f_filter = json.loads(execute("SELECT filter FROM filter WHERE id={}".format(f_id)).first().filter)
                q = self.build_query(analysis.id, analysis.reference_id, 'table', f_filter, [], None, None)
                queries = q[0]
                if len(queries) > 0:
                    # add all query to create temps tables needed by the filter if they do not yet exists
                    for q in queries[:-1]:
                        query += q
                    # add the query to update wt with the filter
                    # Note : As trx_pk_uid and transcript_pk_field_value may be null, we cannot use '=' operator and must use 'IS NOT DISTINCT FROM' 
                    #        as two expressions that return 'null' are not considered as equal in SQL.
                    update_queries.append("UPDATE wt_{0} SET filter_{1}=True FROM ({2}) AS _sub WHERE wt_{0}.variant_id=_sub.variant_id AND wt_{0}.trx_pk_uid IS NOT DISTINCT FROM _sub.trx_pk_uid AND wt_{0}.trx_pk_value IS NOT DISTINCT FROM _sub.trx_pk_value ; ".format(analysis.id, f_id, queries[-1].strip()[:-1]))
        if query != "":
            log(" > Update wt schema, adding new annotation's columns")
            execute(query)
        progress.update({"step": 3})
        core.notify_all(None, data=progress)

        # Loop over new annotation's databases, because if new: need to add new transcripts to the working table
        fields_to_copy_from_variant = ["variant_id","bin","chr","pos","ref","alt","is_transition","sample_tlist","sample_tcount","sample_alist","sample_acount","depth"]
        fields_to_copy_from_variant.extend(['s{}_gt'.format(s) for s in sample_ids])
        fields_to_copy_from_variant.extend(['s{}_dp'.format(s) for s in sample_ids])
        fields_to_copy_from_variant.extend(['attr_{}'.format(a.lower()) for a in attributes.keys()])
        fields_to_copy_from_variant.extend(['filter_{}'.format(f) for f in filter_ids])
        pattern = "INSERT INTO wt_{0} (annotated, trx_pk_uid, trx_pk_value, {1}) \
        SELECT False, '{2}', {4}.regovar_trx_id, {3} \
        FROM (SELECT {1} FROM wt_{0} WHERE trx_pk_uid IS NULL) AS _var \
        INNER JOIN {4} ON _var.variant_id={4}.variant_id" # TODO : check if more optim to select with JOIN ON bin/chr/pos/ref/alt
        for uid in diff_dbs:
            if self.db_map[uid]["type"] == "transcript":
                query = pattern.format(analysis.id,
                                       ', '.join(fields_to_copy_from_variant),
                                       self.db_map[uid]["db_pk_field_uid"],
                                       ', '.join(["_var.{}".format(f) for f in fields_to_copy_from_variant]),
                                       self.db_map[uid]["name"])
                log(" > annotation's database {} : adding variant's transcripts".format(self.db_map[uid]["name"]))
                execute(query)
        progress.update({"step": 4})
        core.notify_all(None, data=progress)

        # Create update query to retrieve annotation
        UPDATE_LOOP_RANGE = 1000
        to_update = {}
        for f_uid in diff_fields:
            if self.fields_map[f_uid[1:]]['db_uid'] not in to_update.keys():
                to_update[self.fields_map[f_uid[1:]]['db_uid']] = []
            to_update[self.fields_map[f_uid[1:]]['db_uid']].append({
                "name": self.fields_map[f_uid[1:]]['name'], 
                "uid":f_uid[1:], 
                "db_name": self.fields_map[f_uid[1:]]['db_name']})
        # Loop to update working table annotation (queries "packed" fields requested by annotation's database)
        for db_uid in to_update.keys():
            qset_ann = ', '.join(['_{0}=_ann._{0}'.format(f["uid"]) for f in to_update[db_uid]])
            qslt_ann = ','.join(['{0}.{1} AS _{2}'.format(f['db_name'], f["name"], f["uid"]) for f in to_update[db_uid]])
            qjoin = 'LEFT JOIN {0} '.format(self.db_map[db_uid]['join'].format('_var'))
            
            if self.db_map[db_uid]["type"] == "transcript":
                qslt_var = "SELECT variant_id, bin, chr, pos, ref, alt, trx_pk_value FROM wt_{0} WHERE annotated=False AND trx_pk_uid='{1}' LIMIT {2}".format(analysis.id, self.db_map[self.fields_map[f_uid[1:]]['db_uid']]['db_pk_field_uid'], UPDATE_LOOP_RANGE)
                query = "UPDATE wt_{0} SET annotated=True, {1} FROM (SELECT _var.variant_id, _var.trx_pk_value, {2} \
                    FROM ({3}) AS _var {4}) AS _ann \
                    WHERE wt_{0}.variant_id=_ann.variant_id AND wt_{0}.trx_pk_uid='{5}' AND wt_{0}.trx_pk_value=_ann.trx_pk_value".format(
                    analysis.id, 
                    qset_ann, 
                    qslt_ann, 
                    qslt_var, 
                    qjoin,
                    self.db_map[self.fields_map[f_uid[1:]]['db_uid']]['db_pk_field_uid'])
            else:
                qslt_var = 'SELECT variant_id, bin, chr, pos, ref, alt, trx_pk_value FROM wt_{0} WHERE annotated=False AND trx_pk_uid IS NULL LIMIT {1}'.format(analysis.id, UPDATE_LOOP_RANGE)
                query = "UPDATE wt_{0} SET annotated=True, {1} FROM (SELECT _var.variant_id, {2} \
                    FROM ({3}) AS _var {4}) AS _ann \
                    WHERE wt_{0}.variant_id=_ann.variant_id".format(
                    analysis.id, 
                    qset_ann, 
                    qslt_ann, 
                    qslt_var, 
                    qjoin)


            # if qset_ann != "":
            #     # Mark all variant as not annotated (to be able to do a "resumable update")
            #     log(" > mark all wt entries as 'not annotated'")
            #     execute("UPDATE wt_{} SET annotated=False".format(analysis.id))
            #     for page in range(0, total, UPDATE_LOOP_RANGE):
            #         log(" > update wt from {} to {} (on {})".format(page, page+UPDATE_LOOP_RANGE, total))
            #         execute(query)
            #         progress.update({"progress_current": page})
            #         core.notify_all(None, data=progress)
            # progress.update({"step": 5, "progress_current": total})
            # core.notify_all(None, data=progress)

        # Apply queries to update attributes and filters columns in the wt
        # if len(update_queries) > 0:
        #     log(" > update filters and attributes")
        #     execute("".join(update_queries))
        # progress.update({"step": 6})
        # core.notify_all(None, data=progress)

        # Check if trio analysis
        if analysis.settings["trio"]:
            db_ref_suffix= "_hg19"  # execute("SELECT table_suffix FROM reference WHERE id={}".format(reference_id)).first().table_suffix
            trio = analysis.settings["trio"]
            colname = "htz_comp_{}_{}_{}".format(trio["child"], trio["mother"], trio["father"])
            if colname not in current_fields:
                log(" > trio analysis : create htz_comp column")
                print("ALTER TABLE wt_{} ADD COLUMN {} boolean DEFAULT False".format(analysis.id, colname))
                query = "UPDATE wt_{0} u SET htz_comp_{1}_{2}_{3}=TRUE WHERE u.variant_id IN ( SELECT DISTINCT UNNEST(sub.vids) as variant_id FROM ( SELECT array_agg(w.variant_id) as vids, g.name2 FROM wt_{0} w  INNER JOIN refgene{4} g ON g.chr=w.chr AND g.txrange @> w.pos  WHERE  s{1}_gt > 1 AND ( (s{2}_gt > 1 AND (s{3}_gt = NULL or s{3}_gt < 2)) OR (s{3}_gt > 1 AND (s{2}_gt = NULL or s{2}_gt < 2))) GROUP BY name2 HAVING count(*) > 1) AS sub )"
                log(" > trio analysis : compute column : {}".format(colname))
                print (query.format(analysis.id, trio["child"], trio["mother"], trio["father"], db_ref_suffix))
                #execute(query.format(analysis.id, trio["child"], trio["mother"], trio["father"], db_ref_suffix))
            
            colname = "denovo_{}_{}_{}".format(trio["child"], trio["mother"], trio["father"])
            if colname not in current_fields:
                log(" > trio analysis : create denovo column")
                print("ALTER TABLE wt_{} ADD COLUMN {} boolean DEFAULT False".format(analysis.id, colname))
                query = "UPDATE wt_{0} SET denovo_{1}_{2}_{3}=TRUE WHERE s{1}_gt>0 and s{2}_gt=0 and s{3}_gt=0"
                log(" > trio analysis : compute column : {}".format(colname))
                print(query.format(analysis.id, trio["child"], trio["mother"], trio["father"]))

            colname = "xlinked_{}_{}_{}".format(trio["child"], trio["mother"], trio["father"])
            if colname not in current_fields:
                log(" > trio analysis : create xlinked column")
                print("ALTER TABLE wt_{} ADD COLUMN {} boolean DEFAULT False".format(analysis.id, colname))
                query = "UPDATE wt_{0} SET xlinked_{1}_{2}_{3}=TRUE WHERE chr=23 AND s{1}_gt>1 and s{2}_gt>1"
                # if trio["child_sex"] == "F":
                #     query += "  AND s{3}_gt>1"
                log(" > trio analysis : compute column : {}".format(colname))
                print(query.format(analysis.id, trio["child"], trio["mother"], trio["father"]))


        # Update count stat of the analysis
        query = "UPDATE analysis SET status='ready' WHERE id={}".format(analysis.id)
        log(" > wt is ready")
        execute(query)
        




    def prepare(self, analysis, filter_json, order=None):
        """
            Build tmp table for the provided filter/order by parameters
            set also the total count of variant/transcript
        """
        from core.core import core
        log("---\nPrepare tmp working table for analysis {}".format(analysis.id))
        progress = {"start": datetime.datetime.now().ctime(), "analysis_id": analysis.id, "progress": 0}
        core.notify_all(None, data={'action':'filtering_prepare', 'data': progress})
        # Create schema
        w_table = 'wt_{}'.format(analysis.id)
        query = "DROP TABLE IF EXISTS {0}_tmp CASCADE; CREATE TABLE {0}_tmp AS "
        query += "SELECT ROW_NUMBER() OVER() as page, variant_id, array_agg(trx_pk_value) as trx, count(*) as trx_count{1} FROM {0} WHERE trx_pk_value is not null{2} GROUP BY variant_id{1} ORDER BY {3};"
        
        f_fields = "" if order is None else "," + ", ".join(order)
        f_order = "variant_id" if order is None else ", ".join(order)
        f_filter = self.parse_filter(analysis, filter_json, order)
        f_filter = " AND ({0})".format(f_filter) if len(filter_json[1]) > 0 else f_filter
        query = query.format(w_table, f_fields, f_filter, f_order)

        sql_result = None
        log("Filter: {0}\nOrder: {1}\nQuery: {2}".format(filter_json, order, query))
        with Timer() as t:
            sql_result = execute(query)
        
        total_variant = sql_result.rowcount
        log("Time: {0}\nResults count: {1}".format(t, total_variant))
        
        # Save filter data
        settings = {}
        try:
            analysis.filter = filter_json
            analysis.order = [] if order is None else order
            analysis.total_variants = total_variant
            analysis.save()
        except:
            err("Not able to save current filter")
        
        progress.update({"progress": 1})
        core.notify_all(None, data={'action':'filtering_prepare', 'data': progress})




    def update_wt(self, analysis, column, filter_json):
        """
            Add of update working table provided boolean's column with variant that match the provided filter
            Use this method to dynamically Add/Update saved filter or panel filter
            
            Note that as we need to run this method async when creating filter (filter_manager.create_update_filter), 
            we cannot use async (incompatible with mutithread)
        """
        from core.core import core
        log("---\nUpdating working table of analysis {}".format(analysis.id))
        progress = {"start": datetime.datetime.now().ctime(), "analysis_id": analysis.id, "progress": 0, "column": column}
        core.notify_all(None, data={'action':'wt_update', 'data': progress})
        
        # Create schema
        w_table = 'wt_{}'.format(analysis.id)
        query = "ALTER TABLE {0} ADD COLUMN {1} boolean DEFAULT False; "
        try:
            execute(query.format(w_table, column))
            log("Column: {0} init".format(column))
        except RegovarException as ex:
            query = "UPDATE {0} SET {1}=False; " # force reset to false
            execute(query.format(w_table, column))
            log("Column: {0} already exists -> reset to false".format(column))
        
        progress.update({"progress": 0.33})
        core.notify_all(None, data={'action':'wt_update', 'data': progress})
        
        # Set filtered data
        # Note : As trx_pk_value may be null, we cannot use '=' operator and must use 'IS NOT DISTINCT FROM' 
        #        as two expressions that return 'null' are not considered as equal in SQL
        query = "UPDATE {0} SET {1}=True FROM (SELECT variant_id, trx_pk_value FROM {0} {2}) AS _sub WHERE {0}.variant_id=_sub.variant_id AND {0}.trx_pk_value IS NOT DISTINCT FROM _sub.trx_pk_value; " 
        subq = self.parse_filter(analysis, filter_json, [])
        subq = "WHERE " + subq if subq else ""
        query = query.format(w_table, column, subq)
        sql_result = None
        log("Filter: {0}\nQuery: {1}".format(filter_json, query))
        with Timer() as t:
            sql_result = execute(query)
        total_variant = sql_result.rowcount
        log("Time: {0}\nResults count: {1}".format(t, total_variant))
        
        progress.update({"progress": 0.66})
        core.notify_all(None, data={'action':'wt_update', 'data': progress})
        
        # Create index
        query = "CREATE INDEX IF NOT EXISTS idx_{1} ON {0} ({1});"
        execute(query.format(w_table, column))
        log("Index updated: idx_{0}".format(column))
        
        progress.update({"progress": 1})
        core.notify_all(None, data={'action':'wt_update', 'data': progress})
        return total_variant


    async def get_variant(self, analysis, fields, limit=100, offset=0):
        """
            Return results from current temporary table according to provided fields and pagination information
            
        """
        from core.core import core
        w_table = 'wt_{}'.format(analysis.id)
        query = "SELECT ws.variant_id, ws.trx_count, {1} FROM {0}_tmp ws INNER JOIN {0} wt ON ws.variant_id=wt.variant_id WHERE wt.is_variant AND ws.page>={2} ORDER BY ws.page LIMIT {3}"
        
        query = query.format(w_table, self.parse_fields(analysis, fields, "wt."), offset, limit)
        sql_result = None
        with Timer() as t:
            sql_result = await execute_aio(query)
            
        log("--- Select:\nFrom: {0}\nTo: {1}\nFields: {2}\nQuery: {3}\nTime: {4}".format(offset, limit, fields, query, t))
        return sql_result
        
        
        
    async def get_trx(self, analysis, fields, variant_id):
        """
            Return results from current temporary table according to provided fields and variant
        """
        from core.core import core
        w_table = 'wt_{}'.format(analysis.id)
        
        sub_query = "SELECT unnest(trx) FROM {0}_tmp WHERE variant_id={1}".format(w_table, variant_id)
        query = "SELECT variant_id, trx_pk_value as trx_id, {1} FROM {0} WHERE variant_id={2} AND trx_pk_value IN ({3})"
        
        query = query.format(w_table, self.parse_fields(analysis, fields, ""), variant_id, sub_query)
        sql_result = None
        with Timer() as t:
            sql_result = await execute_aio(query)
            
        log("--- Select trx:\nVariantId: {0}\nTrx count: {1}\nTime: {2}".format(variant_id, sql_result.rowcount, t))
        return sql_result




    async def request(self, analysis_id, filter_json=None, fields=None, order=None, variant_id=None, limit=100, offset=0):
        """
            Commont request to manage all different cases
        """
        if fields is None or not isinstance(fields, list) or len(fields) == 0:
            raise RegovarException("You must specify which information must be returned by the query.")
        
        # Get analysis data and check status if ok to do filtering
        analysis = Analysis.from_id(analysis_id)
        if analysis is None:
            raise RegovarException("Not able to retrieve analysis with provided id: {}".format(analysis_id))
        if not analysis.status or analysis.status == 'empty':
            # check if all samples are ready to be use for the creation of the working table
            for sid in analysis.samples_ids:
                sample = Sample.from_id(sid)
                if sample.status != 'ready':
                    raise RegovarException("Samples of the analysis {} are not ready to be used".format(analysis.id))
            await self.create_working_table(analysis)
        elif analysis.status == 'computing':
            raise RegovarException("Analysis {} is not ready to be used: computing progress {} %".format(analysis.id, round(analysis.computing_progress*100, 2)))
        elif analysis.status == 'error':
            raise RegovarException("Analysis {} in error: sysadmin must check log on server".format(analysis.id))
        
        # Prepare wt for specific filter query
        # if filter_json is None, we assume that we are requesting the current tmp working table formerly prepared
        
        if filter_json:
            # Need to prepare temp table
            self.prepare(analysis, filter_json, order)
        elif not analysis.filter:
            if filter_json is None:
                raise RegovarException("Analysis {} is not ready. You need to 'prepare' your filter by providing the filter and ordering parameters before requesting results.".format(analysis.id))
                
        # Get results
        vmode = variant_id is None or variant_id == ""
        if vmode:
            sql_result = await self.get_variant(analysis, fields, limit, offset)
        else:
            sql_result = await self.get_trx(analysis, fields, variant_id)
            
        # Format result
        result = []
        
        with Timer() as t:
            if sql_result is not None:
                for row in sql_result:
                    if vmode:
                        entry = {"id" : str(row.variant_id), "trx_count": row.trx_count}
                    else:
                        entry = {"id" : "{}_{}".format(row.variant_id, row.trx_id)}
                    for f_uid in fields:
                        # Manage special case for fields splitted by sample
                        if self.fields_map[f_uid]['name'].startswith('s{}_'):
                            pattern = "row." + self.fields_map[f_uid]['name']
                            r = {}
                            for sid in analysis.samples_ids:
                                r[sid] = FilterEngine.parse_result(eval(pattern.format(sid)))
                            entry[f_uid] = r
                        else:
                            if f_uid == "7166ec6d1ce65529ca2800897c47a0a2": # field = pos
                                entry[f_uid] = FilterEngine.parse_result(eval("row.{}".format(self.fields_map[f_uid]['name'])) + 1)
                            elif self.fields_map[f_uid]['db_name_ui'] in ['Variant', 'Regovar']:
                                entry[f_uid] = FilterEngine.parse_result(eval("row.{}".format(self.fields_map[f_uid]['name'])))
                            else:
                                entry[f_uid] = FilterEngine.parse_result(eval("row._{}".format(f_uid)))
                    result.append(entry)
        log("Result processing: {0}\n".format(t))
        
        
        
        return {"wt_total_variants" : analysis.total_variants, "wt_total_results" : 0, "from":0, "to": 0, "results" : result}



    def parse_fields(self, analysis, fields, prefix):
        """
            Parse the json fields and return the corresponding postgreSQL query
        """
        fields_names = []
        for f_uid in fields:
            if self.fields_map[f_uid]['db_name_ui'] in ['Variant', 'Regovar']:
                # Manage special case for fields splitted by sample
                if self.fields_map[f_uid]['name'].startswith('s{}_'):
                    fields_names.extend([prefix + self.fields_map[f_uid]['name'].format(s) for s in analysis.samples_ids])
                else:
                    fields_names.append(prefix+'{}'.format(self.fields_map[f_uid]["name"]))
            else:
                fields_names.append(prefix+'_{}'.format(f_uid))
        return ', '.join(fields_names)

       
       
    def parse_order(self, analysis, order):
        """
            Parse the json order and return the corresponding postgreSQL query
        """
        if order is None or len(order) == 0:
            return ""
        
        orders = []
        for f_uid in order:
            asc = 'ASC'
            if f_uid[0] == '-':
                f_uid = f_uid[1:]
                asc = 'DESC'
            if self.fields_map[f_uid]['db_name_ui'] in ['Variant', 'Regovar']:
                # Manage special case for fields splitted by sample
                if self.fields_map[f_uid]['name'].startswith('s{}_'):
                    # TODO : actually, it's not possible to do "order by" on special fields (GT and DP because they are split by sample)
                    pass
                else:
                    orders.append('{} {}'.format(self.fields_map[f_uid]["name"], asc))
            else:
                orders.append('_{} {}'.format(f_uid, asc))
        return ', '.join(orders)




    def parse_filter(self, analysis, filters, order=None):
        """
            Parse the json filter and return the corresponding postgreSQL query
        """
        # Init some global variables
        wt = 'wt_{}'.format(analysis.id)


        # Build WHERE
        temporary_to_import = {}


        def build_filter(data):
            """ 
                Recursive method that build the query from the filter json data at operator level 
            """
            operator = data[0]
            if operator in ['AND', 'OR']:
                if len(data[1]) == 0:
                    return ''
                return ' (' + FilterEngine.op_map[operator].join([build_filter(f) for f in data[1]]) + ') '
            elif operator in ['==', '!=', '>', '<', '>=', '<=']:
                # Comparaison with a field: the field MUST BE the first operande
                if data[1][0] != 'field':
                    raise RegovarException("Comparaison operator MUST have field as left operande.")
                    pass
                metadata = self.fields_map[data[1][1]]
                
                
                # Manage special case for fields splitted by sample
                if metadata['name'].startswith('s{}_'):
                    return ' (' + ' OR '.join(['{0}{1}{2}'.format(metadata['name'].format(s), FilterEngine.op_map[operator], parse_value(metadata["type"], data[2])) for s in analysis.samples_ids]) + ') '
                elif metadata["type"] == "list":
                    return '{2}{1} ANY({0})'.format(parse_value(metadata["type"], data[1]), FilterEngine.op_map[operator], parse_value(metadata["type"], data[2]))
                else:
                    return '{0}{1}{2}'.format(parse_value(metadata["type"], data[1]), FilterEngine.op_map[operator], parse_value(metadata["type"], data[2]))
            elif operator in ['~', '!~']:
                return '{0}{1}{2}'.format(parse_value('string', data[1]), FilterEngine.op_map[operator], parse_value('string%', data[2]))
            elif operator in ['IN', 'NOTIN']:
                tmp_table = get_tmp_table(data[1], data[2])
                temporary_to_import[tmp_table]['where'] = FilterEngine.op_map[operator].format(tmp_table, wt)
                if data[1] == 'site':
                    temporary_to_import[tmp_table]['from'] = " LEFT JOIN {1} ON {0}.bin={1}.bin AND {0}.chr={1}.chr AND {0}.pos={1}.pos".format(wt, tmp_table)
                else:  # if data[1] == 'variant':
                    temporary_to_import[tmp_table]['from'] = " LEFT JOIN {1} ON {0}.bin={1}.bin AND {0}.chr={1}.chr AND {0}.pos={1}.pos AND {0}.ref={1}.ref AND {0}.alt={1}.alt".format(wt, tmp_table)
                return temporary_to_import[tmp_table]['where']



        def get_tmp_table(mode, data):
            """
                Parse json data to build temp table for ensemblist operation IN/NOTIN
                    mode: site or variant
                    data: json data about the temp table to create
            """
            ttable_quer_map = "CREATE TEMPORARY TABLE IF NOT EXISTS {0} AS {1}; "
            if data[0] == 'sample':
                tmp_table_name = "tmp_sample_{0}_{1}".format(data[1], mode)
                if mode == 'site':
                    tmp_table_query = ttable_quer_map.format(tmp_table_name, "SELECT DISTINCT {0}.bin, {0}.chr, {0}.pos FROM {0} WHERE {0}.s{1}_gt IS NOT NULL".format(wt, data[1]))
                else:  # if mode = 'variant':
                    tmp_table_query = ttable_quer_map.format(tmp_table_name, "SELECT DISTINCT {0}.bin, {0}.chr, {0}.pos, {0}.ref, {0}.alt FROM {0} WHERE {0}.s{1}_gt IS NOT NULL".format(wt, data[1]))
            elif data[0] == 'filter':
                tmp_table_name = "tmp_filter_{0}".format(data[1])
                if mode == 'site':
                    tmp_table_query = ttable_quer_map.format(tmp_table_name, "SELECT DISTINCT {0}.bin, {0}.chr, {0}.pos FROM {0} WHERE {0}.filter_{1}=True".format(wt, data[1]))
                else:  # if mode = 'variant':
                    tmp_table_query = ttable_quer_map.format(tmp_table_name, "SELECT DISTINCT {0}.bin, {0}.chr, {0}.pos, {0}.ref, {0}.alt FROM {0} WHERE {0}.filter_{1}=True".format(wt, data[1]))
            elif data[0] == 'attribute':
                key, value = data[1].split(':')
                tmp_table_name = "tmp_attribute_{0}_{1}_{2}_{3}".format(analysis_id, key, value, mode)
                if mode == 'site':
                    tmp_table_query = ttable_quer_map.format(tmp_table_name, "SELECT DISTINCT {0}.bin, {0}.chr, {0}.pos FROM {0} WHERE {0}.attr_{1}='{2}'".format(wt, key, value))
                else:  # if mode = 'variant':
                    tmp_table_query = ttable_quer_map.format(tmp_table_name, "SELECT DISTINCT {0}.bin, {0}.chr, {0}.pos, {0}.ref, {0}.alt FROM {0} WHERE {0}.attr_{1}='{2}'".format(wt, key, value))
            temporary_to_import[tmp_table_name] = {'query': tmp_table_query } #+ "CREATE INDEX IF NOT EXISTS {0}_idx_var ON {0} USING btree (bin, chr, pos);".format(tmp_table_name)}
            return tmp_table_name



        def parse_value(ftype, data):
            if data[0] == 'field':
                if self.fields_map[data[1]]["type"] == ftype:
                    if self.fields_map[data[1]]['db_name'] == "wt" :
                        return "{0}".format(self.fields_map[data[1]]["name"])
                    else:
                        return "_{0}".format(data[1])
            if data[0] == 'value':
                if ftype in ['int', 'float', 'enum', 'bool', 'sample_array']:
                    return str(data[1])
                elif ftype in ['string', 'list', 'sequence']:
                    return "'{0}'".format(data[1])
                elif ftype == 'string%':
                    return "'%%{0}%%'".format(data[1])
                elif ftype == 'range' and len(data) == 3:
                    return 'int8range({0}, {1})'.format(data[1], data[2])
            raise RegovarException("FilterEngine.request.parse_value - Unknow type: {0} ({1})".format(ftype, data))


        query = build_filter(filters)
        if query is not None:
            query =query.strip()


        return query






    @staticmethod
    def get_hasname(analysis_id, mode, fields, filter_json):
        # clean and sort fields list
        clean_fields = fields
        clean_fields.sort()
        clean_fields = list(set(clean_fields))

        string_id = "{0}{1}{2}{3}".format(analysis_id, mode, clean_fields, json.dumps(filter_json))
        return hashlib.md5(string_id.encode()).hexdigest()


    @staticmethod
    def parse_result(value):
        """
            Parse value returned by sqlAlchemy and cast it, if needed, into "simples" python types
        """
        # if value is None:
        #     return ""
        if type(value) == psycopg2._range.NumericRange:
            return (value.lower, value.upper)
        return value
 
