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

        # create wt table
        self.create_wt_schema(analysis)

        # insert variant
        self.insert_wt_variants(analysis)

        # set sample's fields (GT, DP, ...)
        self.update_wt_samples_fields(analysis)

        # compute stats and predefined filter (attributes, panels, trio, ...)
        await self.update_wt_stats_prefilters(analysis)

        # variant's indexes
        self.create_wt_variants_indexes(analysis)

        # insert trx annotations
        self.insert_wt_trx(analysis)

        # trx's indexes
        self.create_wt_trx_indexes(analysis)

        # Update count stat of the analysis
        query = "UPDATE analysis SET status='ready', computing_progress=1 WHERE id={}".format(analysis.id)
        log(" > wt is ready")
        execute(query)



    def create_wt_schema(self, analysis):
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
        query += ", ".join(["s{}_gt integer".format(i) for i in analysis.samples_ids]) + ", "
        query += ", ".join(["s{}_dp integer".format(i) for i in analysis.samples_ids]) + ", "
        query += ", ".join(["s{}_qual real".format(i) for i in analysis.samples_ids]) + ", "
        query += ", ".join(["s{}_filter JSON".format(i) for i in analysis.samples_ids]) + ", "
        query += ", ".join(["s{}_is_composite boolean".format(i) for i in analysis.samples_ids]) + ", "

        # Add annotation's columns
        for dbuid in analysis.settings["annotations_db"]:
            for fuid in self.db_map[dbuid]["fields"]:
                query += "_{} {}, ".format(fuid, self.sql_type_map[self.fields_map[fuid]['type']])
                
        # Add attribute's columns
        for attr in analysis.attributes:
            for value, col_id in attr["values_map"].items():
                query += "attr_{} boolean DEFAULT False, ".format(col_id)

        # Add filter's columns
        # TODO: foreach analysis.filters_ids

        # Add panel's columns
        # TODO: foreach analysis.panels_ids

        query = query[:-2] + ");"
        log(" > create wt schema")
        execute(query.format(wt))


    def insert_wt_variants(self, analysis):
        wt = "wt_{}".format(analysis.id)

        # create temp table with id of variants
        query  = "DROP TABLE IF EXISTS {0}_var CASCADE; CREATE TABLE {0}_var (id bigint, trx_count integer); "
        execute(query.format(wt))
        
        query = "INSERT INTO {0}_var (id) SELECT DISTINCT variant_id FROM sample_variant{1} WHERE sample_id IN ({2}); "
        res = execute(query.format(wt, analysis.db_suffix, ",".join([str(sid) for sid in analysis.samples_ids])))
        
        # set total number of variant for the analysis
        log(" > {} variants found".format(res.rowcount))
        query = "UPDATE analysis SET total_variants={1} WHERE id={0};".format(analysis.id, res.rowcount)
        query += "CREATE INDEX {0}_var_idx_id ON {0}_var USING btree (id);"
        execute(query.format(wt))

        # Insert variants and their annotations
        q_fields = "is_variant, variant_id, bin, chr, pos, ref, alt, is_transition, sample_tlist"
        q_select = "True, _vids.id, _var.bin, _var.chr, _var.pos, _var.ref, _var.alt, _var.is_transition, _var.sample_list"
        q_from   = "{0}_var _vids LEFT JOIN variant{1} _var ON _vids.id=_var.id".format(wt, analysis.db_suffix)

        for dbuid in analysis.settings["annotations_db"]:
            if self.db_map[dbuid]["type"] == "variant":
                dbname = "_db_{}".format(dbuid)
                q_from += " LEFT JOIN {0}".format(self.db_map[dbuid]['join'].format(dbname, '_var'))
                q_fields += ", " + ", ".join(["_{}".format(fuid) for fuid in self.db_map[dbuid]["fields"]])
                q_select += ", " + ", ".join(["{}.{}".format(dbname, self.fields_map[fuid]["name"]) for fuid in self.db_map[dbuid]["fields"]])

        # execute query
        query = "INSERT INTO {0} ({1}) SELECT {2} FROM {3};".format(wt, q_fields, q_select, q_from)
        execute(query)


    def update_wt_samples_fields(self, analysis):
        wt = "wt_{}".format(analysis.id)
        for sid in analysis.samples_ids:
            execute("UPDATE {0} SET s{2}_gt=_sub.genotype, s{2}_dp=_sub.depth, s{2}_qual=_sub.quality, s{2}_filter=_sub.filter, s{2}_is_composite=_sub.is_composite FROM (SELECT variant_id, genotype, depth, quality, filter, is_composite FROM sample_variant{1} WHERE sample_id={2}) AS _sub WHERE {0}.variant_id=_sub.variant_id".format(wt, analysis.db_suffix, sid))


    async def update_wt_stats_prefilters(self, analysis):
        wt = "wt_{}".format(analysis.id)

        # Variant occurence stats
        query = "UPDATE {0} SET \
            sample_tcount=array_length(sample_tlist,1), \
            sample_alist=array_intersect(sample_tlist, array[{1}]), \
            sample_acount=array_length(array_intersect(sample_tlist, array[{1}]),1)"
        log(" > compute statistics")
        execute(query.format(wt, ",".join([str(i) for i in analysis.samples_ids])))
        
        # Attributes
        for attr in analysis.attributes:
            log(" > compute attribute {}".format(attr["name"]))
            for sid, attr_data in attr["samples_values"].items():
                execute("UPDATE {0} SET attr_{1}=True WHERE s{2}_gt IS NOT NULL".format(wt, attr_data["wt_col_id"], sid))

        # Filter
        # TODO

        # Panels
        # TODO

        # Predefinied quickfilters
        if len(analysis.samples_ids) == 1:
            await self.update_wt_compute_prefilter_single(analysis, analysis.samples_ids[0], "M")
        elif analysis.settings["trio"]:
            self.update_wt_compute_prefilter_trio(analysis, analysis.samples_ids, analysis.settings["trio"])
            
        # 
        

    def create_wt_variants_indexes(self, analysis):
        wt = "wt_{}".format(analysis.id)

        # Common indexes for variants
        query = "CREATE INDEX {0}_idx_vid ON {0} USING btree (variant_id);".format(wt)
        query += "".join(["CREATE INDEX {0}_idx_s{1}_gt ON {0} USING btree (s{1}_gt);".format(wt, i) for i in analysis.samples_ids])
        query += "".join(["CREATE INDEX {0}_idx_s{1}_dp ON {0} USING btree (s{1}_dp);".format(wt, i) for i in analysis.samples_ids])
        query += "".join(["CREATE INDEX {0}_idx_s{1}_qual ON {0} USING btree (s{1}_qual);".format(wt, i) for i in analysis.samples_ids])
        #query += "".join(["CREATE INDEX {0}_idx_s{1}_filter ON {0} USING btree (s{1}_filter);".format(wt, i) for i in analysis.samples_ids])
        query += "".join(["CREATE INDEX {0}_idx_s{1}_is_composite ON {0} USING btree (s{1}_is_composite);".format(wt, i) for i in analysis.samples_ids])
        query += "CREATE INDEX {0}_idx_is_dom ON {0} USING btree (is_dom);".format(wt)
        query += "CREATE INDEX {0}_idx_is_rec_hom ON {0} USING btree (is_rec_hom);".format(wt)
        query += "CREATE INDEX {0}_idx_is_rec_htzcomp ON {0} USING btree (is_rec_htzcomp);".format(wt)
        query += "CREATE INDEX {0}_idx_is_denovo ON {0} USING btree (is_denovo);".format(wt)
        query += "CREATE INDEX {0}_idx_is_aut ON {0} USING btree (is_aut);".format(wt)
        query += "CREATE INDEX {0}_idx_is_xlk ON {0} USING btree (is_xlk);".format(wt)
        query += "CREATE INDEX {0}_idx_is_mit ON {0} USING btree (is_mit);".format(wt)

        # Add indexes on attributes columns
        for attr in analysis.attributes:
            for value, col_id in attr["values_map"].items():
                query += "CREATE INDEX {0}_idx_attr_{1} ON {0} USING btree (attr_{1});".format(wt, col_id)

                    
        # Add indexes on filter columns
        # TODO

        # Add indexes on panel columns
        # TODO
        
        log(" > create index for variants random access")
        execute(query)
        


    def insert_wt_trx(self, analysis):
        wt = "wt_{}".format(analysis.id)

        # Insert trx and their annotations
        q_fields  = "is_variant, variant_id, trx_pk_uid, trx_pk_value, bin, chr, pos, ref, alt, is_transition, sample_tlist, sample_tcount, sample_alist, sample_acount, "
        q_fields += "is_dom, is_rec_hom, is_rec_htzcomp, is_denovo, is_aut, is_xlk, is_mit, "
        q_fields += ", ".join(["s{}_gt".format(i) for i in analysis.samples_ids]) + ", "
        q_fields += ", ".join(["s{}_dp".format(i) for i in analysis.samples_ids]) + ", "
        q_fields += ", ".join(["s{}_qual".format(i) for i in analysis.samples_ids]) + ", "
        q_fields += ", ".join(["s{}_filter".format(i) for i in analysis.samples_ids]) + ", "
        q_fields += ", ".join(["s{}_is_composite".format(i) for i in analysis.samples_ids])
        # Add attribute's columns
        for attr in analysis.attributes:
            for value, col_id in attr["values_map"].items():
                q_fields += ", attr_{}".format(col_id)
        # Add filter's columns
        # TODO: foreach analysis.filters_ids

        # Add panel's columns
        # TODO: foreach analysis.panels_ids
        
        q_select  = "False, _wt.variant_id, '{0}', {1}.regovar_trx_id, _wt.bin, _wt.chr, _wt.pos, _wt.ref, _wt.alt, _wt.is_transition, _wt.sample_tlist, "
        q_select += "_wt.sample_tcount, _wt.sample_alist, _wt.sample_acount, _wt.is_dom, _wt.is_rec_hom, _wt.is_rec_htzcomp, _wt.is_denovo, "
        q_select += "_wt.is_aut, _wt.is_xlk, _wt.is_mit, "
        q_select += ", ".join(["_wt.s{}_gt".format(i) for i in analysis.samples_ids]) + ", "
        q_select += ", ".join(["_wt.s{}_dp".format(i) for i in analysis.samples_ids]) + ", "
        q_select += ", ".join(["_wt.s{}_qual".format(i) for i in analysis.samples_ids]) + ", "
        q_select += ", ".join(["_wt.s{}_filter".format(i) for i in analysis.samples_ids]) + ", "
        q_select += ", ".join(["_wt.s{}_is_composite".format(i) for i in analysis.samples_ids])
        # Add attribute's columns
        for attr in analysis.attributes:
            for value, col_id in attr["values_map"].items():
                q_select += ", _wt.attr_{}".format(col_id)

        # Add filter's columns
        # TODO: foreach analysis.filters_ids

        # Add panel's columns
        # TODO: foreach analysis.panels_ids
        
        q_from   = "{0} _wt".format(wt, analysis.db_suffix)

        # first loop over "variant db" in order to set common annotation to trx
        for dbuid in analysis.settings["annotations_db"]:
            if self.db_map[dbuid]["type"] == "variant":
                q_fields += ", " + ", ".join(["_{}".format(fuid) for fuid in self.db_map[dbuid]["fields"]])
                q_select += ", " + ", ".join(["_{}".format(fuid) for fuid in self.db_map[dbuid]["fields"]])


        # Second loop to execute insert query by trx annotation db
        for dbuid in analysis.settings["annotations_db"]:
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


    def create_wt_trx_indexes(self, analysis):
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
                field = data[1]
                if field[0] == 'sample':
                    sql = 'NOT NULL' if operator == 'IN' else 'NULL'
                    return "s{}_gt IS ".format(field[1]) + sql
                elif field[0] == 'filter':
                    sql = '' if operator == 'IN' else 'NOT '
                    return sql + "filter_{}".format(field[1])
                elif field[0] == 'attr':
                    sql = '' if operator == 'IN' else 'NOT '
                    return sql + "attr_{}".format(field[1])

                



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
 
