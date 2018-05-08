#!env/python3
# coding: utf-8
import json
import uuid
import config as C
import glob
import requests
from extratools import *

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.orm import sessionmaker, scoped_session




# Tools & DB connection
def init_pg(user, password, host, port, db):
    '''Returns a connection and a metadata object'''
    try:
        url = 'postgresql://{}:{}@{}:{}/{}'.format(user, password, host, port, db)
        con = sqlalchemy.create_engine(url, client_encoding='utf8')
    except Exception as ex:
        raise RegovarException(code="E000001", exception=ex)
    return con
    

# Connect and map the engine to the database
Base = automap_base()
__db_engine = init_pg(C.DATABASE_USER, C.DATABASE_PWD, C.DATABASE_HOST, C.DATABASE_PORT, C.DATABASE_NAME)
try:
    Base.prepare(__db_engine, reflect=True)
    Base.metadata.create_all(__db_engine)
    Session = scoped_session(sessionmaker(bind=__db_engine))
except Exception as ex:
    print("ERROR when trying to connect to Postgresql database")
    exit(1)
    



def execute_sql(query):
    result = None
    s = Session()
    result = s.execute(query)
    s.commit() 
    return result






dirpath = C.DATABASES_DIR + "/GenesPanel-master"





lst_files = glob.glob(dirpath + "/*.lst")
bed_files = glob.glob(dirpath + "/*.bed")

print (lst_files)
print (bed_files)

# Clear Panel tables
print('Clear database: ', end='', flush=True)
execute_sql("DELETE FROM panel")
execute_sql("DELETE FROM panel_entry")
print('Done')


# Load lst file
print('Load panels from ''lst'' file: ', end='', flush=True)
sql_p = "INSERT INTO panel (id, name) VALUES "
sql_v = "INSERT INTO panel_entry (id, panel_id, version, data) VALUES "
for panel_path in lst_files:
    with open(panel_path, "r") as f:
        # create panel
        filename = panel_path.split("/")[-1]
        pid = uuid.uuid4()
        sql_p += "('{}', '{}'),".format(pid, filename.split(".")[0].replace("_", " "))
        # register entries
        lines = f.readlines()
        vid = uuid.uuid4()
        data = []
        for l in lines:
            name = l.strip()
            data.append({"label": name, "symbol": name})
        sql_v += "('{}', '{}', 'v1', '{}'),".format(vid, pid, json.dumps(data))

execute_sql(sql_p[:-1])
execute_sql(sql_v[:-1])
print('Done')


# Load lst file
# print('Load panels from ''bed'' file: ', end='', flush=True)
# sql_p = "INSERT INTO panel (id, name, description) VALUES "
# sql_v = "INSERT INTO panel_entry (id, panel_id, version, data) VALUES "
# chr_map = {"1":1, "2":2, "3":3, "4":4,"5":5, "6":6, "7":7, "8":8, "9":9, "10":10, "11":11, "12":12, "13":13, "14":14, "15":15, "16":16, "17":17, "18":18, "19":19, "20":20, "21":21, "22":22, "X":23, "Y":24, "M":24}
# for panel_path in bed_files:
#     with open(panel_path, "r") as f:
#         # create panel
#         filename = panel_path.split("/")[-1]
#         pid = uuid.uuid4()
#         name = filename.split(".")
#         sql_p += "('{}', '{}', '{}'),".format(pid, name[0].replace("_", " "), "{} ({})".format(name[1], name[2]))
#         # register entries
#         lines = f.readlines()
#         vid = uuid.uuid4()
#         data = []
#         for l in lines:
#             ldata = l.strip().split("\t")
#             chr = ldata[0][3:]
#             if chr not in chr_map: continue
#             chr = chr_map[chr]
#             data.append({"label": "{} ({})".format(ldata[4], ldata[3]) , "chr": chr, "start":int(ldata[1]), "end":int(ldata[2])})
#         sql_v += "('{}', '{}', 'v1', '{}'),".format(vid, pid, json.dumps(data))

# execute_sql(sql_p[:-1])
# execute_sql(sql_v[:-1])
# print('Done')
