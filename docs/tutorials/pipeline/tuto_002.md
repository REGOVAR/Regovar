# Encapsuler son pipeline dans Regovar (notions de base)

Ce tutoriel présente les notions de base à connaître avant de s'attaquer à l'encapsulation de son pipeline dans Regovar. 
La réalisation technique de cette encapsulation dépend de la technologie utilisée et est développé dans des tutoriels suivants :
* [Créer un pipeline pour Regovar avec LXD](tuto_003.md)
* [Créer un pipeline pour Regovar avec Docker](tuto_004.md)



## Qu'est-ce que l'encapsulation ?
Regovar permet d'utiliser n'importe quel pipeline bioinformatique. 
Pour ce faire chaque pipeline doit être « packagé » d'une certaine façon. En effet, pour des raisons de sécurité et de maintenance, chaque pipeline est encapsulé dans un container qui va l'isoler virtuellement du serveur qui va vous permettre de démarrer et superviser son exécution. 

###Technologies
L'encapsulation repose sur le concept de conteneurisation. À l'heure actuelle, la technologie utilisé est [LXC](https://linuxcontainers.org/fr/). Un module pour supporter la technologie [Docker](https://www.docker.com/what-docker) est prévu mais n'a pas encore été developpé. Si cela vous intéresse, vous pouvez participer (et accélérer) le développement de ce module en contactant les développeurs via GitHub ou à l'adresse dev@regovar.org.


###Les points positifs
* Sécurité assurée et maintenance facilitée : chaque pipeline est isolé dans son container, absence de risque de conflits avec les autres logiciels installés sur le serveur ;
* archivage des différentes versions des pipelines ;
* automatisation ;
* facilité d'utilisation pour les utilisateurs non experts ;
* reproductibilité des runs ;
* interface commune pour les contrôler tous ;
* possibilité de surveiller et de contrôler l'exécution des pipelines (logs, pause, start, cancel) ;
* file d'attente pour l'exécution les pipelines.



###Les points négatifs
* Contrainte à respecter pour l'exécution du pipeline (API) ;
* travail supplémentaire pour encapsuler son pipeline. Cela peut prendre 1/2 à 1 journée en fonction des problèmes rencontrés.


## Exigences et options

Quelque soit la technologie utilisée ([LXD](pipeline/tuto_003.md) ou [Docker](pipeline/tuto_004.md)), votre pipeline encapsulé se présentera sous la forme d'un fichier zip avec à sa racine un fichier `manifest.json`.

Seront décrit dans ce fichier tout ce qui permettra à Regovar et aux administrateurs de correctement installer et utiliser votre pipeline. Ci-dessous se trouve le format attendu pour le fichier `manifest.json`:

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
- NAME : votre pipeline doit impérativement avoir un nom :) ;
- DESCRIPTION : il est recommandé d'expliquer en quelques mots à quoi sert votre pipeline et son cadre d'application (objectif du pipeline, séquençeur, type de données...) ;
- VERSION : ce renseignement permet de différencier et d'installer plusieurs version de votre pipeline sur un même serveur. Sans ça, il est impossible d'installer deux pipelines qui ont le même nom sur le serveur ;
- TYPE : vous devrez indiquer impérativement quel est la technologie utilisée pour cotre container (actuellement, seul le type `"lxd"` est supporté) ;
- INPUTS, OUTPUTS, LOGS et DATABASES : vous pouvez librement choisir où et comment sont nommés ces dossiers dans votre container, mais ceux-ci doivent être présents et permettra au serveur Regovar et à votre pipeline de travailler correctement ensemble;
- JOB : la ligne de commande pour démarrer votre pipeline ;
- FORMULAIRE : si votre pipeline a des paramètres configurable, vous pouvez décrire ces paramètres dans un fichier json afin que Regovar puisse permettre à l'utilisateur de les régler via un formulaire qui sera automatiquement généré depuis ce fichier json;
- ICON : si vous le souhaitez, vous pouvez fournir un icone qui sera associé à votre pipeline dans Regovar ;
- PRESENTATION et AIDE : il est conseillé d'avoir (au format html) une page de présentation de votre pipeline et une page d'aide à la configuration de ce dernier. Ces pages seront en permanence présenter et accessible aux utilisateurs de votre pipeline dans Regovar ;
- LICENSE_NAME et LICENSE : les pipelines de Regovar étant fournis sous forme de fichier zip clés en main, il y a de forte chance qu'il puisse se retrouver très vite tout seul dans la nature. Il est donc recommandé de joindre à votre pipeline un fichier LICENSE ;
- README : si l'installation de votre pipeline nécessite des actions particulières de la part des administrateurs. Par exemple si votre pipeline nécessite d'accéder en local à des base de données volumineuses, il vous faudra indiquer dans le README où et comment se procurer/générer ces bases. Ces bases doivent impérativement être sous forme de fichiers qui seront installés par les administrateurs et seront par la suite automatiquement accessible par votre pipeline dans son container via le répertoire DATABASES.

Structure type d'un package
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

## Configuration via le fichier config.json
Regovar offre à ses utilisateurs une interface simple et conviviale pour démarrer et superviser soit-même les pipelines. 

La configuration se déroule en 3 étapes :
- Choix du pipeline parmi la liste des pipeline installé sur le serveur
- Choix des fichiers sur lequel devra travailler le pipeline.
- Configuration du pipeline via un formulaire spécifique à celui-ci

Pour cette troisième et dernière étape, les développeurs doivent fournir avec leur pipeline un fichier `form.json` (cf `manifest.json`) qui va décrire les paramètres de ce dernier. Regovar s'occupera ensuite de générer le formulaire correspondant afin de récupérer les réglages de l'utilisateur. Ces valeurs sont ensuite stockées dans un fichier qui se nommera `config.json` et qui se trouvera dans le répertoire INPUTS du contenaire du pipeline (cf `manifest.json`)

L'exemple ci-dessous montre la structure attendu pour le fichier `form.json` ainsi que les différents types de paramètre supportés.
```
{
    "$schema": "http://json-schema.org/draft-03/schema#",
    "type": "object",
    "properties":
    {
        "param1_key":
        {
            "title": "Mon paramètre 1",
            "description": "Premier paramètre obligatoire de mon pipeline",
            "type": "integer",
            "required": true,
            "default": 20,
            "minimum": 0,
            "maximum": 100
        },
        "param2_key":
        {
            "title": "Mon paramètre 2",
            "description": "Deuxième paramètre optionnel de mon pipeline",
            "type": "string",
            "required": false,
            "default": "",
        },
        "param3_key":
        {
            "title": "Mon paramètre 3",
            "description": "Ce troisième paramètre est une liste à choix unique (combobox)",
            "type": "enum",
            "required": true,
            "enum": ["choix 1", "choix 2", "choix 3"]
            "default": "choix 1"
        },
        "param4_key":
        {
            "title": "Mon paramètre 4",
            "description": "Les type integer pour les entiers, et number pour les réels (float)",
            "type": "number",
            "required": false,
            "default": 1.75,
            "minimum": -75,
            "maximum": 106.5
        }
    }
}
```

###Les différents types de champs

**integer**

Pour saisir des entiers (int). 
```
"param_key":
{
    "title": "Param name",
    "description": "Param description",
    "type": "integer",
    "required": true,
    "default": 20,
    "minimum": 0,
    "maximum": 100
}
```

**number**

Pour saisir des réels (float)
```
"param_key":
{
    "title": "Param name",
    "description": "Param description",
    "type": "number",
    "required": true,
    "default": 20,
    "minimum": 0,
    "maximum": 100
}
```

**string**

Pour saisir du texte (string)
```
"param_key":
{
    "title": "Param name",
    "description": "Param description",
    "type": "string",
    "required": true,
    "default": "default value",
}
```

**enum**

Pour proposer une liste à choix unique (liste de string)
```
"param_key":
{
    "title": "Param name",
    "description": "Param description",
    "type": "enum",
    "enum": ["choix 1", "choix 2", "choix 3"]
    "required": true,
    "default": "choix 1"
}
```

Pour les enum, vous pouvez soit proposer une liste de valeur manuellement comme dans l'exemple soit opter pour les listes générés autamtiquement grâce aux mots clés suivant :

- `__INPUTS_FILES__` va générer la liste des fichiers qui ont été sélectionnés lors de l'étape précédente de la configuration du pipeline. Celà permet ainsi de pouvoir sélectionner un fichier en particulier parmis plusieurs et de l'indiquer au pipeline.
```
    "enum": "__INPUTS_FILES__",
```

- `__GENOMES_REFS__` va générer la liste des génomes de références (Hg19, Hg38, ...) qui ont été installés sur le serveur et dont les fichiers et bases de données associés seront accessible par le pipeline via le répertoire DATABASES.
```
    "enum": "__GENOMES_REFS__",
```


