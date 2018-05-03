#!env/python3
# coding: utf-8
import ipdb
import os
import hashlib
import datetime
import logging
import traceback
import uuid
import time
import asyncio
import subprocess
import re
import json
import requests
import concurrent.futures


from config import LOG_DIR, CACHE_DIR, CACHE_EXPIRATION_SECONDS, DEBUG


main_loop = asyncio.get_event_loop()


if DEBUG:
    main_loop.set_debug(enabled=True)


#
# As Pirus is a subproject of Regovar, thanks to keep framework complient
# TODO : find a way to manage it properly with github (subproject ?)
#


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]



# =====================================================================================================================
# GENERIC TOOLS
# =====================================================================================================================
def run_until_complete(future):
    """
        Allow calling of an async method into a "normal" method (which is not a coroutine)
    """
    #main_loop.run_until_complete(future)
    asyncio.run_coroutine_threadsafe(future, main_loop)


def run_async(future, *args):
    """
        Call a "normal" method into another thread 
        (don't block the caller method, but cannot retrieve result)
    """
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Execute the query in another thread via coroutine
            main_loop.run_in_executor(None, future, *args)
    except Exception as ex:
        err("Asynch method failed.", ex) 



def exec_cmd(cmd, asynch=False):
    """
        execute a system command and return the stdout result
    """
    if asynch:
        print("execute command async : {}".format(" ".join(cmd)))
        subprocess.Popen(cmd, stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
        return True, None, None

    out_tmp = '/tmp/regovar_exec_cmd_out'
    err_tmp = '/tmp/regovar_exec_cmd_err'
    print("execute command sync : {}".format(" ".join(cmd)))
    res = subprocess.call(cmd, stdout=open(out_tmp, "w"), stderr=open(err_tmp, "w"))
    out = open(out_tmp, "r").read()
    err = open(err_tmp, "r").read()
    return res, out, err








# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# TOOLS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

    

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



def clean_filename(filename):
    # TODO : clean filename by removing special characters, trimming white spaces, and replacing white space by _
    rx = re.compile('\W+')
    res = rx.sub('.', filename).strip('.')
    return res








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




def check_date(value, default=None):
    """
        Secure method to get datetime from unknow value
    """
    if isinstance(value, datetime.datetime): 
        return value
    elif isinstance(value, str):
        try:
            return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f") if len(value) > 10 else datetime.datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return default
    return default


def check_int(value, default=None):
    """
        Secure method to get int from unknow value
    """
    if isinstance(value, int):
        return value
    else:
        try:
            return int(value)
        except ValueError:
            return default
    return default


def check_float(value, default=None):
    """
        Secure method to get float from unknow value
    """
    if isinstance(value, float):
        return value
    else:
        try:
            return float(value)
        except ValueError:
            return default
    return default


def check_bool(value, default=None):
    """
        Secure method to get bool from unknow value
    """
    if isinstance(value, bool):
        return value
    else:
        try:
            return bool(value)
        except ValueError:
            return default
    return default


def check_string(value, default=None):
    """
        Secure method to get string from unknow value
    """
    if isinstance(value, str):
        return value
    else:
        try:
            return str(value)
        except ValueError:
            return default
    return default


def remove_duplicates(source):
    """
        Remove duplicates in the provided list (keeping elements order)
    """
    if isinstance(source, list):
        result = []
        for i in source:
            if i not in result:
                result.append(i)
        return result
    return source




# =====================================================================================================================
# CACHE TOOLS
# =====================================================================================================================
def get_cached_url(url, prefix="", headers={}):
    """
        Return cache response if exists, otherwise, execute request and store result in cache before return.
    """
    # encrypt url to md5 to avoid problem with special characters
    uri = prefix + hashlib.md5(url.encode('utf-8')).hexdigest()
    result = get_cache(uri)

    if result is None:
        res = requests.get(url, headers=headers)
        if res.ok:
            try:
                result = json.loads(res.content.decode())
                set_cache(uri, result)
            except Exception as ex:
                raise RegovarException("Unable to cache result of the query: " + url, ex)
    return result










def get_cache(uri):
    """
        Return the cached json corresponding to the uri if exists; None otherwise
    """
    cache_file = CACHE_DIR + "/" + uri
    if os.path.exists(cache_file):
        s=os.stat(cache_file)
        date = datetime.datetime.utcfromtimestamp(s.st_ctime)
        ellapsed = datetime.datetime.now() - date
        if ellapsed.total_seconds() < CACHE_EXPIRATION_SECONDS:
            # Return result as json
            with open(cache_file, 'r') as f:
                return json.loads(f.read())
        else:
            # Too old, remove cache entry
            os.remove(cache_file)
    return None


def set_cache(uri, data):
    """
        Put the data in the cache
    """
    if not uri or not data: return
    cache_file = CACHE_DIR + "/" + uri
    with open(cache_file, 'w') as f:
        f.write(json.dumps(data))
        f.close()
    




# =====================================================================================================================
# DATA MODEL TOOLS
# =====================================================================================================================
CHR_DB_MAP = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10", 11: "11", 12: "12", 13: "13", 14: "14", 15: "15", 16: "16", 17: "17", 18: "18", 19: "19", 20: "20", 21: "21", 22: "22", 23: "X", 24: "Y", 25: "M"}
CHR_DB_RMAP = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "11": 11, "12": 12, "13": 13, "14": 14, "15": 15, "16": 16, "17": 17, "18": 18, "19": 19, "20": 20, "21": 21, "22": 22, "23": 23, "24": 24, "25": 25, "X": 23, "Y": 24, "M": 25}


def chr_from_db(chr_value):
    if chr_value in CHR_DB_MAP.keys():
        return CHR_DB_MAP[chr_value]
    return None


def chr_to_db(chr_value):
    if chr_value in CHR_DB_RMAP.keys():
        return CHR_DB_RMAP[chr_value]
    return None



    



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
    msgs = msg.split('\n')
    finals = []
    for m in msgs:
        finals.append(m[0:200])
        m = m[200:]
        while(len(m)>0):
            finals.append("\t" + m[0:200])
            m = m[200:]
    for m in finals:
        regovar_logger.info(m)


def war(msg):
    global regovar_logger
    regovar_logger.warning(msg)


def err(msg, exception=None):
    global regovar_logger
    log_file = log_snippet(msg, exception)
    regovar_logger.error("[{}] ".format(log_file) + msg)
    return log_file
    


def log_snippet(longmsg, exception:BaseException=None):
    """
        Log the provided msg into a new log file and return the generated log file
        To use when you want to log a long text (like a long generated sql query by example) to 
        avoid to poluate the main log with too much code.
    """
    uid = str(uuid.uuid4())
    filename = os.path.join(LOG_DIR, "Error_{}.log".format(uid))
    with open(filename, 'w+') as f:
        if exception:
            # Retrieve stack trace of the exception
            e_traceback = traceback.format_exception(exception.__class__, exception, exception.__traceback__)
            for line in e_traceback:
                f.write(line)
            f.write("\n=============================\n")
        f.write(longmsg)
    return "Error_{}.log".format(uid)




# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# ERROR MANAGEMENT
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 




class RegovarException(Exception):
    """
        Regovar exception
    """
    msg = "Unknow error :("
    code = "E000000"

    def __init__(self, msg: str=None, code: str=None, args=[], exception: Exception=None, logger: logging.Logger=None):
        self.code = code or RegovarException.code
        
        # If code set, we can retrieve default error message from error_list, else get message or unknow message
        if code and not msg: 
            from core.framework.errors_list import ERR
            self.msg = eval("ERR.{}".format(code))
            self.msg = self.msg.format(*args)
        else:
            self.msg = msg or RegovarException.msg
        self.date = datetime.datetime.utcnow().timestamp()
        self.log = "ERROR {} - {}".format(self.code, self.msg)


    def __str__(self):
        return self.log












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
            log("{} ms".format(self.msecs))

    def __str__(self):
        if self.msecs >= 1000:
            return "{} s".format(self.secs)
        return "{} ms".format(self.msecs)

    def total_ms(self):
        return self.msecs

    def total_s(self):
        return self.secs










# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# INIT OBJECTS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# Create logger
setup_logger('regovar', os.path.join(LOG_DIR, "regovar.log"), logging.DEBUG if DEBUG else logging.INFO)
regovar_logger = logging.getLogger('regovar')
