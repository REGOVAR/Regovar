#!env/python3
# coding: utf-8


class ERR():
    # SETUP / CONFIG
    E000001 = "Unable to connect to the database with settings provided by configuration file."
    E000002 = "Error occured when initializing the database."
    E000003 = "Error when requesting the database. SQL error occured in the custom query (query logged in the error's snippet log file : {})."
    E000004 = "Unable to save resource {} into database."

    # DATABASE / MODEL
    E101001 = "User not found. User with provided id doesn't exist."
    E101002 = "Unable to create user, missing required field : `login`."
    E101003 = "Unable to create user, `login` \"{}\" already exists."
    E101004 = ""
    E101005 = ""

    # CORE

