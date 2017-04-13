#!env/python3
# coding: utf-8
import os
import datetime
import uuid
import sqlalchemy
import asyncio
import multiprocessing as mp


from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.orm import sessionmaker


import config as C
import ipdb




def init_pg(user, password, host, port, db):
    '''Returns a connection and a metadata object'''
    url = 'postgresql://{}:{}@{}:{}/{}'.format(user, password, host, port, db)
    con = sqlalchemy.create_engine(url, client_encoding='utf8')
    return con





# =====================================================================================================================
# INTERNAL
# =====================================================================================================================



# Connect and map the engine to the database
Base = automap_base()
__db_engine = init_pg(C.DATABASE_USER, C.DATABASE_PWD, C.DATABASE_HOST, C.DATABASE_PORT, C.DATABASE_NAME)
Base.prepare(__db_engine, reflect=True)
Base.metadata.create_all(__db_engine)
Session = sessionmaker(bind=__db_engine)
__db_session = Session()
__db_pool = mp.Pool()
__async_job_id = 0
__async_jobs = {}



def private_execute_async(async_job_id, query):
    """
        Internal method used to execute query asynchronously
    """
    # As execution done in another thread, use also another db session to avoid thread conflicts
    session = Session()
    result = None
    try:
        result = session.execute(query)
        session.commit()
        session.commit() # Need a second commit to force session to commit :/ ... strange behavior when we execute(raw_sql) instead of using sqlalchemy's objects as query
        session.close()
    except Exception as err:
        ipdb.set_trace()
        log(err)
        session.close()
        return (async_job_id, err)
    return (async_job_id, result)


def private_execute_callback(result):
    """
        Internal callback method for asynch query execution. 
    """
    job_id = result[0]
    result = result[1]
    # Storing result in dictionary
    __async_jobs[job_id]['result'] = result

    # Call callback if defined
    if __async_jobs[job_id]['callback']:
        __async_jobs[job_id]['callback'](job_id, result)

    # Delete job 
    del __async_jobs[async_job_id]







# =====================================================================================================================
# MODEL METHODS
# =====================================================================================================================


def get_or_create(session, model, defaults=None, **kwargs):
    if defaults is None:
        defaults = {}
    try:
        query = session.query(model).filter_by(**kwargs)

        instance = query.first()

        if instance:
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


def session():
    """
        Return the current pgsql session (SQLAlchemy)
    """
    return __db_session


def execute(query):
    """
        Synchrone execution of the query
    """
    result = None
    try:
        result = __db_session.execute(query)
        __db_session.commit()
        __db_session.commit() # Need a second commit to force session to commit :/ ... strange behavior when we execute(raw_sql) instead of using sqlalchemy's objects as query
    except Exception as err:
        ipdb.set_trace()
        err(err)
    return result


def execute_bw(query, callback=None):
    """
        execute in background worker:
        Asynchrone execution of the query in an other thread. An optional callback method that take 2 arguments (job_id, query_result) can be set.
        This method return a job_id for this request that allow you to cancel it if needed
    """
    global __async_job_id, __async_jobs, __db_pool
    __async_job_id += 1
    t = __db_pool.apply_async(private_execute_async, args = (__async_job_id, query,), callback=private_execute_callback)
    __async_jobs[__async_job_id] = {"task" : t, "callback": callback, "query" : query, "start": datetime.datetime.now}
    return __async_job_id
        


async def execute_aio(query):
    """
        execute as coroutine
        Asynchrone execution of the query as coroutine
    """

    # Execute the query in another thread via coroutine
    loop = asyncio.get_event_loop()
    futur = loop.run_in_executor(None, private_execute_async, None, query)


    # Aio wait the end of the async task to return result
    result = await futur
    return result[1]


def cancel(async_job_id):
    """
        Cancel an asynch job running in the threads pool
    """
    if async_job_id in __async_jobs.keys():
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(__async_jobs.keys[async_job_id]["task"].cancel)
        log("Model async query (id:{}) canceled".format(async_job_id))
    else:
        log("Model unable to cancel async query (id:{}) because it doesn't exists".format(async_job_id))





# =====================================================================================================================
# MODEL DEFINITION - Build from the database (see sql scripts used to generate the database)
# =====================================================================================================================
User = Base.classes.user