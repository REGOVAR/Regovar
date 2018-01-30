#!/bin/sh


# Start postgresql service
/etc/init.d/postgresql restart




# Run server
python -Wdefault /var/regovar/app/regovar/regovar_server.py