#!env/python3
# coding: utf-8
import os
import datetime
import logging
import uuid
import time
import asyncio

from config import REGOVAR_DIR


# =====================================================================================================================
# TOOLS
# =====================================================================================================================
asyncio_main_loop = asyncio.get_event_loop()
def run_until_complete(future):
    asyncio_main_loop.run_until_complete(future)



def array_diff(array1, array2):
    """
        Return the list of element in array2 that are not in array1
    """
    return [f for f in array2 if f not in array1]


def array_merge(array1, array2):
    """
        Merge the two arrays in one (by removing duplicates)
    """
    result = []
    for f in array1:
        if f not in result:
            result.append(f)
    for f in array2:
        if f not in result:
            result.append(f)
    return result





# =====================================================================================================================
# LOGS MANAGEMENT
# =====================================================================================================================


def setup_logger(logger_name, log_file, level=logging.INFO):
    """
        Todo : doc
    """
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s | %(message)s')
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)


def log(msg):
    global rlog
    rlog.info(msg)


def war(msg):
    global rlog
    rlog.warning(msg)


def err(msg):
    global rlog
    rlog.error(msg)


# =====================================================================================================================
# ERROR MANAGEMENT
# =====================================================================================================================


class RegovarException(Exception):
    """
        Todo : doc
    """
    msg = "Unknow error :/"
    code = 0
    id = None
    date = None

    def __init__(self, msg: str, code: int=0, logger=None):
        self.code = RegovarException.code
        self.msg = RegovarException.msg
        self.id = str(uuid.uuid4())
        self.date = datetime.datetime.utcnow().timestamp()

        if logger is not None:
            logger.err(msg)

    def __str__(self):
        return "[ERROR:{:05}] {} : {}".format(self.code, self.id, self.msg)


# =====================================================================================================================
# TIMER
# =====================================================================================================================


class Timer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs
        if self.verbose:
            log(self.msecs, ' ms')

    def __str__(self):
        if self.msecs >= 1000:
            return "{0} s".format(self.secs)
        return "{0} ms".format(self.msecs)

    def total_ms(self):
        return self.msecs

    def total_s(self):
        return self.secs


# =====================================================================================================================
# INIT OBJECTS
# =====================================================================================================================

# Create regovar logger : rlog
setup_logger('regovar', os.path.join(REGOVAR_DIR, "regovar.log"))
rlog = logging.getLogger('regovar')