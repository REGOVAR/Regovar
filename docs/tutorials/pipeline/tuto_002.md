# Encapsuler son pipeline dans Regovar (conceptes de base)

Ce tutoriel présente les notions de base à connaître avant de s'attaquer à l'encapsulation de son pipeline dans Regovar. 



## Qu'est-ce que l'encapsulation
Regovar permet d'utiliser n'importe quel pipeline bioinformatique. 
Pour ce faire chaque pipeline doit être "packagé" d'une certaine façon et respecter 
Pour des raisons de sécurité et de maintenance, chaque pipeline est encapsulé dans un container qui va l'isoler. 
Ainsi on peut installer et exécuter autant de pipeline/container que l'on veut sur le serveur sans risquer de corrompre le serveur et ses données.


### Techniquement 



## Les points positifs
* sécurité assuré et maintenance facilité: chaque pipeline est isolé dans son container comme si il est tout seul. Pas de risque de conflits avec les autres logiciels installé sur le serveur
* archivage des différentes versions des pipelines 
* automatisation 
* facilité d'utilisation pour les utilisateurs non expert (IHM simple)
* reproductibilité des runs
* une interface commune pour les controler tous
* possibilité de surveiller et de controler l'exécution des pipelines (logs, pause/start, cancel)
* file d'attente pour l'exécution les pipelines



## Les points négatifs
* contrainte à respecter pour l'exécution du pipeline. (API)
* travail supplémentaire pour encapsuler son pipeline. Celà peut prendre 1/2 à 1 journée en fonction des problèmes rencontrés.
