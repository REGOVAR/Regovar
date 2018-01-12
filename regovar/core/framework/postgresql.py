#!env/python3
# coding: utf-8
import os
import datetime
import asyncio
import sqlalchemy
#import multiprocessing as mp

import concurrent.futures

from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.orm import sessionmaker, scoped_session

from core.framework.common import *
import config as C




# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# DATABASE CONNECTION
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

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
    raise RegovarException(code="E000002", exception=ex)





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
            except IntegrityError as ex:
                session.rollback()
                instance = query.one()
                return instance, False
    except Exception as ex:
        raise ex


def check_session(obj):
    s = Session.object_session(obj)
    if not s :
        Session().add(obj)


def generic_save(obj):
    """
        generic method to save SQLalchemy object into database
    """
    try:
        s = Session.object_session(obj)
        if not s :
            s = Session()
            s.add(obj)
        obj.update_date = datetime.datetime.now()
        s.commit()
    except Exception as ex:
        if s: s.rollback()
        raise RegovarException(code="E100002", arg=[str(obj)], exception=ex)


def generic_count(obj):
    """
        generic method to count how many object in the table
    """
    try:
        return Session().query(obj).count()
    except Exception as ex:
        Session().rollback()
        raise RegovarException(msg="Unable to count how many object in the table", exception=ex)
    



def execute(query, loop=True):
    """
        Synchrone execution of the query in the shared session. If error occured, raise RegovarException
    """
    result = None
    s = Session()
    if C.DEBUG and loop: print("Execute query :\nSESSION: {}\nQUERY: {}".format(s, query[0:1000]+"..."))
    try:
        result = s.execute(query)
        s.commit() 
    except sqlalchemy.exc.InternalError:
        # May occure if previous request failled and session is in prepared state
        if loop:
            print ("LOOPING > Rollback session and Try to execute again the query")
            s.rollback()
            execute(query, False)
    except Exception as ex:
        print ("EXCEPTION SQL !!!!")
        s.rollback()
        r = RegovarException(code="E100001", exception=ex)
        log_snippet(query, r)
        raise r
    
    return result




async def execute_aio(query):
    """
        execute as coroutine
        Asynchrone execution of the query as coroutine
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Execute the query in another thread via coroutine
        loop = asyncio.get_event_loop()
        futur = loop.run_in_executor(executor, execute, query)

        # Aio wait the end of the async task to return result
        result = await futur
    return result





def sql_escape(value):
    if type(value) is str:
        value = value.replace("'", "''")
    return value
