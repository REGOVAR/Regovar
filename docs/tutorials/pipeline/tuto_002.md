# Encapsuler son pipeline dans Regovar (conceptes de base)

Ce tutoriel présente les notions de base à connaître avant de s'attaquer à l'encapsulation de son pipeline dans Regovar. 
La réalisation technique de cette encapsulation dépend de la technologie utilisé et est développé dans des tutoriels suivants :
* [Créer un pipeline pour Regovar avec LXD](pipeline/tuto_003.md)
* [Créer un pipeline pour Regovar avec Docker](pipeline/tuto_004.md)



## Qu'est-ce que l'encapsulation
Regovar permet d'utiliser n'importe quel pipeline bioinformatique. 
Pour ce faire chaque pipeline doit être "packagé" d'une certaine façon. En effet pour des raisons de sécurité et de maintenance, chaque pipeline est encapsulé dans un container qui va l'isoler virtuellement du serveur qui va vous permettre de démarrer et superviser son exécution. 

## Technologies
L'encapsulation repose en fait sur le concepte de machine virtuelle. A l'heure actuelle, le technologie utilisé est [LXC](https://linuxcontainers.org/fr/). Un module pour supporter la technologie [Docker](https://www.docker.com/what-docker) est prévu mais n'a pas encore été developpé. Si celà vous intéresse vous pouvez participer (et accélérer) le développement de ce module en contactant les développeurs via github ou à l'adresse dev@regovar.org


## Les points positifs
* Sécurité assuré et maintenance facilité: chaque pipeline est isolé dans son container comme si il est tout seul. Pas de risque de conflits avec les autres logiciels installé sur le serveur;
* Archivage des différentes versions des pipelines;
* Automatisation;
* Facilité d'utilisation pour les utilisateurs non expert (IHM simple);
* Reproductibilité des runs;
* Une interface commune pour les controler tous;
* Possibilité de surveiller et de controler l'exécution des pipelines (logs, pause/start, cancel);
* File d'attente pour l'exécution les pipelines.



## Les points négatifs
* Contrainte à respecter pour l'exécution du pipeline (API);
* Travail supplémentaire pour encapsuler son pipeline. Celà peut prendre 1/2 à 1 journée en fonction des problèmes rencontrés.
