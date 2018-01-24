
# Installation du serveur Regovar

## Pré-requis

 * Ubuntu Xenial LTS (pipelines et analyse de variants) ou Debian Stretch (analyse de variants uniquement).
 * Droits root sur le serveur
 * Accès internet depuis le serveur
 * Python 3.5 ou plus
 * PostgresSQL 9.6 ou plus

## Installation

À terme, Regovar pourra être installé via un paquet .deb. D'ici là, il est possible de l'installer via SaltStack, ou manuellement.

### Via SaltStack

Référez-vous au [SLS utilisé pour le déploiement au CHU d'Angers](https://github.com/REGOVAR/ServerConfiguration/blob/master/regovar/init.sls).

### Manuellement

Les commandes sont à exécuter en tant que root.

```sh
apt update && apt upgrade
apt install curl git ca-certificates nginx postgresql-9.6
	
adduser regovar

sudo -u postgres createuser -P -s regovar # type "regovar" as password
sudo -u regovar createdb regovar

mkdir -p /var/regovar/{cache,downloads,files,pipelines,jobs,databases/hg19,databases/hg38}
curl http://hgdownload.soe.ucsc.edu/goldenPath/hg19/database/refGene.txt.gz | gunzip > /var/regovar/databases/hg19/refGene.txt:
curl http://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/refGene.txt.gz | gunzip > /var/regovar/databases/hg38/refGene.txt:
chown -R regovar:regovar /var/regovar

sudo -u regovar git clone https://github.com/REGOVAR/Regovar.git /home/regovar/Regovar
cd /home/regovar/Regovar
sudo -u regovar pip install -r requirements.txt
cd regovar
sudo -u regovar make init
sudo -u regovar sed -i 's/^\(\s*DATABASE_NAME\s*=\s*"\)[^"]\+\(".*\)/\1regovar\2/' config.py
sudo -u regovar make setup
sudo -u regovar make install_hpo
```

## Configuration avec NGINX

Configurez un site comme suit dans `/etc/nginx/sites-available/regovar` :

```nginx
upstream regovar
{
    server 127.0.0.1:8500 fail_timeout=0;
}

server
{
    listen 80;
    listen [::]:80;

    location / 
    {
        # Need for websockets
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_redirect off;
        proxy_buffering off;
        proxy_pass http://regovar;
    }
}
```

… puis activez le site :


```sh
rm /etc/nginx/sites-enabled/default
ln -s /etc/nginx/sites-available/regovar /etc/nginx/sites-enabled
service nginx restart
```

## Configurer HTTPS et la certification

TODO

## Démarrer et tester le serveur

```sh
cd /home/regovar/Regovar/regovar
sudo -u regovar make app
```
