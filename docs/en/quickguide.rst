Quick guide
###########

Deploye and use Annso in 5 minutes. In the below tutorial :
 * <HOST> : is the server host, by example "www.annso.com"
 * <PORT> ! is the port that will be use by the annso python application, by example 8080
 * <ANNSO_PATH> : is the path on the server where is deployed the pirus python application, by example "/var/annso_v1"



Installation
============

The following tutorial will show you how to set up a quick development environment for the annso application on a linux server.
You may need to install first ::

        sudo apt install build-essential libssl-dev libffi-dev python3-dev virtualenv libpq-dev


Annso need a postgresql database (9.5+). As ususal, you can customise value, just don't forget to update the config.py file accordingly ::

        sudo apt install postgresql
        psql -U postgres -c "CREATE USER annso WITH PASSWORD 'annso';"
        psql -U postgres -c "DROP DATABASE IF EXISTS annso;"
        psql -U postgres -c "CREATE DATABASE annso;"
        psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE annso to annso;"


        
Then clone the repository and install requirements ::

        git clone https://github.com/REGOVAR/Annso.git
        cd Annso
        virtualenv -p /usr/bin/python3.5 venv
        source venv/bin/activate
        pip install -r requirements.txt



You will need to create following empty folder in the /tmp directory (you can change the location, but don't forget to update the config.py file) ::

        mkdir /tmp/annso_v1
        mkdir /tmp/annso_v1/cache
        mkdir /tmp/annso_v1/downloads
        mkdir /tmp/annso_v1/files
        
        

Init database ::

        psql -U annso -d annso -f <ANNSO_PATH>/annso/database/create_all.sql
        psql -U annso -d annso -f <ANNSO_PATH>/annso/database/scripts/import_refgen.sql
        
        
        
        

Using NginX
-----------
Create the file  into `/etc/nginx/sites-available/annso` with the following content

Replace <PORT> and <HOST> with the good value::

        #
        # Virtual Host configuration for pirus.absolumentg.fr
        #
        upstream aiohttp_annso
        {
                server 127.0.0.1:<PORT> fail_timeout=0;
        }

        server
        {
                listen 80;
                listen [::]:80;
                server_name <HOST>;

                location / {
                        # Need for websockets
                        proxy_http_version 1.1;
                        proxy_set_header Upgrade $http_upgrade;
                        proxy_set_header Connection "upgrade";

                        proxy_set_header Host $http_host;
                        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                        proxy_redirect off;
                        proxy_buffering off;
                        proxy_pass http://aiohttp_annso;
                }

                location /static {
                        root /tmp/annso_v1;
                }
        }


Enable this virtual host by creating a symbolic link ::

        sudo ln -s /etc/nginx/sites-enable/annso /etc/nginx/sites-available/annso 
        sudo /etc/init.d/nginx restart
	

Don't forget to modify the <ANNSO_PATH>/annso/config.py file according to your configuration.




Run Annso
---------

just ::

	cd <ANNSO_PATH>/annso
	make app





Using Annso
===========

Create an analysis
-----------------

todo


Setup samples
-------------

todo


Create and apply filters
------------------------

todo


Select variant and get result
-----------------------------

todo
