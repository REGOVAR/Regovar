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
    sql_type_map = {'int': 'integer', 'string': 'text', 'float': 'real', 'percent': 'real', 'enum': 'integer', 'range': 'int8range', 'bool': 'boolean',
                    'list_i': 'text', 'list_s': 'text', 'list_f': 'text', 'list_i': 'text', 'list_pb': 'text'}


    def __init__(self):
        run_until_complete(self.load_annotation_metadata())


    async def load_annotation_metadata(self):
        """
            Init Annso Filtering engine.
            Init mapping collection for annotations databases and fields
        """
        refname = 'hg19'  # execute("SELECT table_suffix FROM reference WHERE id="+str(reference)).first()["table_suffix"]
        self.reference = 2
        self.fields_map = {}
        self.db_map = {}
        self.variant_table = "sample_variant_{0}".format(refname)
        query = "SELECT d.uid AS duid, d.name AS dname, d.name_ui AS dname_ui, d.jointure, d.reference_id, d.type AS dtype, d.db_pk_field_uid, a.uid AS fuid, a.name AS fname, a.type, a.wt_default FROM annotation_field a LEFT JOIN annotation_database d ON a.database_uid=d.uid"
        result = await execute_aio(query)
        for row in result:
            if row.duid not in self.db_map:
                self.db_map[row.duid] = {"name": row.dname, "join": row.jointure, "fields": {}, "reference_id": row.reference_id, "type": row.dtype, "db_pk_field_uid" : row.db_pk_field_uid}
            self.db_map[row.duid]["fields"][row.fuid] = {"name": row.fname, "type": row.type}
            self.fields_map[row.fuid] = {"name": row.fname, "type": row.type, "db_uid": row.duid, "db_name_ui": row.dname_ui, "db_name": row.dname, "db_type": row.dtype, "join": row.jointure, "wt_default": row.wt_default}


    def create_working_table(self, analysis, sample_ids):
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
            transcript_pk_field_uid character varying(32), \
            transcript_pk_value character varying(100), \
            is_transition boolean, \
            sample_tlist integer[], \
            sample_tcount integer, \
            sample_alist integer[], \
            sample_acount integer, \
            depth integer, "
        query += ", ".join(["s{}_gt integer".format(i) for i in sample_ids]) + ", "
        query += ", ".join(["s{}_dp integer".format(i) for i in sample_ids]) + ", "
        query += ", ".join(["s{}_is_composite boolean".format(i) for i in sample_ids]) 
        query += ", CONSTRAINT {0}_ukey UNIQUE (variant_id, transcript_pk_field_uid, transcript_pk_value));"

        log(" > create wt schema")
        execute(query.format(w_table))
        # Insert variant without annotation first
        query =  "INSERT INTO {0} (variant_id, bin, chr, pos, ref, alt, is_transition, sample_tlist) \
            SELECT DISTINCT sample_variant_{1}.variant_id, sample_variant_{1}.bin, sample_variant_{1}.chr, sample_variant_{1}.pos, sample_variant_{1}.ref, sample_variant_{1}.alt, \
                variant_{1}.is_transition, \
                variant_{1}.sample_list \
            FROM sample_variant_{1} INNER JOIN variant_{1} ON sample_variant_{1}.variant_id=variant_{1}.id \
            WHERE sample_variant_{1}.sample_id IN ({2}) \
            ON CONFLICT (variant_id, transcript_pk_field_uid, transcript_pk_value) DO NOTHING;"

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
        query += "CREATE INDEX {0}_idx_var ON {0} USING btree (bin, chr, pos, transcript_pk_field_uid, transcript_pk_value);".format(w_table)
        query += "CREATE INDEX {0}_idx_trx ON {0} USING btree (transcript_pk_field_uid, transcript_pk_value);".format(w_table)
        query += "".join(["CREATE INDEX {0}_idx_s{1}_gt ON {0} USING btree (s{1}_gt);".format(w_table, i) for i in sample_ids])
        query += "".join(["CREATE INDEX {0}_idx_s{1}_dp ON {0} USING btree (s{1}_dp);".format(w_table, i) for i in sample_ids])
        query += "".join(["CREATE INDEX {0}_idx_s{1}_is_composite ON {0} USING btree (s{1}_is_composite);".format(w_table, i) for i in sample_ids])
        log(" > create index for variants random access")
        execute(query)
        # Update count stat of the analysis
        query = "UPDATE analysis SET total_variants=(SELECT COUNT(*) FROM {} WHERE is_variant), status='computing' WHERE id={}".format(w_table, analysis.id)
        log(" > count total variants in the analysis")
        execute(query)


    def update_working_table(self, analysis, sample_ids, field_uids, filter_ids=[], attributes={}):
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
                    # Note : As transcript_pk_field_uid and transcript_pk_field_value may be null, we cannot use '=' operator and must use 'IS NOT DISTINCT FROM' 
                    #        as two expressions that return 'null' are not considered as equal in SQL.
                    update_queries.append("UPDATE wt_{0} SET filter_{1}=True FROM ({2}) AS _sub WHERE wt_{0}.variant_id=_sub.variant_id AND wt_{0}.transcript_pk_field_uid IS NOT DISTINCT FROM _sub.transcript_pk_field_uid AND wt_{0}.transcript_pk_value IS NOT DISTINCT FROM _sub.transcript_pk_value ; ".format(analysis.id, f_id, queries[-1].strip()[:-1]))
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
        pattern = "INSERT INTO wt_{0} (annotated, transcript_pk_field_uid, transcript_pk_value, {1}) \
        SELECT False, '{2}', {4}.regovar_trx_id, {3} \
        FROM (SELECT {1} FROM wt_{0} WHERE transcript_pk_field_uid IS NULL) AS _var \
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
                qslt_var = "SELECT variant_id, bin, chr, pos, ref, alt, transcript_pk_value FROM wt_{0} WHERE annotated=False AND transcript_pk_field_uid='{1}' LIMIT {2}".format(analysis.id, self.db_map[self.fields_map[f_uid[1:]]['db_uid']]['db_pk_field_uid'], UPDATE_LOOP_RANGE)
                query = "UPDATE wt_{0} SET annotated=True, {1} FROM (SELECT _var.variant_id, _var.transcript_pk_value, {2} \
                    FROM ({3}) AS _var {4}) AS _ann \
                    WHERE wt_{0}.variant_id=_ann.variant_id AND wt_{0}.transcript_pk_field_uid='{5}' AND wt_{0}.transcript_pk_value=_ann.transcript_pk_value".format(
                    analysis.id, 
                    qset_ann, 
                    qslt_ann, 
                    qslt_var, 
                    qjoin,
                    self.db_map[self.fields_map[f_uid[1:]]['db_uid']]['db_pk_field_uid'])
            else:
                qslt_var = 'SELECT variant_id, bin, chr, pos, ref, alt, transcript_pk_value FROM wt_{0} WHERE annotated=False AND transcript_pk_field_uid IS NULL LIMIT {1}'.format(analysis.id, UPDATE_LOOP_RANGE)
                query = "UPDATE wt_{0} SET annotated=True, {1} FROM (SELECT _var.variant_id, {2} \
                    FROM ({3}) AS _var {4}) AS _ann \
                    WHERE wt_{0}.variant_id=_ann.variant_id".format(
                    analysis.id, 
                    qset_ann, 
                    qslt_ann, 
                    qslt_var, 
                    qjoin)


            if qset_ann != "":
                # Mark all variant as not annotated (to be able to do a "resumable update")
                log(" > mark all wt entries as 'not annotated'")
                execute("UPDATE wt_{} SET annotated=False".format(analysis.id))
                for page in range(0, total, UPDATE_LOOP_RANGE):
                    log(" > update wt from {} to {} (on {})".format(page, page+UPDATE_LOOP_RANGE, total))
                    execute(query)
                    progress.update({"progress_current": page})
                    core.notify_all(None, data=progress)
            progress.update({"step": 5, "progress_current": total})
            core.notify_all(None, data=progress)

        # Apply queries to update attributes and filters columns in the wt
        if len(update_queries) > 0:
            log(" > update filters and attributes")
            execute("".join(update_queries))
        progress.update({"step": 6})
        core.notify_all(None, data=progress)

        # Check if trio analysis => htz_comp field
        if analysis.settings["trio"]:
            trio = analysis.settings["trio"]
            colname = "htz_comp_{}_{}_{}".format(trio["child"], trio["mother"], trio["father"])
            if colname not in current_fields:
                log(" > trio analysis : create precomputed column")
                execute("ALTER TABLE wt_{} ADD COLUMN {} boolean DEFAULT False".format(analysis.id, colname))
                
                query = "UPDATE wt_{0} u SET htz_comp_{1}_{2}_{3}=TRUE WHERE u.variant_id IN ( SELECT DISTINCT UNNEST(sub.vids) as variant_id FROM ( SELECT array_agg(w.variant_id) as vids, g.name2 FROM wt_{0} w  INNER JOIN refgene{4} g ON g.chr=w.chr AND g.txrange @> w.pos  WHERE  s{1}_gt > 1 --  variant de l'enfant r/a ou a1/a2 AND ( (s{2}_gt > 1 AND (s{3}_gt = NULL or s{3}_gt < 2)) OR (s{3}_gt > 1 AND (s{2}_gt = NULL or s{2}_gt < 2))) GROUP BY name2 HAVING count(*) > 1) AS sub )"
                log(" > trio analysis : compute column : {}".format(colname))
                db_ref_suffix= "_hg19"  # execute("SELECT table_suffix FROM reference WHERE id={}".format(reference_id)).first().table_suffix
                execute(query.format(analysis.id, trio["child"], trio["mother"], trio["father"], db_ref_suffix))
        # Update count stat of the analysis
        query = "UPDATE analysis SET status='ready' WHERE id={}".format(analysis.id)
        log(" > wt is ready")
        execute(query)



    def request(self, analysis_id, mode, filter_json, fields=None, order=None, limit=100, offset=0, count=False):
        """

        """
        # Check parameters: if no field, select by default the first field avalaible to avoir error
        if fields is None:
            fields = [next(iter(self.fields_map.keys()))]
        if type(analysis_id) != int or analysis_id <= 0:
            analysis_id = None
        if mode not in ["table", "list"]:
            mode = "table"

        # Get analysis data and check status if ok to do filtering
        analysis = Analysis.from_id(analysis_id)
        if analysis is None:
            raise RegovarException("Not able to retrieve analysis with provided id: {}".format(analysis_id))

        # Parse data to generate sql query and retrieve list of needed annotations databases/fields
        query, field_uids, dbs_uids, sample_ids, filter_ids, attributes = self.build_query(analysis, mode, filter_json, fields, order, limit, offset, count)

        # Prepare database working table
        if not analysis.status or analysis.status == 'empty':
            self.create_working_table(analysis, sample_ids)
            # Update working table by computing annotation
            field_uids = []
            for db_uid in analysis.settings["annotations_db"]:
                field_uids.extend(self.db_map[db_uid]["fields"].keys())
            self.update_working_table(analysis, sample_ids, field_uids, filter_ids, attributes)
        else:
            self.update_working_table(analysis, sample_ids, field_uids, filter_ids, attributes)

        # Execute query
        sql_result = None
        with Timer() as t:
            sql_result = execute(' '.join(query))
        log("---\nFields:\n{0}\nFilter:\n{1}\nQuery:\n{2}\nRequest query: {3}".format(fields, filter_json, '\n'.join(query), t))

        # Save filter in analysis settings
        if not count and analysis_id > 0:
            settings = {}
            try:
                analysis.filter = filter_json
                analysis.fields = fields
                analysis.order = [] if order is None else order
                analysis.save()
            except:
                # TODO: log error
                err("Not able to save current filter")

        # Get result
        if count:
            result = sql_result.first()[0]
        else:
            result = []
            with Timer() as t:
                if sql_result is not None:
                    for row in sql_result:
                        entry = {"id" : "{}_{}_{}".format(row.variant_id, row.transcript_pk_field_uid, row.transcript_pk_value )}
                        for f_uid in fields:
                            # Manage special case for fields splitted by sample
                            if self.fields_map[f_uid]['name'].startswith('s{}_'):
                                pattern = "row." + self.fields_map[f_uid]['name']
                                r = {}
                                for sid in sample_ids:
                                    r[sid] = FilterEngine.parse_result(eval(pattern.format(sid)))
                                entry[f_uid] = r
                            else:
                                if self.fields_map[f_uid]['db_name_ui'] == 'Variant':
                                    entry[f_uid] = FilterEngine.parse_result(eval("row.{}".format(self.fields_map[f_uid]['name'])))
                                else:
                                    entry[f_uid] = FilterEngine.parse_result(eval("row._{}".format(f_uid)))
                        result.append(entry)
            log("Result processing: {0}\nTotal result: {1}".format(t, "-"))
        return result


    def build_query(self, analysis, mode, filter, fields, order=None, limit=100, offset=0, count=False):
        """
            This method build the sql query according to the provided parameters, and also build several list  with ids of
            fields, databases, sample, etc... all information that could be used by the analysis to work.
        """
        # Data that will be computed and returned by this method !
        query = []       # sql queries that correspond to the provided parameters (we will have several queries if need to create temp tables)
        field_uids = []  # list of annotation field's uids that need to be present in the analysis working table
        db_uids = []     # list of annotation databases uids used for the analysis
        sample_ids = []  # list of sample's ids used for the analysis
        filter_ids = []  # list of saved filter's ids for this analysis
        attributes = {}  # list of attributes (and their values by sample) defined for this analysis

        # Retrieve sample ids of the analysis
        for row in execute("select sample_id from analysis_sample where analysis_id={0}".format(analysis.id)):
            sample_ids.append(str(row.sample_id))

        # Retrieve attributes of the analysis
        for row in execute("select sample_id, value, name from attribute where analysis_id={0}".format(analysis.id)):
            if row.name not in attributes.keys():
                attributes[row.name] = {row.sample_id: row.value}
            else:
                attributes[row.name].update({row.sample_id: row.value})

        # Init fields uid and db uids with the defaults annotations fields according to the reference (hg19 by example)
        # for row in execute("SELECT d.uid AS duid, f.uid FROM annotation_database d INNER JOIN annotation_field f ON d.uid=f.database_uid WHERE d.reference_id={} AND d.type='variant' AND f.wt_default=True".format(reference_id)):
        #     if row.duid not in db_uids:
        #         db_uids.append(row.duid)
        #     field_uids.append(row.uid)

        # Retrieve saved filter's ids of the analysis - and parse their filter to get list of dbs/fields used by filters
        for row in execute("select id, filter from filter where analysis_id={0} ORDER BY id ASC".format(analysis.id)):  # ORDER BY is important as a filter can "called" an oldest filter to be build.
            filter_ids.append(row.id)
            q, f, d = self.parse_filter(analysis, mode, sample_ids, row.filter, fields, None, None)
            field_uids = array_merge(field_uids, f)
            db_uids = array_merge(db_uids, d)

        # Parse the current filter
        query, f, d = self.parse_filter(analysis, mode, sample_ids, filter, fields, order, limit, offset, count)
        field_uids = array_merge(field_uids, f)
        db_uids = array_merge(db_uids, d)

        # return query and all usefulldata about annotations needed to execute the query
        return query, field_uids, db_uids, sample_ids, filter_ids, attributes


    def parse_filter(self, analysis, mode, sample_ids, filters, fields=[], order=None, limit=100, offset=0, count=False):
        """
            This method parse the json filter and return the corresponding postgreSQL query, and also the list of fields and databases uid used by the query
            (thoses databases/fields must be present in the working table to be run succefully the query)
        """
        # Init some global variables
        wt = 'wt_{}'.format(analysis.id)
        query = ""
        field_uids = []
        db_uids = []
        with_trx = False

        # Build SELECT
        fields_names = []
        for f_uid in fields:
            if self.fields_map[f_uid]["db_uid"] not in db_uids:
                db_uids.append(self.fields_map[f_uid]["db_uid"])
            field_uids.append(f_uid)
            if self.fields_map[f_uid]['db_name_ui'] == 'Variant':
                # Manage special case for fields splitted by sample
                if self.fields_map[f_uid]['name'].startswith('s{}_'):
                    # Special case of htz composite that have different maining in trio or solo
                    if self.fields_map[f_uid]['name'] == "s{}_is_composite" and isinstance(analysis.settings["trio"], dict):
                        trio = analysis.settings["trio"]
                        fields_names.append('{}.htz_comp_{}_{}_{}'.format(wt, trio["child"], trio["mother"], trio["father"]))
                    else:
                        fields_names.extend(['{}.'.format(wt) + self.fields_map[f_uid]['name'].format(s) for s in sample_ids])
                else:
                    fields_names.append('{}.{}'.format(wt, self.fields_map[f_uid]["name"]))
            else:
                with_trx = with_trx or self.fields_map[f_uid]["db_type"] == "transcript"
                fields_names.append('{}._{}'.format(wt, f_uid))
        q_select = 'variant_id, transcript_pk_field_uid, transcript_pk_value{} {}'.format(',' if len(fields_names) > 0 else '', ', '.join(fields_names))

        # Build FROM/JOIN
        q_from = wt

        # Build WHERE
        temporary_to_import = {}

        def check_field_uid(data):
            if data[0] == 'field':
                if self.fields_map[data[1]]["db_uid"] not in db_uids:
                    db_uids.append(self.fields_map[data[1]]["db_uid"])
                field_uids.append(data[1])

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
                # If comparaison with a field, the field MUST BE the first operande
                if data[1][0] == 'field':
                    metadata = self.fields_map[data[1][1]]
                else:
                    metadata = {"type": "string", "name":""}
                check_field_uid(data[1])
                check_field_uid(data[2])
                # Manage special case for fields splitted by sample
                if metadata['name'].startswith('s{}_'):
                    # With these special fields, we don't allow field to field comparaison. 
                    # First shall always be the special fields, and the second shall be everythong except another special fields
                    # Special case of htz composite that have different maining in trio or solo
                    if metadata['name'] == "s{}_is_composite" and isinstance(analysis.settings["trio"], dict):
                        trio = analysis.settings["trio"]
                        return '{}.htz_comp_{}_{}_{}=TRUE'.format(wt, trio["child"], trio["mother"], trio["father"])
                    else:
                        return ' (' + ' OR '.join(['{0}{1}{2}'.format(metadata['name'].format(s), FilterEngine.op_map[operator], parse_value(metadata["type"], data[2])) for s in sample_ids]) + ') '
                else:
                    return '{0}{1}{2}'.format(parse_value(metadata["type"], data[1]), FilterEngine.op_map[operator], parse_value(metadata["type"], data[2]))
            elif operator in ['~', '!~']:
                check_field_uid(data[1])
                check_field_uid(data[2])
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
            ttable_quer_map = "CREATE TABLE IF NOT EXISTS {0} AS {1}; "
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
            temporary_to_import[tmp_table_name] = {'query': tmp_table_query + "CREATE INDEX IF NOT EXISTS {0}_idx_var ON {0} USING btree (bin, chr, pos);".format(tmp_table_name)}
            return tmp_table_name

        def parse_value(ftype, data):
            if data[0] == 'field':
                if self.fields_map[data[1]]["type"] == ftype:
                    if self.fields_map[data[1]]['db_name_ui'] == 'Variant':
                        return "{0}".format(self.fields_map[data[1]]["name"])
                    else:
                        return "_{0}".format(data[1])
            if data[0] == 'value':
                if ftype in ['int', 'float', 'enum', 'percent', 'bool', 'sample_array']:
                    return str(data[1])
                elif ftype == 'string':
                    return "'{0}'".format(data[1])
                elif ftype == 'string%':
                    return "'%%{0}%%'".format(data[1])
                elif ftype == 'range' and len(data) == 3:
                    return 'int8range({0}, {1})'.format(data[1], data[2])
            raise RegovarException("FilterEngine.request.parse_value - Unknow type: {0} ({1})".format(ftype, data))

        # q_where = ""
        # if len(sample_ids) == 1:
        #     q_where = "{0}.sample_id={1}".format(wt, sample_ids[0])
        # elif len(sample_ids) > 1:
        #     q_where = "{0}.sample_id IN ({1})".format(wt, ','.join(sample_ids))

        q_where = build_filter(filters)
        if q_where is not None and len(q_where.strip()) > 0:
            q_where = "WHERE " + q_where

        # Build FROM/JOIN according to the list of used annotations databases
        q_from += " ".join([t['from'] for t in temporary_to_import.values()])

        # Build ORDER BY
        # TODO : actually, it's not possible to do "order by" on special fields (GT and DP because they are split by sample)
        q_order = ""
        if order is not None and len(order) > 0:
            orders = []

            for f_uid in order:
                asc = 'ASC'
                if f_uid[0] == '-':
                    f_uid = f_uid[1:]
                    asc = 'DESC'
                if self.fields_map[f_uid]['db_name_ui'] == 'Variant':
                    # Manage special case for fields splitted by sample
                    if self.fields_map[f_uid]['name'].startswith('s{}_'):
                        pass
                    else:
                        orders.append('{} {}'.format(self.fields_map[f_uid]["name"], asc))
                else:
                    orders.append('_{} {}'.format(f_uid, asc))
            q_order = 'ORDER BY {}'.format(', '.join(orders))

        # build final query
        query_tpm = [t['query'] for t in temporary_to_import.values()]
        if count:
            query_req = "SELECT DISTINCT {0} FROM {1} {2}".format(q_select, q_from, q_where)
            query = query_tpm + ['SELECT COUNT(*) FROM ({0}) AS sub;'.format(query_req)]
        else:
            query_req = "SELECT DISTINCT {0} FROM {1} {2} {3} {4} {5};".format(q_select, q_from, q_where, q_order, 'LIMIT {}'.format(limit) if limit is not None else '', 'OFFSET {}'.format(offset) if offset is not None else '')
            query = query_tpm + [query_req]
        return query, field_uids, db_uids


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
 
