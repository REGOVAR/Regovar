#!env/python3
# coding: utf-8
import os
import datetime
import asyncio
import sqlalchemy
#import multiprocessing as mp


from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.orm import sessionmaker

from core.framework.common import *
from core.framework.erreurs_list import *
import config as C




# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# DATABASE CONNECTION
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

def init_pg(user, password, host, port, db):
    '''Returns a connection and a metadata object'''
    try:
        url = 'postgresql://{}:{}@{}:{}/{}'.format(user, password, host, port, db)
        con = sqlalchemy.create_engine(url, client_encoding='utf8')
    except Exception as err:
        raise RegovarException("Unable to connect to database", "", err)
    return con
    

# Connect and map the engine to the database
Base = automap_base()
__db_engine = init_pg(C.DATABASE_USER, C.DATABASE_PWD, C.DATABASE_HOST, C.DATABASE_PORT, C.DATABASE_NAME)
try:
    Base.prepare(__db_engine, reflect=True)
    Base.metadata.create_all(__db_engine)
    Session = sessionmaker(bind=__db_engine)
except Exception as err:
    raise RegovarException("Error occured when initialising database", "", err)



__db_session = Session()
#p__db_pool = mp.Pool()
#p__async_job_id = 0
#p__async_jobs = {}




def __execute_async(async_job_id, query):
    """
        Internal method used to execute query asynchronously
    """
    # As execution done in another thread, use also another db session to avoid thread conflicts
    session = Session()
    result = None
    try:
        result = session.execute(query)
        session.commit()
        session.close()
    except Exception as err:
        session.close()
        r = RegovarException(ERR.E100001, "E100001", err)
        log_snippet(query, r)
        return (async_job_id, r)
    return (async_job_id, result)


#def p__execute_callback(result):
    #"""
        #Internal callback method for asynch query execution. 
    #"""
    #job_id = result[0]
    #result = result[1]
    ## Storing result in dictionary
    #p__async_jobs[job_id]['result'] = result

    ## Call callback if defined
    #if p__async_jobs[job_id]['callback']:
        #p__async_jobs[job_id]['callback'](job_id, result)

    ## Delete job 
    #del p__async_jobs[async_job_id]







# =====================================================================================================================
# MODEL METHODS
# =====================================================================================================================


def get_or_create(session, model, defaults=None, **kwargs):
    """
        Generic method to get or create a SQLalchemy object from database
    """
    if defaults is None:
        defaults = {}
    try:
        query = session.query(model).filter_by(**kwargs)
        instance = query.first()
        if instance:
            instance.init()
            return instance, False
        else:
            session.begin(nested=True)
            try:
                params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
                params.update(defaults)
                instance = model(**params)
                session.add(instance)
                session.commit()
                return instance, True
            except IntegrityError as e:
                session.rollback()
                instance = query.one()
                return instance, False
    except Exception as e:
        raise e


def check_session(obj):
    s = Session.object_session(obj)
    if not s :
        __db_session.add(obj)


def generic_save(obj):
    """
        generic method to save SQLalchemy object into database
    """
    try:
        s = Session.object_session(obj)
        if not s :
            s = __db_session
            s.add(obj)
        obj.update_date = datetime.datetime.now()
        s.commit()
    except Exception as err:
        raise RegovarException("Unable to save object in the database", "", err)


def generic_count(obj):
    """
        generic method to count how many object in the table
    """
    try:
        return __db_session.query(obj).count()

    except Exception as err:
        raise RegovarException("Unable to count how many object in the table", "", err)
    


def session():
    """
        Return the current pgsql session (SQLAlchemy)
    """
    return __db_session


def execute(query):
    """
        Synchrone execution of the query. If error occured, raise RegovarException
    """
    result = None
    try:
        s = Session()
        result = s.execute(query)
        s.commit()
    except Exception as err:
        r = RegovarException(ERR.E100001, "E100001", err)
        log_snippet(query, r)
        raise r
    return result


#def execute_bw(query, callback=None):
    #"""
        #Execute in background worker:
        #Asynchrone execution of the query in an other thread. An optional callback method that take 2 arguments (job_id, query_result) can be set.
        #This method return a job_id for this request that allow you to cancel it if needed
    #"""
    #global p__async_job_id, p__async_jobs, p__db_pool
    #p__async_job_id += 1
    #t = p__db_pool.apply_async(__execute_async, args = (p__async_job_id, query,), callback=p__execute_callback)
    #p__async_jobs[p__async_job_id] = {"task" : t, "callback": callback, "query" : query, "start": datetime.datetime.now}
    #return p__async_job_id


async def execute_aio(query):
    """
        execute as coroutine
        Asynchrone execution of the query as coroutine
    """
    # Execute the query in another thread via coroutine
    loop = asyncio.get_event_loop()
    futur = loop.run_in_executor(None, __execute_async, None, query)

    # Aio wait the end of the async task to return result
    result = await futur
    return result[1]


#def cancel(async_job_id):
    #"""
        #Cancel an asynch job running in the threads pool
    #"""
    #if async_job_id in p__async_jobs.keys():
        #loop = asyncio.get_event_loop()
        #loop.call_soon_threadsafe(p__async_jobs.keys[async_job_id]["task"].cancel)
        #log("Model async query (id:{}) canceled".format(async_job_id))
    #else:
        #war("Model unable to cancel async query (id:{}) because it doesn't exists".format(async_job_id)) 



def sql_escape(value):
    if type(value) is str:
        value = value.replace("'", "''")
    return value
