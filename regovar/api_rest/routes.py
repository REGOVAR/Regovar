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
from api_rest.policy import RegovarAuthorizationPolicy
from api_rest.rest import *
from api_rest.handlers import *


# Handlers instances
apiHandler = ApiHandler()
userHandler = UserHandler()
projHandler = ProjectHandler()
subjectHandler = SubjectHandler()
eventHandler = EventHandler()
websocket = WebsocketHandler()

fileHdl = FileHandler()
jobHdl = JobHandler()
pipeHdl = PipelineHandler()
dbHdl = DatabaseHandler()

annotationHandler = AnnotationDBHandler()
analysisHandler = AnalysisHandler()
sampleHandler = SampleHandler()
variantHandler = VariantHandler()
searchHandler = SearchHandler()
adminHandler = AdminHandler()


# Create a auth ticket mechanism that expires after SESSION_MAX_DURATION seconds (default is 86400s = 24h), and has a randomly generated secret. 
# Also includes the optional inclusion of the users IP address in the hash
key = base64.b64encode(PRIVATE_KEY32.encode()).decode()


# Create server app
app = web.Application()
setup_session(app, EncryptedCookieStorage(key, max_age=SESSION_MAX_DURATION))
setup_security(app, SessionIdentityPolicy(session_key='regovar_session_token'), RegovarAuthorizationPolicy())
app['websockets'] = []
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(TEMPLATE_DIR)) 

# On shutdown, close all websockets
app.on_shutdown.append(on_shutdown)






# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# ROUTES
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
app.router.add_route('GET',    "/",       apiHandler.welcom)                                                     # Get "welcom page of the rest API"
app.router.add_route('GET',    "/config", apiHandler.config)                                                     # Get config of the server
app.router.add_route('GET',    "/api",    apiHandler.api)                                                        # Get html test api page
app.router.add_route('GET',    "/ws",     websocket.get)                                                         # Websocket url to use with ws or wss protocol


app.router.add_route('GET',    "/user", userHandler.list)                                                        # Get list of all users (allow search parameters)
app.router.add_route('POST',   "/user", userHandler.new)                                                         # Create new users with provided data
app.router.add_route('GET',    "/user/{user_id}", userHandler.get)                                               # Get details about one user
app.router.add_route('PUT',    "/user/{user_id}", userHandler.edit)                                              # Edit user with provided data
app.router.add_route('POST',   "/user/login", userHandler.login)                                                 # Start user's session if provided credentials are correct
app.router.add_route('GET',    "/user/logout", userHandler.logout)                                               # Kill user's session
app.router.add_route('DELETE', "/user/{user_id}", userHandler.delete)                                            # Delete a user

app.router.add_route('GET',    "/project/browserTree",           projHandler.tree)                               # Get projects as tree (allow search parameters)
app.router.add_route('GET',    "/project",                       projHandler.list)                               # Get list of all projects (allow search parameters)
app.router.add_route('POST',   "/project",                       projHandler.create_or_update)                   # Create new project with provided data
app.router.add_route('GET',    "/project/{project_id}",          projHandler.get)                                # Get details about the project
app.router.add_route('PUT',    "/project/{project_id}",          projHandler.create_or_update)                   # Edit project meta data
app.router.add_route('DELETE', "/project/{project_id}",          projHandler.delete)                             # Delete the project
app.router.add_route('GET',    "/project/{project_id}/events",   projHandler.events)                             # Get list of events of the project (allow search parameters)
app.router.add_route('GET',    "/project/{project_id}/subjects", projHandler.subjects)                           # Get list of subjects of the project (allow search parameters)
app.router.add_route('GET',    "/project/{project_id}/analyses", projHandler.analyses)                           # Get list of analyses (pipeline and filtering) of the project (allow search parameters)
app.router.add_route('GET',    "/project/{project_id}/files",    projHandler.files)                              # Get list of files (samples and attachments) of the project (allow search parameters)

app.router.add_route('POST',   "/event",            eventHandler.new)                                            # Create a new event
app.router.add_route('GET',    "/event/{event_id}", eventHandler.get)                                            # Get details about an event
app.router.add_route('PUT',    "/event/{event_id}", eventHandler.edit)                                           # Edit event's data
app.router.add_route('DELETE', "/event/{event_id}", eventHandler.delete)                                         # Delete an event

app.router.add_route('GET',    "/subject",                       subjectHandler.list)                            # Get subjects as list (allow search parameters)
app.router.add_route('POST',   "/subject",                       subjectHandler.create_or_update)                # Create subjects
app.router.add_route('GET',    "/subject/{subject_id}",          subjectHandler.get)                             # Get details about a subject
app.router.add_route('PUT',    "/subject/{subject_id}",          subjectHandler.create_or_update)                # Edit subject's data
app.router.add_route('DELETE', "/subject/{subject_id}",          subjectHandler.delete)                          # Delete a subject
app.router.add_route('GET',    "/project/{project_id}/events",   subjectHandler.events)                          # Get list of events of the project (allow search parameters)
app.router.add_route('GET',    "/project/{project_id}/samples",  subjectHandler.samples)                         # Get list of subjects of the subject (allow search parameters)
app.router.add_route('GET',    "/project/{project_id}/analyses", subjectHandler.samples)                         # Get list of analyses (pipeline and filtering) of the subject (allow search parameters)
app.router.add_route('GET',    "/project/{project_id}/files",    subjectHandler.files)                           # Get list of files of the subject (allow search parameters)

app.router.add_route('GET',    "/file",                  fileHdl.list)                                           # Get list of all file (allow search parameters)
app.router.add_route('GET',    "/file/{file_id}",        fileHdl.get)                                            # Get details about a file
app.router.add_route('PUT',    "/file/{file_id}",        fileHdl.edit)                                           # Edit file's details
app.router.add_route('DELETE', "/file/{file_id}",        fileHdl.delete)                                         # Delete the file
app.router.add_route('POST',   "/file/upload",           fileHdl.tus_upload_init)
app.router.add_route('OPTIONS',"/file/upload",           fileHdl.tus_config)
app.router.add_route('HEAD',   "/file/upload/{file_id}", fileHdl.tus_upload_resume)
app.router.add_route('PATCH',  "/file/upload/{file_id}", fileHdl.tus_upload_chunk)
app.router.add_route('DELETE', "/file/upload/{file_id}", fileHdl.tus_upload_delete)

app.router.add_route('GET',    "/pipeline",                                    pipeHdl.list)
app.router.add_route('GET',    "/pipeline/{pipe_id}",                          pipeHdl.get)
app.router.add_route('DELETE', "/pipeline/{pipe_id}",                          pipeHdl.delete)
app.router.add_route('GET',    "/pipeline/install/{file_id}/{container_type}", pipeHdl.install)
app.router.add_route('POST',   "/pipeline/install",                            pipeHdl.install_json)

app.router.add_route('GET',    "/job",                     jobHdl.list)
app.router.add_route('POST',   "/job",                     jobHdl.new)
app.router.add_route('GET',    "/job/{job_id}",            jobHdl.get)
app.router.add_route('GET',    "/job/{job_id}/pause",      jobHdl.pause)
app.router.add_route('GET',    "/job/{job_id}/start",      jobHdl.start)
app.router.add_route('GET',    "/job/{job_id}/cancel",     jobHdl.cancel)
app.router.add_route('GET',    "/job/{job_id}/monitoring", jobHdl.monitoring)
app.router.add_route('GET',    "/job/{job_id}/finalize",   jobHdl.finalize)

app.router.add_route('GET',    "/db",     dbHdl.get)
app.router.add_route('GET',    "/db/{ref}", dbHdl.get)




app.router.add_route('GET',    "/annotation", annotationHandler.list)                                                # Get list of genom's referencials supported
app.router.add_route('GET',    "/annotation/{ref_id}", annotationHandler.get)                                        # Get list of all annotation's databases and for each the list of availables versions and the list of their fields for the latest version
app.router.add_route('GET',    "/annotation/db/{db_id}", annotationHandler.get_database)                             # Get the database details and the list of all its fields
app.router.add_route('GET',    "/annotation/field/{field_id}", annotationHandler.get_field)                          # Get the database details and the list of all its fields
app.router.add_route('DELETE', "/annotation/db/{db_id}", annotationHandler.delete)                                   # Delete an annotation database with all its fields.

app.router.add_route('GET',    "/variant/{ref_id}/{variant_id}", variantHandler.get)                                 # Get all available information about the given variant
app.router.add_route('GET',    "/variant/{ref_id}/{variant_id}/{analysis_id}", variantHandler.get)                   # Get all available information about the given variant + data in the context of the analysis
app.router.add_route('POST',   "/variant", variantHandler.new)                                                       # Import all variant and their annotations provided as json in the POST body into the annso database

app.router.add_route('GET',    "/sample/browse/{ref_id}", sampleHandler.tree)                                        # Get sampleslist for the requested reference
app.router.add_route('GET',    "/sample", sampleHandler.list)                                                        # Get list of all samples in database
#app.router.add_route('GET',    "/sample/{ref_id}", sampleHandler.list)                                              # Get list of all samples in database for the provided genome reference
app.router.add_route('GET',    "/sample/{sample_id}", sampleHandler.get)                                             # Get specific sample's database
app.router.add_route('GET',    "/sample/import/{file_id}/{ref_id}", sampleHandler.import_from_file)                  # import sample's data from the file (vcf supported)
app.router.add_route('PUT',    "/sample/{sample_id}", sampleHandler.update)                                          # Update sample informations

app.router.add_route('GET',    "/analysis",                                  analysisHandler.list)                   # List analyses
app.router.add_route('POST',   "/analysis",                                  analysisHandler.new)                    # Create new analysis
app.router.add_route('GET',    "/analysis/{analysis_id}",                    analysisHandler.get)                    # Get analysis metadata
app.router.add_route('PUT',    "/analysis/{analysis_id}",                    analysisHandler.update)                 # Save analysis metadata
#app.router.add_route('POST',   "/analysis/{analysis_id}/load/{file_id}",     analysisHandler.load_file)              # TODO : Load a file (vcf and ped supported) to setup the analysis data (variant/annotations/samples)
app.router.add_route('GET',    "/analysis/{analysis_id}/filter",             analysisHandler.get_filters)            # Get list of available filter for the provided analysis
app.router.add_route('POST',   "/analysis/{analysis_id}/filter",             analysisHandler.create_update_filter)   # Create a new filter for the analisis
app.router.add_route('PUT',    "/analysis/{analysis_id}/filter/{filter_id}", analysisHandler.create_update_filter)   # Update filter
app.router.add_route('DELETE', "/analysis/{analysis_id}/filter/{filter_id}", analysisHandler.delete_filter)          # Delete a filter
app.router.add_route('POST',   "/analysis/{analysis_id}/filtering",          analysisHandler.filtering)              # Get result (variants) of the provided filter
app.router.add_route('POST',   "/analysis/{analysis_id}/filtering/{variant_id}", analysisHandler.filtering)          # Get total count of result of the provided filter

app.router.add_route('GET',    "/analysis/{analysis_id}/selection",          analysisHandler.get_selection)          # Get variants data for the provided selection
# CRUD selection
app.router.add_route('GET',    "/analysis/{analysis_id}/clear_temps_data",   analysisHandler.clear_temps_data)       # Clear temporary data (to save disk space by example)

app.router.add_route('POST',   "/analysis/{analysis_id}/selection/{selection_id}/export/{pipe_id}",   analysisHandler.get_export)             # Export selection of the provided analysis into the requested format
app.router.add_route('POST',   "/analysis/{analysis_id}/report/{pipe_id}",   analysisHandler.get_report)             # Generate report html for the provided analysis+report id

app.router.add_route('GET',    "/search/{query}",                            searchHandler.get)                      # generic research


app.router.add_route('GET',    "/admin/stats",                               adminHandler.stats)                   # generic research














# Websockets / realtime notification
app.router.add_route('POST',   "/job/{job_id}/notify", jobHdl.update_status)


# Statics root for direct download
# FIXME - Routes that should be manages directly by NginX
app.router.add_static('/error', TEMPLATE_DIR + "/errors/")
app.router.add_static('/assets', TEMPLATE_DIR)
app.router.add_static('/dl/db/', DATABASES_DIR)
app.router.add_static('/dl/pipe/', PIPELINES_DIR)
app.router.add_static('/dl/file/', FILES_DIR)
app.router.add_static('/dl/job/', JOBS_DIR)


