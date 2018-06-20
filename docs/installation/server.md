
# Installation du serveur Regovar

À terme, Regovar pourra être installé via un paquet .deb. À l'heure actuelle, deux modes de déploiement pour le serveur sont proposés :
 - directement sur le serveur (installation et configuration automatisées via SaltStack) ;
 - via Docker où Regovar est lui-même encapsulé dans un conteneur.
La première méthode est prévue pour un déploiement et une utilisation de Regovar sur une machine dédiée, tandis que la seconde permet une installation rapide et simple sans impact sur la configuration de la machine hôte.

### Via SaltStack

Référez-vous au [README](https://github.com/REGOVAR/ServerConfiguration/blob/master/README.md) de la configuration utilisée pour le déploiement au CHU d'Angers et de Nancy.

Une fois le serveur installé, vous pouvez le démarrer.
```sh
cd ~/Regovar/regovar
sudo -u regovar python3 regovar.py
```

### Via Docker

La procédure reste relativement simple grâce à un script `install.sh` qui va vous poser quelques questions afin de configurer et créer pour vous les conteneurs docker, le proxy nginx et l'application regovar.  

####Pré-requis

 * Ubuntu Xenial LTS (pipelines et analyse de variants) ou Debian Stretch ou supérieur (analyse de variants uniquement)
 * Droits root sur le serveur
 * Accès internet depuis le serveur
 * Git
 * [Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/)
 * [Docker-compose](https://docs.docker.com/compose/install/#install-compose)
 * Ne pas oublier de s'autoriser à utiliser Docker directement avec la commande ci-dessous

```sh
sudo usermod -a -G docker $USER
```

N'oubliez pas de vous déconnecter de la session en cours et de vous reconnecter pour que l'ajout au groupe soit pris en compte.

####Procédure

```sh
git clone https://github.com/REGOVAR/Regovar.git ~/Regovar
cd ~/Regovar/install
./install.sh
```
Laissez-vous guider en répondant aux différentes questions. Il vous sera demandé une clé API OMIM, que vous pouvez obtenir à [cette adresse](https://www.omim.org/api).

Une fois l'installation terminée, vous devez mettre à jour les informations HPO.
```
cd /var/regovar/app
make update_hpo
make update_panels
make start
```

####Check final

Si vous laissez tous les choix par défaut, à la fin de l'installation vous pourrez voir deux conteneurs dans docker.
```
➜  regovar git:(dev) docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
be2506e3b293        regovar             "python regovar.py"      24 minutes ago      Up 24 minutes       0.0.0.0:8500->8500/tcp   regovar_app
0fb1c4b61d4d        postgres            "docker-entrypoint.s…"   24 minutes ago      Up 24 minutes       5432/tcp                 regovar_pg
```

 * `regovar_pg`: est la base de donnée (postgreSQL 9.6) dont le contenu est écrit dans /var/regovar/pgdata;
 * `regovar_app`: est l'application regovar mappée sur le port 8500 de votre serveur;

Le code source de votre serveur est mappé sur le dépot GitHub que vous avez cloné : `~/Regovar`.
```
➜  regovar git:(dev) ll /var/regovar 
total 32K
lrwxrwxrwx  1 olivier olivier   44 May  2 13:45 app -> /home/olivier/git/Regovar/install/../regovar
drwxr-xr-x  2 olivier olivier 4.0K May  2 13:14 cache
drwxr-xr-x  2 olivier olivier 4.0K May  2 13:45 config
drwxr-xr-x  4 olivier olivier 4.0K May  2 13:14 databases
drwxr-xr-x  2 olivier olivier 4.0K May  2 13:14 downloads
drwxr-xr-x  2 olivier olivier 4.0K May  2 13:14 files
drwxr-xr-x  2 olivier olivier 4.0K May  2 13:14 jobs
drwx------ 19 olivier olivier 4.0K May  2 13:45 pgdata
drwxr-xr-x  2 olivier olivier 4.0K May  2 13:14 pipelines
```
 
 - `/var/regovar/config` répertorie l'ensemble des fichiers configurables de l'application.

