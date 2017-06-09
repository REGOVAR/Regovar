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
# Analysis MANAGER
# =====================================================================================================================
class AnalysisManager:
    def __init__(self):
        pass


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
        s = session()
        analyses = s.query(Analysis).filter_by(**query).order_by(order).limit(limit).offset(offset).all()
        for a in analyses: a.init(depth)
        return analyses
    


    def create(self, name, ref_id, template_id=None):
        """
            Create a new analysis in the database.
        """
        from core.core import core        
        try:
            if ref_id not in core.annotations.ref_list.keys():
                ref_id = DEFAULT_REFERENCIAL_ID
            settings = {"fields": [], "filter": ['AND', []]}
            db_uid = core.annotations.db_list[ref_id]['db']['Variant']['versions']['']
            for f in core.annotations.db_map[db_uid]["fields"][1:]:
                settings["fields"].append(f)
            analysis = Analysis.new()
            analysis.name = name
            analysis.reference_id = ref_id
            analysis.template = template_id
            analysis.settings = json.dumps(settings)
            analysis.save()
            log('Core.AnalysisManager.create : New analysis \"{}\" created with the id {}.'.format(name, analysis.id))
            return analysis
        except Exception as ex:
            raise RegovarException("Unable to create new analysis with provided data", "", ex)
        return None


    def load(self, analysis_id):
        """
            Load all data about the analysis with the provided id and return result as JSON object.
        """
        analysis = execute("SELECT a.id, a.name, a.update_date, a.creation_date, a.settings, t.name AS t_name, t.id AS t_id FROM analysis a LEFT JOIN template t ON a.template_id = t.id WHERE a.id = {0}".format(analysis_id)).first()
        result = {
            "id": analysis.id,
            "name": analysis.name,
            "update_date": analysis.update_date.ctime() if analysis.update_date is not None else datetime.datetime.now().ctime(),
            "creation_date": analysis.creation_date.ctime() if analysis.creation_date is not None else datetime.datetime.now().ctime(),
            "template_id": analysis.t_id,
            "template_name": analysis.t_name,
            "samples": [],
            "attributes": [],
            "reference_id": 2,  # TODO: reference_id shall be associated to the analysis and retrieved in the database
            "filters": {}}
        if analysis.settings is not None and analysis.settings.strip() is not "":
            result["settings"] = json.loads(analysis.settings)
        else:
            result["settings"] = '{"fields": [1,3,4,5,6,7,8], "filter":["AND", []]}'

        # Get predefined filters set for this analysis
        query = "SELECT * FROM filter WHERE analysis_id = {0} ORDER BY name ASC;"
        for f in execute(query.format(analysis_id)):
            result["filters"][f.id] = {"name": f.name, "description": f.description, "filter": json.loads(f.filter)}

        # Get attributes used for this analysis
        query = "SELECT a.sample_id, a.name, a.value \
            FROM attribute a \
            WHERE a.analysis_id = {0}\
            ORDER BY a.name ASC, a.sample_id ASC"

        current_attribute = None
        for r in execute(query.format(analysis_id)):
            if current_attribute is None or current_attribute != r.name:
                current_attribute = r.name
                result["attributes"].append({"name": r.name, "samples_value": {r.sample_id: r.value}})
            else:
                result["attributes"][-1]["samples_value"][r.sample_id] = r.value

        # Get Samples used for this analysis
        query = "SELECT s.id, s.name, s.comments, s.is_mosaic, asp.nickname, f.id as f_id, f.name as fname, f.create_date \
            FROM analysis_sample asp \
            LEFT JOIN sample s ON asp.sample_id = s.id \
            LEFT JOIN sample_file sf ON s.id = sf.sample_id \
            LEFT JOIN file f ON f.id = sf.file_id \
            WHERE asp.analysis_id = {0}"
        for r in execute(query.format(analysis_id)):
            result["samples"].append({
                "id": r.id,
                "name": r.name,
                "comments": r.comments,
                "is_mosaic": r.is_mosaic,
                "nickname": r.nickname,
                "file_id": r.f_id,
                "file_name": r.fname,
                "create_date": r.create_date.ctime() if r.create_date is not None else datetime.datetime.now().ctime(),
                "attributes": {}})
            for a in result["attributes"]:
                if r.id in a["samples_value"].keys():
                    result["samples"][-1]["attributes"][a['name']] = a["samples_value"][r.id]
                else:
                    result["samples"][-1]["attributes"][a['name']] = ""

        return result




    def update(self, analysis_id, data):
        """
            Update analysis with provided data. Data that are not provided are not updated (ignored).
        """
        # BASICS SETTINGS (current filter and displayed fields)
        if "fields" in data.keys() or "filter" in data.keys() or "selection" in data.keys():
            # retrieved current settings from database
            settings = {}
            try:
                settings = json.loads(execute("SELECT settings FROM analysis WHERE id={}".format(analysis_id)).first().settings)
            except:
                # TODO: log error
                settings = {}
            if "fields" in data.keys():
                settings["fields"] = data["fields"]
            if "filter" in data.keys():
                settings["filter"] = data["filter"]
            if "selection" in data.keys():
                settings["selection"] = data["selection"]
            # update database
            main_query = "settings='{0}', ".format(json.dumps(settings))

        # saved filters
        if "filters" in data.keys():
            # delete old filters
            execute("DELETE FROM filter WHERE analysis_id={}".format(analysis_id))
            # create new associations
            query = "INSERT INTO filter (analysis_id, name, filter) VALUES "
            subquery = "({0}, '{1}', '{2}'')"
            query = query + ', '.join([subquery.format(analysis_id, f['name'], f['filter']) for f in data["filters"]])
            execute(query)

        # samples + nickname
        if "samples" in data.keys():
            # create new associations
            pattern = "({0}, {1}, {2})"
            query = ', '.join([pattern.format(analysis_id, s['id'], "'{0}'".format(s['nickname']) if 'nickname' in s.keys() else 'NULL') for s in data["samples"]])
            # check if query seems good then apply change
            if query != "":
                # delete old analysis sample associations
                execute("DELETE FROM analysis_sample WHERE analysis_id={}".format(analysis_id))
                execute("INSERT INTO analysis_sample (analysis_id, sample_id, nickname) VALUES " + query)
            else:
                # TODO: log error
                pass

        # attributes + values
        if "attributes" in data.keys():
            # create new attributes
            pattern = "({0}, {1}, '{2}', '{3}')"
            data['attributes'] = [a for a in data['attributes'] if a['name'] != ""]
            query = ', '.join([pattern.format(analysis_id, sid, att['name'], att['samples_value'][sid]) for att in data['attributes'] for sid in att['samples_value']])
            # check if query seems good then apply change
            if query != "":
                execute("DELETE FROM attribute WHERE analysis_id={}".format(analysis_id))
                execute("INSERT INTO attribute (analysis_id, sample_id, name, value) VALUES " + query)
            else:
                # TODO: log error
                pass

        # analysis name, ...
        if "name" in data.keys():
            main_query += "name='{0}', ".format(data["name"])

        # update analysis
        execute("UPDATE analysis SET {0}update_date=CURRENT_TIMESTAMP WHERE id={1}".format(main_query, analysis_id))



    #def load_ped(self, analysis_id, file_path):
    async def load_file(self, analysis_id, file_id):
        pfile = File.from_id(file_id)
        if pfile == None:
            raise RegovarException("Unable to retrieve the file with the provided id : " + file_id)
        
        # Importing to the database according to the type (if an import module can manage it)
        log('Looking for available module to import file data into database.')
        for m in self.import_modules.values():
            if pfile.type in m['info']['input']:
                log('Start import of the file (id={0}) with the module {1} ({2})'.format(file_id, m['info']['name'], m['info']['description']))
                await m['do'](pfile.id, pfile.path, core)
                # Reload annotation's databases/fields metadata as some new annot db/fields may have been created during the import
                await self.annotation_db.load_annotation_metadata()
                await self.filter.load_annotation_metadata()
                break
        
        
        


    def save_filter(self, analysis_id, name, filter_json):
        """
            Save (add) a new filter for the analysis with the provided id.
        """
        instance = None
        session().begin(nested=True)
        try:
            instance = Filter(analysis_id=analysis_id, name=name, filter=json.dumps(filter_json))
            session().add(instance)
            session().commit()  # commit the save point into the session (opened by the .begin() before the try:)
            session().commit()  # commit into the database.
            return instance.to_json(), True
        except IntegrityError as e:
            session().rollback()
        return None, False


    def update_filter(self, filter_id, name, filter_json):
        query = "UPDATE filter SET name='{1}', filter='{2}' WHERE id={0}".format(filter_id, name, json.dumps(filter_json))
        execute(query)


    def delete_filter(self, filter_id):
        execute("DELETE FROM filter WHERE id={}".format(filter_id))



    def report(self, analysis_id, report_id, report_data):
        from core.core import core
        # Working cache folder for the report generator
        cache = os.path.join(CACHE_DIR, 'reports/', report_id)
        if not os.path.isdir(cache):
            os.makedirs(cache)

        # Output path where the report shall be stored
        output_path = os.path.join(CACHE_DIR, 'reports/{}-{}-{:%Y%m%d.%H%M%S}.{}'.format(analysis_id, report_id, datetime.datetime.now(), report_data['output']))

        try:
            module = core.report_modules[report_id]
            module['do'](analysis_id, report_data, cache, output_path, annso)
        except Exception as error:
            # TODO: log error
            err("Error occured: {0}".format(error))

        # Store report in database
        # Todo

        return output_path


    def export(self, analysis_id, export_id, report_data):
        return "<h1>Your export!</h1>" 
