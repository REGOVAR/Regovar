# Encapsuler son pipeline dans Regovar (notions de base)

Ce tutoriel présente les notions de base à connaître avant de s'attaquer à [l'encapsulation de son pipeline dans Regovar](tuto_002.md). Ensuite 2 exemples concrets d'encapsulation détaillent pas à pas ce qu'il faut faire pour vous exercer:
* [Ex1: Pipeline non paramétrable](tuto_003.md)
* [Ex2: Pipeline paramétrable](tuto_004.md)


## Qu'est-ce que l'encapsulation ?
Regovar permet d'utiliser n'importe quel pipeline bioinformatique. 
Pour ce faire chaque pipeline doit être « packagé » d'une certaine façon. En effet, pour des raisons de sécurité et de maintenance, chaque pipeline est encapsulé dans un container qui va l'isoler virtuellement du serveur qui va vous permettre de démarrer et superviser son exécution. 

###Technologies
L'encapsulation repose sur le concept de conteneurisation. La technologie utilisé est [Docker](https://www.docker.com/what-docker). Le choix de Docker a été fait car la communauté autour de cette technologie est très active, la technologie est fiable, relativement simple à utiliser et performante. De plus, beaucoup de projet bioinformatiques utilisent Docker, comme [biocontainers](http://biocontainers.pro) ou [Bioboxes](http://bioboxes.org/), ce qui offre la possibilité de partager les outils avec ces communautés.


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

Votre pipeline encapsulé se présentera sous la forme d'un fichier zip respectant la structure suivante:

```
MyPipeline_v1.0.zip
  |  doc/
  |   |  icon.jpg
  |   |  about.html
  |   |  help.html
  |  Dockerfile
  |  form.json
  |  LICENSE.txt
  |  manifest.json
  |  README.txt
  |  ... <custom dirs/files>
```

| Fichier | Type | Description |
| ---- | ---- |  ---------- |
| `doc/` | répertoire | contient les fichiers relatif à la présentation et à la documentation du pipeline |
| `icon.jpg` | jpg ou png | petit icon optionnel qui sera utilisé dans Regovar |
| `about.html` | html | page de présentation du pipeline |
| `help.html` | html | page d'aide du pipeline |
| `Dockerfile` | Dockerfile | fichier [docker](https://docs.docker.com/engine/reference/builder/) nécessaire pour la création de votre pipeline dockerisé |
| `form.json` | html | si votre pipeline a des paramètres configurable, vous pouvez décrire ces paramètres dans un fichier json afin que Regovar puisse permettre à l'utilisateur de les régler via un formulaire qui sera automatiquement généré depuis ce fichier json |
| `LICENSE.txt` | txt | les pipelines de Regovar étant fournis sous forme de fichier zip clés en main, il y a de forte chance qu'il puisse se retrouver très vite tout seul dans la nature. Il est donc recommandé de joindre à votre pipeline un fichier LICENSE |
| `manifest.json` | json | page d'aide du pipeline |
| `README.txt` | html | si l'installation de votre pipeline nécessite des actions particulières de la part des administrateurs. Par exemple si votre pipeline nécessite d'accéder en local à des base de données volumineuses, il vous faudra indiquer dans le README où et comment se procurer/générer ces bases. Ces bases doivent impérativement être sous forme de fichiers qui seront installés par les administrateurs et seront par la suite automatiquement accessible par votre pipeline dans son container via le répertoire DATABASES |


Seul le fichier `Dockerfile` et `manifest.json` sont obligatoire. Mais tous sont vivement recommandé afin de garantir une meilleur intégration de votre pipeline dans Regovar, et une meilleur "expérience" pour l'utilisateur.

## Le fichier manifest.json
Ce fichier décrit tout ce qui permettra à Regovar de correctement installer et utiliser votre pipeline. Ci-dessous se trouve le format attendu pour le fichier `manifest.json`:

```
{
    "name" : NAME,
    "description" : DESCRIPTION,
    "version": VERSION,
    "type": TYPE,
    "contacts" : CONTACTS,
    "regovar_db_access": DB_ACCESS,
    "inputs" : INPUTS,
    "outputs" : OUTPUTS,
    "databases": DATABASES,
    "logs" : LOGS,
}
```

| Data | Type | Description |
| ---- | ---- |  ---------- |
| NAME        | `string` | **\[obligatoire]** Votre pipeline doit impérativement avoir un nom :) |
| DESCRIPTION | `string` | Une phrase ou deux pour expliquer le but de votre pipeline (cf PRESENTATION pour une présentation plus complète de votre pipeline) |
| VERSION     | `string` | **\[obligatoire]** Ce renseignement permet de différencier et d'installer plusieurs version de votre pipeline sur un même serveur. Sans ça, il est impossible d'installer deux pipelines qui ont le même nom sur le serveur |
| TYPE | `string` | Le type de pipeline peut être `importer`, `exporter`, `reporter`, `job`. (cf la section consacré ci-dessous) |
| CONTACTS | `dict` | La liste des personnes (nom+email) à contacter en cas de problème |
| INPUTS, OUTPUTS, LOGS et DATABASES | `string` | Vous pouvez librement choisir où et comment sont nommés ces dossiers dans votre container. Ces dossiers seront alors partagés (Docker volume) et permettra au serveur Regovar et à votre pipeline de travailler correctement ensemble |
| DB_ACCESS | `bool` | `True` ou `False` (par défaut), ce booléen indique si oui ou non votre pipeline nécessite un accès à la base de donnée postgreSQL de Regovar, si oui, alors votre container sera relié à la base de donnée, et les informations de connection seront transmise à votre script |
| ICON | `string` | si vous le souhaitez, vous pouvez fournir un icone qui sera associé à votre pipeline dans Regovar |




## Les types de pipeline
Dans Regovar il existe 4 types de pipelines qui ne seront pas utilisés de la même manière, et ne seront pas présenté de la même façon à l'utilisateur.


| Type | Description |
| ---- |  ---------- |
| `job` | **\[Par défault]** Pipeline générique qui prend en entré des INPUTS et génère des OUTPUTS  |
| `importer` | Pipeline utilisé pour importer un fichier dans la base de donnée Regovar (par exemple pour parser un fichier vcf et enregistrer les variants et les annotations en base de donnée) |
| `exporter` |  Pipeline utilisé pour exporter les variants sélectionnés lors du filtrage dynamique (par exemple au format excel ou csv) |
| `reporter` | Pipeline utilisé pour générer un rapport à partir des variants sélectionnés lors du filtrage dynamiques |



## Configuration via le fichier form.json
Regovar offre à ses utilisateurs une interface simple et conviviale pour démarrer et superviser soit-même les pipelines. 

La configuration se déroule en 3 étapes :
- Choix du pipeline parmi la liste des pipelines installés sur le serveur
- Choix des fichiers sur lesquels devra travailler le pipeline.
- Configuration du pipeline via un formulaire spécifique à celui-ci

Pour cette troisième et dernière étape, les développeurs doivent fournir avec leur pipeline un fichier `form.json` qui va décrire les paramètres de ce dernier. Regovar s'occupera ensuite de générer le formulaire correspondant afin de récupérer les réglages de l'utilisateur. Ces valeurs sont ensuite stockées dans un fichier qui se nommera `config.json` et qui se trouvera dans le répertoire INPUTS du contenaire du pipeline

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

## INPUTS/config.json
Le fichier `INPUTS/config.json` sera généré par Regovar. Il permet de transmettre au pipeline, les paramètres saisie par l'utilisateur, ainsi que des paramètres techniques spécifique au serveur comme les paramètres pour se connecter à la base de donnée postgreSQL, ou bien l'url à utiliser pour les notifications en temps réel de la progression du pipeline.

Voici à quoi ressemblera le fichier `config.json` (si on considère le fichier `form.json` vu précédemment)

```
{
    "parameters":
    {
        "param1_key": 20,
        "param2_key": "",
        "param3_key": "choix 1"
        "param4_key": "default": 1.75
    },
    "regovar":
    {
        "notify_url": "http://127.0.0.1/notify/<job_id>",
        "db_host": "http://127.0.0.2",
        "db_port": "4532",
        "db_user": "regovar",
        "db_name": "regovar",
        "db_pwd": "regovar"
    }
}
```

