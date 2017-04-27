Quick guide
###########

Regovar est un logiciel libre pour l’analyse de données de séquençage haut débit pour les maladies génétiques rares (mais pas que). Son rôle est de permettre le suivit, l'analyse et la gestion des données issues des séquenceurs dans le but de faire de la recherche ou du diagnostiques, et ce que l'on soit un bioinformaticien, un biologiste ou bien un clinitien. 

Quelques liens:
 * Site officiel : http://regovar.org
 * Source du server : https://github.com/REGOVAR/Regovar

Attention:
| Ce guide vous explique comment installer le server afin de le tester directement via son interface web. 
| Il s'agit d'une installation rapide dans un container afin de ne pas polluer votre machine avec les dépendances. 
| Il ne s'agit du guide d'installation pour un serveur dans le but d'une utilsation en production.



Installation
============

Prérequis :
 * ordinateur linux avec accès internet

Installtion :

Optional, to create a lxd container:
    $ lxc-create -n regovar -t download -- -d ubuntu -r xenial -a amd64
    $ lxc-start -n regovar
    $ lxc-attach -n regovar
or (with ubuntu)
   $ lxc launch images:ubuntu/xenial regovar
   $ lxc exec regovar -- /bin/bash
    
    
Installation script for annso on a fresh Ubuntu Xenial:
    # apt update && apt upgrade
    # apt install git ca-certificates nginx uwsgi postgresql postgresql-contrib postgresql-server-dev-9.5 build-essential libssl-dev libffi-dev python3-dev virtualenv libpq-dev libmagickwand-dev nano
    # useradd regovar --create-home
    # sudo -u postgres createuser -P -s regovar # type "regovar" as password
    # sudo -u postgres createdb regovar
    # mkdir -p /var/regovar/{cache,downloads,files}
    # chown -R regovar:regovar /var/regovar
    # su regovar
    $ cd
    $ git clone https://github.com/REGOVAR/Regovar.git ~/Regovar
    $ cd ~/Regovar
    $ virtualenv -p /usr/bin/python3.5 venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt
    $ psql -U regovar -d regovar -f ./install/create_all.sql
    $ cd regovar
    $ make install 
    $ nano ./config.py # edit the config file with your settings
    $ make app &!
    $ exit
    # echo 'upstream aiohttp_annso
    {
        server 127.0.0.1:8100 fail_timeout=0;
    }

    server
    {
        listen 80;
        listen [::]:80;

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
            root /var/regovar/annso;
        }
    }' > /etc/nginx/sites-available/annso
    # rm /etc/nginx/sites-enabled/default
    # ln -s /etc/nginx/sites-available/annso /etc/nginx/sites-enabled
    # /etc/init.d/nginx restart
    # exit
    
    
Optional, if annso wrapped into a lxd container:
    $ IP=$(lxc-info -n regovar_annso | grep IP | sed 's/.* //')
    $ firefox $IP


