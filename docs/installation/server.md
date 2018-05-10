
# Installation du serveur Regovar

À terme, Regovar pourra être installé via un paquet .deb. D'ici là, il est possible de l'installer via SaltStack ou via Docker.

### Via SaltStack

10 mai 2018 : l'installation via SaltStack est en cours de maintenance.

Référez-vous au [README](https://github.com/REGOVAR/ServerConfiguration/blob/master/README.md) de la configuration utilisée pour le déploiement au CHU d'Angers et de Nancy.

### Via Docker

La procédure reste relativement simple grâce à un script `install.sh` qui va vous poser quelques questions afin de configurer et créer pour vous les containers docker, le proxy nginx et l'application regovar.  

####Pré-requis

 * Ubuntu Xenial LTS (pipelines et analyse de variants) ou Debian Stretch ou supérieur (analyse de variants uniquement).
 * Droits root sur le serveur
 * Accès internet depuis le serveur
 * Git
 * [Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/)
 * [Docker-compose](https://docs.docker.com/compose/install/#install-compose)
 * Ne pas oublier de s'autoriser à utiliser Docker directement avec la commande ci-dessous.

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
Laissez vous guider en répondant aux différentes questions. Il vous sera demandé une clé API OMIM, que vous pouvez obtenir à [cette adresse](https://www.omim.org/api).

Une fois l'installation terminée, vous devez mettre à jour les informations HPO.
```
cd /var/regovar/app
make update_hpo
```

####Check final

Si vous laissez tous les choix par défaut, à la fin de l'installation vous pourrez voir 2 containers dans docker
```
➜  regovar git:(dev) docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
be2506e3b293        regovar             "python regovar.py"      24 minutes ago      Up 24 minutes       0.0.0.0:8500->8500/tcp   regovar_app
0fb1c4b61d4d        postgres            "docker-entrypoint.s…"   24 minutes ago      Up 24 minutes       5432/tcp                 regovar_pg
```

 * `regovar_pg`: est la base de donnée (postgreSQL 9.6) dont les données sont ecrites dans /var/regovar/pgdata;
 * `regovar_app`: est l'application regovar mappé sur le port 8500 de votre serveur;

Le code source de votre serveur est mappé sur le dépot github que vous avez cloné: `~/Regovar`.
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
 
Le répertoire `var/regovar/config` contient l'ensemble des fichiers générés automatiquement par le script. Ces fichiers sont ensuite utilisé via des liens symboliques
```
 ➜  regovar git:(dev) ll /var/regovar/app/
total 64K
drwxrwxr-x 5 olivier olivier 4.0K Apr 30 15:16 api_rest
lrwxrwxrwx 1 olivier olivier   29 May  2 13:45 config.py -> /var/regovar/config/config.py
drwxrwxr-x 6 olivier olivier 4.0K Apr 27 15:06 core
lrwxrwxrwx 1 olivier olivier   28 May  2 13:54 Makefile -> /var/regovar/config/Makefile
drwxr-xr-x 2 olivier olivier 4.0K May  2 13:45 __pycache__
-rwxrwxr-x 1 olivier olivier  13K Apr 26 16:41 regovar_cli.py
-rw-r--r-- 1 olivier olivier  195 May  2 13:45 regovar.log
-rw-rw-r-- 1 olivier olivier  981 May  2 13:54 regovar.py
-rw-rw-r-- 1 olivier olivier  308 Apr 26 16:41 setup.cfg
drwxrwxr-x 5 olivier olivier 4.0K Apr 26 16:41 tests
-rwxrwxr-x 1 olivier olivier 3.0K Apr 26 16:41 tests.py
-rw-rw-r-- 1 olivier olivier  14K May  2 13:54 update_hpo.py
```
 
 
