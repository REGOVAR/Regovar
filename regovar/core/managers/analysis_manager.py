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
from core.framework.postgresql import execute
from core.model import *






# =====================================================================================================================
# Analysis MANAGER
# =====================================================================================================================
class AnalysisManager:
    def __init__(self):
        pass


    def list(self):
        """
            Return all analyses with "minimal data"
        """
        sql = "SELECT id, project_id, name, comment, create_date, update_date, reference_id, status FROM analysis"
        result = []
        for res in execute(sql): 
            result.append({
                "id": res.id,
                "project_id": res.project_id,
                "name": res.name,
                "comment": res.comment,
                "create_date": res.create_date.isoformat(),
                "update_date": res.update_date.isoformat(),
                "reference_id": res.reference_id,
                "status": res.status
            })
        return result



    def get(self, fields=None, query=None, order=None, offset=None, limit=None, depth=0):
        """
            Generic method to get analysis metadata according to provided filtering options.
        """
        if not isinstance(fields, dict):
            fields = None
        if query is None:
            query = {}
        if order is None:
            order = "name"
        if offset is None:
            offset = 0
        if limit is None:
            limit = RANGE_MAX
        s = Session()
        analyses = s.query(Analysis).filter_by(**query).order_by(order).limit(limit).offset(offset).all()
        for a in analyses: a.init(depth)
        return analyses
    
    
    
    def get_filters(self, analysis_id, depth=0):
        """
            Return the list of filters for the provided analysis
        """
        s = Session()
        filters = s.query(Filter).filter_by(analysis_id=analysis_id).order_by("name").all()
        for f in filters: f.init(depth)
        return filters
    
    

    def create(self, name, project_id, ref_id, template_id=None):
        """
            Create a new analysis in the database.
        """
        from core.core import core
        if ref_id not in core.annotations.ref_list.keys():
            raise RegovarException(msg="A Valid ref_id must be provided to create an analyusis", exception=ex)
        try:
            analysis = Analysis.new()            
            analysis.name = name
            analysis.project_id = project_id
            analysis.reference_id = ref_id
            analysis.template = template_id
            # Set fields with default Variant's fields
            analysis.fields = []
            db_uid = core.annotations.db_list[0]['db']['Variant']['versions']['_all_']
            for f in core.annotations.db_map[db_uid]["fields"][1:]:
                analysis.fields.append(f)
            analysis.save()
            log('Core.AnalysisManager.create : New analysis \"{}\" created with the id {}.'.format(name, analysis.id))
            return analysis
        except Exception as ex:
            raise RegovarException(msg="Unable to create new analysis with provided data", exception=ex)
        return None



    def load(self, analysis_id):
        """
            Load all data about the analysis with the provided id and return result as JSON object.
        """
        analysis = Analysis.from_id(analysis_id, 1)
        return result



    def delete(self, analysis_id, definitely=False):
        """ 
            Delete the analysis
            When normal user delete an analysis, this one is put in the trash project
            Then an admin can definitely delete the analysis (with the flag finally set to True)
        """
        analysis = Analysis.from_id(analysis_id)
        if not analysis: raise RegovarException("Unable to find analysis with the provided id {}".format(analysis_id))

        if definitely:
            self.clear_temps_data(analysis_id)

            # Delete related files
            # TODO

            sql = "DELETE FROM analysis WHERE id={0}; DELETE FROM filter WHERE analysis_id={0};".format(analysis_id)
            sql+= "DELETE FROM analysis_sample WHERE analysis_id={0}; DELETE FROM attribute WHERE analysis_id={0}".format(analysis_id)
            sql+= "DELETE FROM analysis_indicator_value WHERE analysis_id={0};".format(analysis_id)
        else:
            sql = "UPDATE analysis SET project_id=0 WHERE id={0}; ".format(analysis_id)
        result = analysis.to_json()
        execute(sql)
        return result


    def update(self, analysis_id, data):
        """
            Update analysis with provided data. Data that are not provided are not updated (ignored).
        """
        analysis = Analysis.from_id(analysis_id)
        if not analysis:
            raise RegovarException("Unable to find analysis with the provided id {}".format(analysis_id))
        
        # Update analysis's simple properties
        analysis.load(data)
        
        # saved filters
        if "filters" in data.keys():
            # delete old filters
            execute("DELETE FROM filter WHERE analysis_id={}".format(analysis_id))
            # create new associations
            query = "INSERT INTO filter (analysis_id, name, filter) VALUES "
            subquery = "({0}, '{1}', '{2}'')"
            query = query + ', '.join([subquery.format(analysis_id, f['name'], f['filter']) for f in data["filters"]])
            execute(query)

        # Updating dynamicaly samples not supported. it's better for the user to recreate a new analysis


        # attributes + values
        if "attributes" in data.keys():
            # create new attributes
            pattern = "({0}, {1}, '{2}', '{3}', MD5(CONCAT('{2}', '{3}')))"
            data['attributes'] = [a for a in data['attributes'] if a['name'] != ""]
            query = ', '.join([pattern.format(analysis_id, sid, sql_escape(att['name']), sql_escape(att['samples_values'][sid])) for att in data['attributes'] for sid in att['samples_values']])
            # check if query seems good then apply change
            if query != "":
                execute("DELETE FROM attribute WHERE analysis_id={}".format(analysis_id))
                execute("INSERT INTO attribute (analysis_id, sample_id, name, value, wt_col_id) VALUES " + query)
            else:
                # TODO: log error
                pass

        # return reloaded analysis
        return Analysis.from_id(analysis_id, 1)
        


    def clear_temps_data(self, analysis_id):
        """
            Clear temporary data of the analysis (to save disk space by example)
        """
        analysis = Analysis.from_id(analysis_id)
        if not analysis:
            raise RegovarException("Unable to fin analysis with the provided id {}".format(analysis_id))
        try:
            execute("DROP TABLE IF EXISTS wt_{} CASCADE;".format(analysis_id))
            execute("DROP TABLE IF EXISTS wt_{}_var CASCADE".format(analysis_id))
            execute("DROP TABLE IF EXISTS wt_{}_tmp CASCADE".format(analysis_id))
            analysis.status = "empty"
            analysis.save()
        except Exception as ex:
            raise RegovarException("Error occure when trying to clear temporary data of the analysis {}.".format(analysis_id), exception=ex)
        return True



    #async def load_file(self, analysis_id, file_id):
        #pfile = File.from_id(file_id)
        #if pfile == None:
            #raise RegovarException("Unable to retrieve the file with the provided id : " + file_id)
        
        ## Importing to the database according to the type (if an import module can manage it)
        #log('Looking for available module to import file data into database.')
        #for m in self.import_modules.values():
            #if pfile.type in m['info']['input']:
                #log('Start import of the file (id={0}) with the module {1} ({2})'.format(file_id, m['info']['name'], m['info']['description']))
                #await m['do'](pfile.id, pfile.path, core)
                ## Reload annotation's databases/fields metadata as some new annot db/fields may have been created during the import
                #await self.annotation_db.load_annotation_metadata()
                #await self.filter.load_annotation_metadata()
                #break
        
        

    async def create_update_filter(self, filter_id, data):
        """
            Create or update a filter for the analysis with the provided id.
        """
        from core.core import core
        
        # First need to check that analysis is ready for that
        analysis = Analysis.from_id(data["analysis_id"])
        if analysis is None or analysis.status != "ready":
            raise RegovarException("Not able to create filter for the analysis (id={}). Analysis not in 'ready' state.".format(data["analysis_id"]))
            
        # Save filter informations
        filter = Filter.from_id(filter_id)
        if not filter:
            filter = Filter.new()
        
        filter.load(data)
        
        # Update working table async (if needed)
        def update_analysis_async(analysis, filter_id, data):
            from core.model import Filter
            total_results = core.filters.update_wt(analysis, "filter_{}".format(filter_id), data["filter"])
            filter = Filter.from_id(filter_id)
            filter.total_variants = execute("SELECT COUNT(DISTINCT variant_id) FROM wt_{} WHERE filter_{}".format(analysis.id, filter_id)).first()[0]
            filter.total_results = total_results
            filter.progress = 1
            filter.save()
            core.notify_all(data={'action':'filter_update', 'data': filter.to_json()})
            
        if "filter" in data.keys():
            filter.progress = 0
            filter.save()
            run_async(update_analysis_async, analysis, filter.id, data)
    
        return filter
        
        
        
    def update_selection(self, analysis_id, is_selected, variant_ids):
        """
            Add or remove variant/trx from the selection of the analysis
        """
        analysis = Analysis.from_id(analysis_id)
        if not isinstance(variant_ids, list) or not analysis or not analysis.status == 'ready':
            return False
        query = ""
        for vid in variant_ids:
            ids = vid.split("_")
            if len(ids) == 1:
                query += "UPDATE wt_{} SET is_selected={} WHERE variant_id={}; ".format(analysis.id, is_selected, vid)
            else:
                query += "UPDATE wt_{} SET is_selected={} WHERE variant_id={} AND trx_pk_value='{}'; ".format(analysis.id, is_selected, ids[0], ids[1])
        execute(query)
        return True
    
    

    def get_selection(self, analysis_id):
        """
            Return list of selected variant (with same columns as set for the current filter)
        """
        from core.core import core
        
        analysis = Analysis.from_id(analysis_id)
        if not analysis:
            raise RegovarException("Unable to find analysis with the provided id: {}".format(analysis_id))
        
        fields = core.filters.parse_fields(analysis, analysis.fields, "")
        query = "SELECT {} FROM wt_{} WHERE is_selected".format(fields, analysis_id)
        result = []
        for row in execute(query):
            result.append({fid:row[fid] for fid in fields.split(", ")})
        
        return result
    
    
    
    



