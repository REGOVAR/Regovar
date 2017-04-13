#!python
# coding: utf-8

import os



# Annso package
from config import *
from core.framework import RegovarException

# Some check before starting the web application
if not os.path.exists(TEMPLATE_DIR):
    raise RegovarException("ERROR : Templates directory doesn't exists : " + TEMPLATE_DIR)
if not os.path.exists(CACHE_DIR):
    raise RegovarException("ERROR : Cache directory doesn't exists : " + CACHE_DIR)
if not os.path.exists(TEMP_DIR):
    raise RegovarException("ERROR : Temp directory for file upload doesn't exists : " + TEMP_DIR)
if not os.path.exists(FILES_DIR):
    raise RegovarException("ERROR : File directory doesn't exists : " + FILES_DIR)

# Load rest of pirus application shall be done after celery init
from aiohttp import web
from web import *



# Start the pirus server
if __name__ == '__main__':
    web.run_app(app, host=HOST, port=PORT)