#!env/python3
# coding: utf-8
import os
import datetime
import logging
import uuid
import time
import asyncio

from config import LOG_DIR


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


def err(msg, exception=None):
    global rlog
    rlog.error(msg)
    if exception and not isinstance(exception, RegovarException):
        # To avoid to log multiple time the same exception when chaining try/catch
        rlog.exception(exception)






# =====================================================================================================================
# ERROR MANAGEMENT
# =====================================================================================================================


class RegovarException(Exception):
    """
        Regovar exception
    """
    msg = "Unknow error :/"
    code = "E000000"

    def __init__(self, msg: str, code: str=None, exception: Exception=None, logger: logging.Logger=None):
        self.code = code or RegovarException.code
        self.msg = msg or RegovarException.msg
        self.id = str(uuid.uuid4())
        self.date = datetime.datetime.utcnow().timestamp()
        self.log = "ERROR {} [{}] {}".format(self.code, self.id, self.msg)

        if logger:
            logger.error(self.log)
            if exception and not isinstance(exception, RegovarException):
                # To avoid to log multiple time the same exception when chaining try/catch
                logger.exception(exception)
        else:
            err(self.log, exception)


    def __str__(self):
        return self.log


def log_snippet(longmsg, exception: RegovarException=None):
    """
        Log the provided msg into a new log file and return the generated log file
        To use when you want to log a long text (like a long generated sql query by example) to 
        avoid to poluate the main log with too much code.
    """
    uid = exception.id if exception else str(uuid.uuid4())
    filename = os.path.join(LOG_DIR,"snippet_{}.log".format(uid))
    with open(filename, 'w+') as f:
        f.write(longmsg)
    return filename


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
setup_logger('regovar', os.path.join(LOG_DIR, "regovar.log"))
rlog = logging.getLogger('regovar')