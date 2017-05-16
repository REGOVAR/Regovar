#!env/python3
# coding: utf-8
import os
import datetime
import logging
import uuid
import time
import asyncio
import subprocess


from config import LOG_DIR, RANGE_DEFAULT





# =====================================================================================================================
# GENERIC TOOLS
# =====================================================================================================================
def run_until_complete(future):
    """
        Allow calling of an async method into a "normal" method (which is not a coroutine)
    """
    asyncio.get_event_loop().run_until_complete(future)


def run_async(future, *args):
    """
        Call a "normal" method into another thread 
        (don't block the caller method, but cannot retrieve result)
    """
    asyncio.get_event_loop().run_in_executor(None, future, *args)


def exec_cmd(cmd, asynch=False):
    """
        execute a system command and return the stdout result
    """
    if asynch:
        print("execute command async : {}".format(" ".join(cmd)))
        subprocess.Popen(cmd)
        return True, None, None

    out_tmp = '/tmp/regovar_exec_cmd_out'
    err_tmp = '/tmp/regovar_exec_cmd_err'
    print("execute command sync : {}".format(" ".join(cmd)))
    res = subprocess.call(cmd, stdout=open(out_tmp, "w"), stderr=open(err_tmp, "w"))
    out = open(out_tmp, "r").read()
    err = open(err_tmp, "r").read()
    return res, out, err






# =====================================================================================================================
# TOOLS
# =====================================================================================================================

def check_generic_query_parameter(allowed_fields, default_sort, fields, query, sort, offset, limit):
    """
        Generic method used by the core to check that generic fields/query/sort/offset/limit paramters à good
        fields : list of fields for lazy loading
        query  : dic with for each fields (keys) the list of value
        sort   : list of field on which to sort (prefix by "-" to sort field DESC)
        offset : start offset
        limit  : max number of result to return
    """
    # TODO check param and raise error if wrong parameter : E200001, E200002, E200003, E200004
    if fields is None:
        fields = allowed_fields
    if query is None:
        query = {}
    if sort is None:
        sort = default_sort
    if offset is None:
        offset = 0
    if limit is None:
        limit = RANGE_DEFAULT
    return fields, query, sort, offset, limit

    

def get_pipeline_forlder_name(name:str):
    """
        Todo : doc
    """
    cheked_name = ""
    for l in name:
        if l.isalnum() or l in [".", "-", "_"]:
            cheked_name += l
        if l == " ":
            cheked_name += "_"
    return cheked_name;




# def plugin_running_task(task_id):
#     """
#         Todo : doc
#     """
#     result = execute_plugin.AsyncResult(task_id)
#     return result.get()








def humansize(nbytes):
    """
        Todo : doc
    """
    suffixes = ['o', 'Ko', 'Mo', 'Go', 'To', 'Po']
    if nbytes == 0: return '0 o'
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


def md5(file_path):
    """
        Todo : doc
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()






# =====================================================================================================================
# LOGS MANAGEMENT
# =====================================================================================================================

regovar_logger = None 


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
    global regovar_logger
    regovar_logger.info(msg)


def war(msg):
    global regovar_logger
    regovar_logger.warning(msg)


def err(msg, exception=None):
    global regovar_logger
    regovar_logger.error(msg)
    if exception and not isinstance(exception, RegovarException):
        # To avoid to log multiple time the same exception when chaining try/catch
        regovar_logger.exception(exception)





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

# Create logger
setup_logger('regovar', os.path.join(LOG_DIR, "regovar.log"))
regovar_logger = logging.getLogger('regovar')
