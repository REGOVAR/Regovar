
# Installation du serveur Regovar

À terme, Regovar pourra être installé via un paquet .deb. D'ici là, il est possible de l'installer via SaltStack, ou manuellement.

### Via SaltStack

Référez-vous au [SLS utilisé pour le déploiement au CHU d'Angers](https://github.com/REGOVAR/ServerConfiguration/blob/master/regovar/init.sls).

### Manuellement

La procédure manuelle reste relativement simple grâce à un script.sh qui va vous poser quelques questions afin de configurer et créer pour vous les containers docker, le proxy nginx et l'application regovar.  

####Pré-requis

 * Ubuntu Xenial LTS (pipelines et analyse de variants) ou Debian Stretch (analyse de variants uniquement).
 * Droits root sur le serveur
 * Accès internet depuis le serveur
 * git
 * [Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/)
 * [Docker-compose](https://docs.docker.com/compose/install/#install-compose)
 * Ne pas oublier de s'autoriser à utiliser docker directement
```
sudo usermod -a -G docker $USER
=> N'oubliez pas de se logout-login pour que l'ajout au groupe soit pris en compte
```
 
####Procédure

```sh
git clone https://github.com/REGOVAR/Regovar.git ~/Regovar
cd ~/Regovar/install
./install.sh
```
Laissez vous guider en répondant aux différentes questions.

Si vous laissez tout les choix par défaut, à la fin de l'installation vous pourrez voir 2 containers dans docker
```
➜  regovar git:(dev) docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
be2506e3b293        regovar             "python regovar.py"      24 minutes ago      Up 24 minutes       0.0.0.0:8500->8500/tcp   regovar_app
0fb1c4b61d4d        postgres            "docker-entrypoint.s…"   24 minutes ago      Up 24 minutes       5432/tcp                 regovar_pg
```
NB:
 * `regovar_pg`: est la base de donnée (postgreSQL 9.6) dont les données sont ecrites dans /var/regovar/pgdata;
 * `regovar_app`: est l'application regovar mappé sur le port 8500 de votre serveur;
 * Le code source de votre serveur est mappé sur le dépot github que vous avez cloné: `~/Regovar`.
 
 
