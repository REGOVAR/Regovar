#!env/python3
# coding: utf-8

import aiohttp_jinja2
import jinja2
from aiohttp import web

from config import *
from web.handlers import *


app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(TEMPLATE_DIR))	

# Handlers instances
apiHandler = ApiHandler()
userHandler = UserHandler()

# Config server app
app['websockets'] = []

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
app.router.add_route('POST',   "/users/{user_id}/login", userHandler.login)                                       # Start user's session if provided credentials are correct
app.router.add_route('GET',    "/users/{user_id}/logout", userHandler.logout)                                     # Kill user's session







