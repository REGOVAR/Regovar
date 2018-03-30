# Encapsuler son pipeline dans Regovar (notions de base)

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


## Encapsulation: exigences et options

Quelque soit la technologie utilisé ([LXD](pipeline/tuto_003.md) ou [Docker](pipeline/tuto_004.md)), votre pipeline encapsulé se présentera sous la forme d'un fichier zip avec à sa racine un fichier `manifest.json`.

Seront décrit dans ce fichier tous ce qui permettra à Regovar et aux administrateurs de correctement installer et utiliser votre pipeline. Ci dessous, le format attendu pour le fichier `manifest.json`:

```
{
    "name" : NAME,
    "description" : DESCRIPTION,
    "version": VERSION,
    "type": TYPE,
    "license" : LICENSE_NAME,
    "developpers" : ["Olivier Gueudelot", ...],
    "job" : JOB,
    "inputs" : INPUTS,
    "outputs" : OUTPUTS,
    "databases": DATABASES,
    "logs" : LOGS,
    "documents":
    {
        "form": FORMULAIRE,
        "icon": ICON,
        "presentation": PRESENTATION,
        "help": AIDE,
        "license": LICENSE,
        "readme": README
    }
}
```
- NAME: votre pipeline doit impérativement avoir un nom :) ;
- DESCRIPTION: c'est recommandé d'expliquer en quelques mot à quoi sert votre pipeline;
- VERSION: ce renseignement est optionnel, mais il permettra de différencier et d'installer plusieurs version de votre pipeline sur un même serveur. Sans ça, il est impossible d'installer 2 pipelines qui ont le même nom sur le serveur;
- TYPE: vous devrez indiquer impérativement quel est la technologie utilisé pour cotre container. Actuellement seule le type `"lxd"` est supporté. 
- INPUTS, OUTPUTS, LOGS et DATABASES: vous pouvez librement choisir où et comment sont nommés ces dossiers dans votre container, mais ceux-ci doivent être présents et permettra au serveur Regovar et à votre pipeline de travailler correctement ensemble;
- JOB: la ligne de commande pour démarrer votre pipeline;
- FORMULAIRE: si votre pipeline a des paramètres configurable, vous pouvez décrire ces paramètres dans un fichier json afin que Regovar puisse permettre à l'utilisateur de les régler via un formulaire qui sera automatiquement généré depuis ce fichier json;
- ICON: si vous le souhaitez, vous pouvez fournir un icone qui sera associé à votre pipeline dans Regovar;
- PRESENTATION et AIDE: il est conseillé d'avoir (au format html) une page de présentation de votre pipeline et une page d'aide à la configuration de ce dernier. Ces pages seront en permanence présenter et accessible aux utilisateurs de votre pipeline dans Regovar;
- LICENSE_NAME et LICENSE: les pipelines de Regovar étant fournis sous forme de fichier zip clés en main, il y a de forte chance qu'il puisse se retrouver très vite tout seul dans la nature. Il est donc recommandé de joindre à votre pipeline un fichier LICENSE;
- README: si l'installation de votre pipeline nécessite des actions particulières de la part des administrateurs. Par exemple si votre pipeline nécessite d'accéder en local à des base de données volumineuses, il vous faudra indiquer dans le README où et comment se procurer/générer ces bases. Ces bases doivent impérativement être sous forme de fichiers qui seront installés par les administrateurs et seront par la suite automatiquement accessible par votre pipeline dans son container via le répertoire DATABASES.

Structure type d'un package:
```
MyPipeline_v1.8.zip
  |  doc/
  |   |  icon.jpg
  |   |  prez.html
  |   |  help.html
  |  form.json
  |  LICENSE.txt
  |  lxc_image.tar.gz
  |  manifest.json
  |  README.txt
```
