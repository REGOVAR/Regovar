#!python
# coding: utf-8
import ipdb

import os
import sys
import argparse
import json

from argparse import RawTextHelpFormatter
from config import *





parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter, description="Available commands:"
    "\n  file\t\t- Manage file"
    "\n  pipeline\t- Manage pipelines"
    "\n  job\t\t- Manage job"
    "\n  config\t- Manage the server configuration", 
    usage="rego [subcommand] [options]", add_help=False)
parser.add_argument("subcommand",  type=str, nargs='*', default=[], help=argparse.SUPPRESS)
parser.add_argument("-h", "--help", help="show this help message and exit", action="store_true")
parser.add_argument("--version", help="show the client version", action="store_true")
parser.add_argument("-v", "--verbose", help="display all messages available", action="store_true")
parser.add_argument("-a", "--async", help="try to execute the command asynchronously (without blocking the shell)", action="store_true")



parser.add_argument("-f",  type=str, nargs='*', default=[], help=argparse.SUPPRESS)
parser.add_argument("-i",  type=str, nargs='*', default=[], help=argparse.SUPPRESS)
parser.add_argument("-c",  type=str, help=argparse.SUPPRESS)





# ===================================================================================================
# CONFIG Commands
# ===================================================================================================

# ===================================================================================================
# FILE Commands
# ===================================================================================================
parse_file_help_show = """regovar file  show <file_id>
      Display information about the requested file."""
parse_file_help_add = """regovar file add <local_file_path> 
      Get a local file and register it into regovar database. A copy of the file is done by regovar."""
parse_file_help_rem = """regovar file  rem <local_file_path>
      Delete a file from regovar."""

parse_file_help = """Manage regovar file

regovar file list
      Display the list of file installed on the server and their status.

""" + parse_file_help_show + "\n\n" + parse_file_help_add + "\n\n" + parse_file_help_rem






def parse_file(args, help=False, verbose=False, asynch=False):
    print ("manage file command [{}] h:{} v:{} a:{}".format(",".join(args), help, verbose, asynch))
    if len(args) == 0:
        print(parse_file_help)
    elif args[0] == "rem":
        print("Not implemented")
    elif args[0] == "add":
        if len(args) > 1:
            from core.core import core
            f = core.files.from_local(args[1], False)
            if f:
                print(json.dumps(f.to_json(), sort_keys=True, indent=4))
            else:
                print("Not able to register the file at the location {}".format(args[1]))
        else:
            print(parse_file_help_add)

    elif args[0] == "list":
        if len(args) > 1 :
            print("Warning : list take only one argument... all other have been ignored.")
        from core.core import core
        print("\n".join([json.dumps(f.to_json(), sort_keys=True, indent=4) for f in core.files.get()]))
    elif args[0] == "show":
        if len(args) > 1 and args[1].isdigit():
            from core.model import File
            f= File.from_id(int(args[1]), 1)
            if f:
                print(json.dumps(f.to_json(), sort_keys=True, indent=4))
            else:
                print("No file found with the id {}".format(args[1]))
        else:
            print(parse_file_help_show)
    else:
        print(parse_file_help)







# ===================================================================================================
# PIPELINE Commands
# ===================================================================================================


parse_pipeline_help_show = """regovar pipeline  show <pipe_id>
      Display information about the requested pipe."""
parse_pipeline_help_check = """regovar pipeline check <local_image_file>
      Check that the image of the pipeline is supported by regovar, and have all mandatory information for the installation."""
parse_pipeline_help_install = """regovar pipeline  install <local_image_file> [--async] [--verbose]
      Install the pipeline image on regovar."""
parse_pipeline_help_uninstall = """regovar pipeline uninstall <pipe_id> [--async] [--verbose]
      Uninstall the pipeline. To avoid ambiguity, the id of the pipe must be provided."""
parse_pipeline_help = """Manage regovar pipeline

regovar pipeline list
      Display the list of pipeline installed on the server and their status.

""" + parse_pipeline_help_show + "\n\n" + parse_pipeline_help_check + "\n\n" + parse_pipeline_help_install + "\n\n" + parse_pipeline_help_uninstall






def parse_pipeline(args, help=False, verbose=False, asynch=False):
    print ("manage pipeline command [{}] h:{} v:{} a:{}".format(",".join(args), help, verbose, asynch))
    if len(args) == 0:
        print(parse_pipeline_help)
    elif args[0] == "check":
        print("Not implemented")
    elif args[0] == "install":
        if len(args) > 1:
            from core.core import core
            p = core.pipelines.install_init_image_local(args[1], False, {"type" : "lxd"})
            core.pipelines.install(p.id, asynch=asynch)
        else:
            print(parse_pipeline_help_install)
    elif args[0] == "uninstall":
        if len(args) > 1:
            from core.model import Pipeline
            p = Pipeline.from_id(args[1])
            if p:
                from core.core import core
                p = core.pipelines.delete(p.id, asynch=asynch)
                if p:
                    print ("Pipeline {} (id={}) deleted".format(p.name, p.id))
            else:
                print("No pipeline found with the id {}".format(args[1]))
        else:
            print(parse_pipeline_help_uninstall)
    elif args[0] == "list":
        if len(args) > 1 :
            print("Warning : list take only one argument... all other have been ignored.")
        from core.core import core
        print("\n".join([json.dumps(p.to_json(), sort_keys=True, indent=4) for p in core.pipelines.get()]))
    elif args[0] == "show":
        if len(args) > 1 and args[1].isdigit():
            from core.model import Pipeline
            p = Pipeline.from_id(int(args[1]), 1)
            if p:
                print(json.dumps(p.to_json(), sort_keys=True, indent=4))
            else:
                print("No pipeline found with the id {}".format(args[1]))
        else:
            print(parse_pipeline_help_show)
    else:
        print(parse_pipeline_help)





# ===================================================================================================
# JOB Commands
# ===================================================================================================



parse_job_help_show = """regovar job  show <pipe_id>
      Display information about the requested job."""
parse_job_help_new = """regovar job new <job_name> <pipeline_id> [-c|--config <json_config_file>] [-i <inputs_ids> [...]] [-f <local_file> [...]] 
      Start a new job for the corresponding <pipeline_id> with the provided name. Inputs files can be provided with -i and or -f options."""


parse_job_help = """Manage regovar job

regovar job list [filters...] [--help]
      Display the list of job on the server. Some filter options can be provided to filter/sort  the list

regovar job  show <pipe_id>
      Display information about the requested job.

regovar job new <job_name> <pipeline_id> [-c|--config <json_config_file>] [-i <inputs_ids> [...]] [-f <local_file> [...]] 
      Start a new job for the corresponding <pipeline_id> with the provided name. Inputs files can be provided with -i and or -f options.

regovar job pause <job_id>
      Pause the jobn (if supported by the type of pipe's container manager).

regovar job start <job_id>
      Restart a job that have been paused.

regovar job stop <pipe_id>
      Force the job's execution to stop. Job is canceled, its container is deleted.

regovar job finalize <pipe_id>
      Force the finalization of the job. If the job execution is finished, but for some raisons, the container have not been deleted, 
      this action will properly clean the job's container stuff.

regovar job cd <pipe_id>
      Go to the job's directory.
      """




def parse_job(args, inputs_ids=[], files=[], form=None, help=False, verbose=False, asynch=False):
    print ("manage job command [{}] h:{} v:{} a:{}".format(",".join(args), help, verbose, asynch))
    if len(args) == 0:
        print(parse_pipeline_help)
    elif args[0] == "list":
        if len(args) > 1 :
            print("Warning : list take only one argument... all other have been ignored.")
        from core.core import core
        print("\n".join([json.dumps(j.to_json(), sort_keys=True, indent=4) for j in core.jobs.get()]))
    elif args[0] == "show":
        if len(args) > 1 and args[1].isdigit():
            from core.core import core
            j = core.jobs.monitoring(int(args[1]))
            if j:
                print(json.dumps(j.to_json(), sort_keys=True, indent=4))
            else:
                print("No job found with the id {}".format(args[1]))
        else:
            print(parse_job_help_show)
    elif args[0] == "new":
        if len(args) > 3:
            print("Warning : list take only one argument... all other have been ignored.")
        if len(args) < 3:
            print(parse_pipeline_help_new)
        config = {}
        if form and os.path.exists(form):
            with open(form, "r") as f:
                j = f.read()
                try:
                    j = json.loads(j)
                except Exception as ex:
                    print ("Error with config. Wrong file/json.")
                    print(j)
                    raise ex
                config = j
        config.update({"name" : args[1]})
        from core.core import core
        j = core.jobs.new(int(args[2]), config, inputs_ids, asynch)
        print(json.dumps(j.to_json(), sort_keys=True, indent=4))
    elif args[0] == "pause":
        from core.core import core
        if core.jobs.pause(args[1], asynch=False):
            print("job paused.")
        else:
            print("not able to pause the job.")
    elif args[0] == "start":
        from core.core import core
        if core.jobs.start(args[1], asynch=False):
            print("job restarted.")
        else:
            print("not able to restart the job.")
    elif args[0] == "stop":
        from core.core import core
        if core.jobs.stop(args[1], asynch=False):
            print("job stoped.")
        else:
            print("not able to stop the job.")
    elif args[0] == "finalize":
        from core.core import core
        if core.jobs.finalize(args[1], asynch=False):
            print("job finalized.")
        else:
            print("not able to finalized the job.")
    elif args[0] == "cd":
        from core.model import Job
        j = Job.from_id(args[1])
        if j:
            print ("cd " + j.root_path)
        else:
            print ("No job found with the id : {}".format(args[1]))
    elif args[0] == "list":
        if len(args) > 1 :
            print("Warning : list take only one argument... all other have been ignored.")
        from core.core import core
        print("\n".join([json.dumps(p.to_json(), sort_keys=True, indent=4) for p in core.pipelines.get()]))
    else:
        print(parse_pipeline_help)

















args = parser.parse_args()

if args.version:
    print ("regovar server : {}".format(VERSION))


if len(args.subcommand) > 0:
    if args.subcommand[0] == "pipeline":
        parse_pipeline(args.subcommand[1:], args.help, args.verbose, args.async)
    elif args.subcommand[0] == "job":
        parse_job(args.subcommand[1:], args.i, args.f, args.c, args.help, args.verbose, args.async)
    elif args.subcommand[0] == "file":
        parse_file(args.subcommand[1:], args.help, args.verbose, args.async)
    elif args.subcommand[0] == "version":
        print ("regovar server : {}".format(VERSION))
    elif args.subcommand[0] == "config":
        print ("Server :\n  Version \t{}\n  Hostname \t{}\n  Hostname pub \t{}\n".format(VERSION, HOSTNAME, HOST_P))
        print ("Database :\n  Host \t\t{}\n  Port \t\t{}\n  User \t\t{} (pwd: \"{}\")\n  Name \t\t{}\n  Pool \t\t{}\n".format(DATABASE_HOST, DATABASE_PORT, DATABASE_USER, DATABASE_PWD, DATABASE_NAME, DATABASE_POOL_SIZE))
        print ("File system :\n  Files \t{}\n  Temp \t\t{}\n  Databases \t{}\n  Pipelines \t{}\n  Jobs \t\t{}\n  Logs \t\t{}".format(FILES_DIR, TEMP_DIR, DATABASES_DIR ,PIPELINES_DIR, JOBS_DIR, LOG_DIR))
    else:
        parser.print_help()
else:
    parser.print_help()










