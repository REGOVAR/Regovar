#!env/python3
# coding: utf-8

import aiohttp_jinja2
import jinja2
import base64

from aiohttp import web
from aiohttp_session import setup as setup_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttp_security import setup as setup_security
from aiohttp_security import SessionIdentityPolicy

from config import *
from web.policy import RegovarAuthorizationPolicy
from web.handlers import *


# Handlers instances
apiHandler = ApiHandler()
userHandler = UserHandler()

# Create a auth ticket mechanism that expires after SESSION_MAX_DURATION seconds (default is 86400s = 24h), and has a randomly generated secret. 
# Also includes the optional inclusion of the users IP address in the hash
key = base64.b64encode(PRIVATE_KEY32.encode()).decode()


# Create server app
app = web.Application()
setup_session(app, EncryptedCookieStorage(key, cookie_name='regovar_session', max_age=SESSION_MAX_DURATION))
setup_security(app, SessionIdentityPolicy(), RegovarAuthorizationPolicy())
app['websockets'] = []
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(TEMPLATE_DIR)) 

# On shutdown, close all websockets
app.on_shutdown.append(on_shutdown)






# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# ROUTES
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
app.router.add_route('GET',    "/", apiHandler.welcom)                                                            # Get "welcom page of the rest API"

app.router.add_route('GET',    "/users", userHandler.all)                                                         # Get list of all users (allow search parameters)
app.router.add_route('POST',   "/users", userHandler.add)                                                         # Create new users with provided data
app.router.add_route('GET',    "/users/{user_id}", userHandler.get)                                               # Get details about one user
app.router.add_route('PUT',    "/users/{user_id}", userHandler.edit)                                              # Edit user with provided data
app.router.add_route('POST',   "/users/login", userHandler.login)                                                 # Start user's session if provided credentials are correct
app.router.add_route('GET',    "/users/logout", userHandler.logout)                                               # Kill user's session







