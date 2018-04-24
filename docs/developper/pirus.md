# Pirus : PIpeline RUnning Service

Cette page aborde le sujet complexe de la contenairisation des pipelines. Mais aussi celle du serveur Regovar lui-même. L'API Pirus, permet au serveur d'utiliser différentes technologies. Actuellement 2 technologies sont supportées: LXD et Docker.

**CEPENDANT:** comme le serveur lui-même peut être encapsulé dans Docker, nous recommandons de ne travailler qu'avec Docker. Ainsi, vos pipelines seront utilisables sur toutes les instances de Regovar qu'elles soient ou non encapsulé dans Docker.


## Fonctionnement


## LXD


## Docker



## Créer son propre Manager de Container




## Encapsulation du serveur Regovar

Regovar étant une application complexe, la tâche n'est pas simple. Il faut en effet que notre container réponde aux exigeances suivantes :
 - python 3.6
 - postgresql 9.6
 - pouvoir utiliser le service docker de l'HOST depuis le container Regovar
 - exposer l'API Regovar sur le port 80 et 443 de l'HOST
 - utiliser un certains nombre de volume pour la pérénité des données (base de donnée postgreSQL et les différents fichiers, logs, et base de données)

###Docker-in-Docker

Avant de s'aventurer plus loin, il est important de bien comprendre les enjeux d'avoir un Docker qui puisse utiliser Docker. Tout est dis dans l'[article suivant](https://jpetazzo.github.io/2015/09/03/do-not-use-docker-in-docker-for-ci/)

Donc dans notre cas, (ouf) il n'est pas nécessaire d'avoir Docker-in-Docker. Il nous faudra juste installer les binaires de Docker dans notre container, et exposer le socket Docker de l'HOST afin que depuis notre container on puisse l'utiliser. Ainsi, quand Regovar manipulera des pipelines (installation/suppression d'image, création, execution, supervision de container), il le fera directement sur l'HOST ce qui est plus propre.

```
  docker run -v /var/run/docker.sock:/var/run/docker.sock ...
```

###postgresql 9.6

La principale difficulté ici est de configurer correctement postgresql et le container pour que la base de donnée soit partagé avec l'HOST afin d'assurer la pérénité et l'archivage des données indépendament du container.

Pour commencer il faudra installer la bonne version, qui n'est pas encore disponible dans les dépots officiels:
```
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN apt install  postgresql-9.6
```

Ensuite il faut configurer postgreSQL pour qu'il utilise la base de donnée partagé et non celle par défaut:

TODO



###Nginx port mapping

TODO

###Répertoires paratagés

TODO




