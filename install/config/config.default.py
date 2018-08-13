#!env/python3
# coding: utf-8 
import os


DEBUG = True


# HOST (internal)
HOST = "0.0.0.0"
PORT = 8500
HOSTNAME = "{}:{}".format(HOST, PORT)  # This is the internal host on which aioHTTP will run the service.
# HOST (public)
HOST_P = "127.0.0.1:8500"  # This url shall be set with the public namespace used




# SECURITY
PRIVATE_KEY32 = "" # 32bits server secret key
SESSION_MAX_DURATION = 86400
OMIM_API_KEY = "" # To be set with your key. (get it for free here : https://omim.org/api )


# DB
DATABASE_HOST = "regovar_pg"
DATABASE_PORT = 5432
DATABASE_USER = "regovar"
DATABASE_PWD = "regovar"
DATABASE_NAME = "regovar"
DATABASE_POOL_SIZE = 7
VCF_IMPORT_MAX_THREAD = 7


# FILESYSTEM
FILES_DIR = "/var/regovar/files"
TEMP_DIR = "/var/regovar/downloads"
CACHE_DIR = "/var/regovar/cache"
DATABASES_DIR = "/var/regovar/databases"
PIPELINES_DIR = "/var/regovar/pipelines"
JOBS_DIR = "/var/regovar/jobs"

CACHE_EXPIRATION_SECONDS = 2592000 # 30 days = 60*60*24*30



# AUTOCOMPUTED VALUES
REGOVAR_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = REGOVAR_DIR
TEMPLATE_DIR = os.path.join(REGOVAR_DIR, "api_rest/templates/")
ERROR_ROOT_URL = "{}/errorcode/".format(HOST_P)
NOTIFY_URL = "http://" + HOST_P + "/job/{}/notify"



# REST API
RANGE_DEFAULT = 1000
RANGE_MAX = 10000



# GENERIC CONTAINER CONFIG
MAX_JOB_RUNNING = 5


# DOCKER TECHNOLOGY CONFIG
DOCKER_CONFIG = {
    "network": "regovar_net",
    "job_name" : "regovar_job_{}",
    "image_name" : "regovar_pipe_{}"
}


