#!env/python3
# coding: utf-8


class ERR():
    # SETUP / CONFIG
    E000001 = "Unable to connect to the database with settings provided by configuration file."
    E000002 = "Error occured when initializing the database."

    # DATABASE / MODEL
    E100001 = "Error when requesting the database. SQL error occured in the custom query (query logged in the error's snippet log file)."
    E100002 = "Unable to save resource {} into database."

    E101001 = "User not found. User with provided id ({}) doesn't exists."
    E101002 = "Unable to create or update user. Wrong data provided."
    E101003 = "User deletion can only to be done by an admin."

    E101004 = "Unable to delete yourself. This action must be done by another admin."
    E101005 = "Unable to edit your roles yourself. This action must be done by an admin."
    E101006 = "Unable to remove to yourself the Administration role. This action must be done by an admin."


    E102001 = "Project not found. Project with provided id ({}) doesn't exists."
    
    
    
    
    # CORE

    E202001 = "User not authorized to edit the project."
    E202002 = "Unable to create or update project. Wrong data provided."
    