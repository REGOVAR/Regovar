#!env/python3
# coding: utf-8
import ipdb

import os
import psutil
import datetime
import getpass



from config import *
from core.framework.common import *
from core.model import *


class AdminManager:

    async def stats(self):
        db   = await self.db_stats()
        db_tpm = await self.db_tmp_stats(db["database"])
        disk = self.disk_stats()
        cpu  = self.cpu_stats()
        ram  = self.ram_stat()
        # proc = self.proc_stat()
        
        result = {}
        result.update(db)
        result.update(db_tpm)
        result.update(cpu)
        result.update(ram)
        result.update(disk)
        # result.update(proc)
        return result
    


    async def db_tmp_stats(self, db_stats):
        data = []
        sql = "SELECT id, status FROM analysis WHERE status = 'ready'"
        result = await execute_aio(sql)
        for row in result:
            size = 0
            analysis = Analysis.from_id(row.id)
            for db in db_stats:
                if db["name"].startswith("wt_{}".format(row.id)):
                    size += db["totalsize"]
            data.append({"id" :row.id, "size" : size, "name": analysis.name})
        return {"database_tmp" : data}

    async def db_stats(self):
        """
            Return stats on the sql database
        """
        refs   = {}
        annots = {}
        tables = []
        regovar_tables_description = {
            "annotation_field" : "Description of vcf annotations databases fields",
            "analysis" : "Filtering analysis",
            "sample" : "VCF samples",
            "annotation_database" : "Descriptions of vcf annotations databases",
            "user" : "Regovar user",
            "event" : "Logged events",
            "reference" : "Genom refereces",
            "parameter" : "Regovar server parameters",
            "indicator" : "Custom indicators definitions",
            "attribute" : "Samples attributes definitions",
            "filter" : "Custom filters definition for filtering analysis",
            "job" : "Pipeline job (run)",
            "pipeline" : "Installed custom pipeline on the server",
            "variant" : "Variant information (chr, pos, ref, ...)",
            "sample_variant" : "Specific sample information by variant (GT, DP, ...)",
            }
        
        # references
        sql = "select name, table_suffix from reference"
        result = await execute_aio(sql)
        for row in result:
            refs.update({row.table_suffix: row.name})
                
        # annotations db infos
        sql = "select name, name_ui, version, description from annotation_database where reference_id > 0"
        result = await execute_aio(sql)
        for row in result:
            annots.update({row.name: "{} ({}) : {}".format(row.name_ui, row.version, row.description)})
        
        # get db infos
        
        def find_section(table_name):
            if table_name.startswith("wt_"):
                return "Tmp"
            for suffix in refs.keys():
                if table_name.endswith("_" + suffix):
                    return refs[suffix]
            return "Regovar"
        
        def get_description(table_name):
            if table_name in list(annots.keys()):
                return annots[table_name]
            # clean table name (remove suffix if exists)
            for suffix in refs.keys():
                if table_name.endswith("_" + suffix):
                    table_name = table_name[:table_name.index("_" + suffix)]
                    break
                
            if table_name in list(regovar_tables_description.keys()):
                return regovar_tables_description[table_name]
            return ""
        
        
        #sql = "SELECT relname as table, pg_size_pretty(pg_total_relation_size(relid)) As size, "
        #sql+= "pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as externalsize, rowcount as rowcount "
        #sql+= "FROM pg_catalog.pg_statio_user_tables "
        #sql+= "LEFT JOIN ("
        #sql+= "SELECT table_name, n_tup_ins - n_tup_del as rowcount "
        #sql+= "FROM (SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name) AS _t "
        #sql+= "LEFT JOIN pg_stat_all_tables ON table_name=relname ORDER BY table_name) AS _sub ON table_name=relname "
        #sql+= "ORDER BY pg_total_relation_size(relid) DESC"
        sql = "SELECT relname as table, pg_relation_size(relid) As size, "
        sql+= "pg_total_relation_size(relid) as totalsize, rowcount as rowcount "
        sql+= "FROM pg_catalog.pg_statio_user_tables "
        sql+= "LEFT JOIN ("
        sql+= "SELECT table_name, n_tup_ins - n_tup_del as rowcount "
        sql+= "FROM (SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name) AS _t "
        sql+= "LEFT JOIN pg_stat_all_tables ON table_name=relname ORDER BY table_name) AS _sub ON table_name=relname "
        
        result = await execute_aio(sql)
        for row in result:
            entry = {
                "section" : find_section(row.table),
                "name"    : row.table,
                "size"    : row.size,
                "totalsize" : row.totalsize,
                "count"   : row.rowcount,
                "desc"    : get_description(row.table)
            }
            tables.append(entry)
        
        
        return {"database" : tables}

            
    
            
    def disk_stats(self):
        """
            Stats about disk usage
        """
        def get_size(start_path = '.'):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(start_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            return total_size
        
        fds = get_size(FILES_DIR)
        tds = get_size(TEMP_DIR)
        cds = get_size(CACHE_DIR)
        dds = get_size(DATABASES_DIR)
        pds = get_size(PIPELINES_DIR)
        jds = get_size(JOBS_DIR)
        
        stats = psutil.disk_usage('/')
        result = {"overall": {"total": stats.total, "used": stats.used, "free": stats.free, "percent": stats.percent}}
        result.update({"files" : get_size(FILES_DIR)})
        result.update({"temp"  : get_size(TEMP_DIR)})
        result.update({"cache" : get_size(CACHE_DIR)})
        result.update({"ext_db" : get_size(DATABASES_DIR)})
        result.update({"pipelines" : get_size(PIPELINES_DIR)})
        result.update({"jobs" : get_size(JOBS_DIR)})
    
        return {"disk" : result}
            
    
    def cpu_stats(self):
        """
            Stats about CPU usage
        """
        cpus = psutil.cpu_percent(interval=0.1, percpu=True)
        return {"cpu": {"count": psutil.cpu_count(logical=False), "virtual": psutil.cpu_count(), "freq" : psutil.cpu_freq().max, "usages" : cpus, "usage": sum(cpus) / len(cpus)}}
            
       
       
    def ram_stat(self):
        """
            Stats about RAM usage
        """
        ram  = psutil.virtual_memory()
        swap = psutil.swap_memory()
        ram  = {"total": ram.total, "available": ram.available, "percent": ram.percent, "used": ram.used, "buffers": ram.buffers, "cached": ram.cached}
        swap = {"total": swap.total, "percent": swap.percent, "used": swap.used, "free": swap.free}
        return {"ram": ram, "swap": swap}
            
            
    def proc_stat(self):
        """
            Stats about process owned by Regovar
        """
        user = getpass.getuser()
        # TODO : manage parent/child process
        result = []
        for pid in psutil.pids():
            p = psutil.Process(pid)
            if p.username() == user:
                date = datetime.datetime.fromtimestamp(p.create_time()).isoformat()
                result.append({"pid": pid, "name": p.name(), "cmd": ' '.join(p.cmdline()), "status": p.status(), "creation": date, "cpu": p.cpu_percent(), "ram": p.memory_percent()})
                
        return {"proc": result}
            
            
            