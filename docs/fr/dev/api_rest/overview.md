# Guide du développeur

Bienvenue à toi, 

Cette page à 2 rôles :
 * Lister les liens vers l'ensemble de la documentation technique.
 * Présenter le B-A-BA que doivent connaître toute personne désirant participer au projet (Le "welcom guide" donc).



## Documentation
 1. Généralités 
     * Organisation du projet et des sources
     * Architecture système de Regovar
     * Architecture de l'application Regovar
     * Nommenclature et règle de codage
     * [Log et gestion des erreurs](https://hackmd.io/JwRgzAhgJgbA7DAtCaAGRAWAHAIx4vAMy0RjMmCyzFRBiA==)
         * [Liste des erreurs gérées](https://hackmd.io/EYBgJgHBzAjAtAMwMYFMAs91lgTngIYggCs8AzJCcAeegEyqNA==)
 1. [Modele de donnée]()
     * [Base de donnée PostgresSQL]()
     * [Modèle de donnée (python SQLAlchemy)]()
 1. [Regovar Core]()
 1. [API Rest](https://hackmd.io/GYIzE5gJgQwWgAwEYBsBTOAWArAYwCZwji4DMc6+2M4Sm+ypQA==)
     * [`user`](https://hackmd.io/OwQwjOCsBsBMC0BjWAOE8AsIAmx4E5pR5sAGRUgM0v1n22jCA===)
     * [`project`]()
     * [`file`]()
 1. [API cli]()


## Organisation du projet et des sources
Regovar est une application client-serveur.
 * `Regovar` désigne en général le serveur ou l'application server, mais parfois aussi peut désigner l'équipe qui travaille sur le projet ou "l'organisation" github du projet ;
 * `QRegovar` désigne le client officiel de Regovar développé en Qt.

Les sources de ces projets sont open-source et accessible sur les dépôts githbub:
 * [Regovar](https://github.com/REGOVAR/Regovar)
 * [QRegovar](https://github.com/REGOVAR/QRegovar)

Les dépôts du projet Regovar s'organisent ainsi:
```
/Regovar
   /docs
   /install
   /regovar               <- tout le code source se trouve ici
       /cli                  le module pour l'api cli
       /core                 le module principale (model + core)
       /web                  le module pour l'api web (rest)
       Makefile
       regovar_server.py  <- run le server (api REST)
       regovar_cli.py     <- run Regovar en tant qu'application python standard
       regovar_test.py    <- run les tests unitaires
   /tests                 <- tout le code source additionnel pour les tests
   README.md
   LICENSE
   requirements.txt       <- généré par pip
```
D'une manière générale, l'arborescence de fichier doit respecter le plus fidélement possible l'architecture de Regovar (que voici)



## Architecture système de Regovar
*A FAIRE, beau schéma avec le server, les couches matérielles/logicielles (linux, brtrfs, server/sequencer/réseau/mail/clients, ... )


## Architecture de l'application Regovar
[]



## Nommenclature et règle de codage
Pour ceux qui connaissent, on respecte la convention python [PEP8](https://www.python.org/dev/peps/pep-0008/). Pour ceux qui ont la flemme de tout lire, au moins lire [le résumé par Sam&Max](http://sametmax.com/le-pep8-en-resume/)
Cependant on tolère les entorses suivantes :
 - sauter plusieurs ligne entre définition de class ou de fonction car ça permet d'avoir un code plus aéré;
 - avoir des lignes de code faisant plus de 80 caractères... faut pas déconner non plus, on a des écrans larges maintenant.



## Documentation
Bien documenter le code. chaque fonction et chaque classe doit avoir un commentaire en-tête (entre triple """).

Penser aussi à mettre à jour la documentation en ligne une fois que vous avez terminer ce que vous avez commencé. Ne pas hésiter à mettre un ticket github pour ne pas oublier de faire la traduction dans les autres langues si vous ne le faites pas.

Si vous créez de nouvelles erreurs, [se référer à la documentation](https://hackmd.io/JwRgzAhgJgbA7DAtCaAGRAWAHAIx4vAMy0RjMmCyzFRBiA==) pour y associer un code et intégrer correctement ces erreurs dans le système mis en place.
