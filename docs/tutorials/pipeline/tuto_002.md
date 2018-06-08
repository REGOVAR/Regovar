# Packager son pipeline dans Regovar

## Qu'est-ce que l'encapsulation ?
Regovar permet d'utiliser n'importe quel pipeline bioinformatique. Pour cela, chaque pipeline doit être « packagé » d'une certaine façon. En effet, pour des raisons de sécurité et de maintenance, chaque pipeline est encapsulé dans un conteneur qui va l'isoler virtuellement du serveur. Cela va vous permettre de démarrer et de superviser l'exécution de votre pipeline.

###Technologies
L'encapsulation repose sur le concept des conteneurs. La technologie utilisée est [Docker](https://www.docker.com/what-docker). La communauté autour de cette technologie est très active, la technologie est fiable, relativement simple à utiliser et performante. De nombreux projets bioinformatiques utilisent cette technologie, comme [BioContainers](http://biocontainers.pro) ou [Bioboxes](http://bioboxes.org/), ce qui offre la possibilité de partager les outils avec ces communautés.

###Les points positifs
* Sécurité assurée et maintenance facilitée : pipeline isolé dans son conteneur, absence de risque de conflits avec les autres logiciels installés sur le serveur.
* Archivage des différentes versions des pipelines.
* Automatisation.
* Facilité d'utilisation pour les utilisateurs non experts.
* Reproductibilité de l'analyse des données.
* Interface commune pour contrôler l'ensemble des pipelines.
* Possibilité de surveiller et de contrôler l'exécution des pipelines (*logs*, *pause*, *start*, *cancel*).
* File d'attente pour l'exécution des pipelines.

###Les points négatifs
* Contraintes à respecter pour l'exécution du pipeline (API).
* Travail supplémentaire pour encapsuler son pipeline. Cela peut prendre une heure à une semaine en fonction de la complexité du pipeline.

## Arborescence du package
Votre pipeline encapsulé se présentera sous la forme d'une archive zip respectant l'arborescence suivante :

``` 
MyExamplePipeline_v1.0.0.zip
  |  doc/
  |   |  icon.jpg
  |   |  about.html
  |   |  help.html
  |  Dockerfile
  |  form.json
  |  LICENSE
  |  manifest.json
  |  README
  |  ... <custom dirs/files>
```

Le dépôt MyExamplePipeline contient les fichiers de base pour préparer l'archive zip du pipeline. Si vous le souhaitez, vous pouvez le cloner et modifier les fichiers pour les adapter à vos propres pipelines :

```sh
git clone https://github.com/REGOVAR-Pipelines/MyExamplePipeline.git
```

| Fichier | Type | Description |
| ---- | ---- |  ---------- |
| `doc/` | répertoire | Contient les fichiers relatif à la présentation et à la documentation du pipeline. |
| `icon.jpg` | jpg ou png | Petite icône optionnelle qui sera affichée dans Regovar. |
| `about.html` | html | Page de présentation du pipeline. |
| `help.html` | html | Page d'aide du pipeline. |
| `Dockerfile` | [Dockerfile](https://docs.docker.com/engine/reference/builder/) | Fichier docker nécessaire pour la création de votre pipeline dockerisé. |
| `form.json` | json | Si votre pipeline a des paramètres configurables, vous pouvez décrire ces paramètres dans un fichier json afin que Regovar puisse permettre à l'utilisateur de les régler via un formulaire qui sera automatiquement généré depuis ce fichier json. |
| `LICENSE` | txt | Licence de votre pipeline, par exemple [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.fr.html). |
| `manifest.json` | json | Page d'aide du pipeline. |
| `README` | txt | Si l'installation de votre pipeline nécessite des actions particulières de la part des administrateurs. Par exemple, si votre pipeline nécessite d'accéder en local à des base de données volumineuses, il vous faudra indiquer dans le README où et comment se procurer/générer ces bases. Ces bases doivent impérativement être sous forme de fichiers qui seront installés par les administrateurs et seront par la suite automatiquement accessibles par votre pipeline dans son conteneur via le répertoire DATABASES. |

Seuls les fichiers `Dockerfile`, `manifest.json` et `LICENSE` sont obligatoires, mais tous sont vivement recommandés afin de garantir une meilleure intégration de votre pipeline dans Regovar et une meilleure expérience pour l'utilisateur.

## Le fichier manifest.json
Ce fichier décrit tout ce qui va permettre à Regovar de correctement installer et utiliser votre pipeline. Ci-dessous se trouve le format attendu pour le fichier `manifest.json` :

```
{
    "name" : NAME,
    "description" : DESCRIPTION,
    "version": VERSION,
    "type": TYPE,
    "contacts" : CONTACTS,
    "inputs" : INPUTS,
    "outputs" : OUTPUTS,
    "logs" : LOGS,
    "databases": DATABASES,
    "regovar_db_access": DB_ACCESS,
}
```

| Data | Type | Description |
| ---- | ---- |  ---------- |
| NAME        | `string` | **\[obligatoire]** Votre pipeline doit impérativement avoir un nom. :) |
| DESCRIPTION | `string` | Une phrase ou deux pour expliquer le but de votre pipeline (cf. `help.html` pour une présentation plus complète de votre pipeline). |
| VERSION     | `string` | **\[obligatoire]** Ce renseignement permet de différencier et d'installer plusieurs versions de votre pipeline sur un même serveur. Sans cela, il est impossible d'installer deux pipelines qui ont le même nom sur le serveur. Il est conseillé d'utiliser les numéros de version en suivant les recommandations [SemVer](https://semver.org/), tels que `"1.0.0"`. |
| TYPE | `string` | Le type de pipeline peut être `job` **\[par défaut]**, `importer`, `exporter` ou `reporter` (cf. [section consacrée ci-dessous](tuto_002.md#les-types-de-pipelines)). |
| CONTACTS | `list` | Liste des personnes (identité + email) à contacter en cas de problème. |
| INPUTS, OUTPUTS, LOGS et DATABASES | `string` | Vous pouvez librement choisir où et comment sont nommés ces répertoires dans votre conteneur. Ces répertoires seront alors partagés, c'est-à-dire accessibles depuis plusieurs conteneurs différents (*Docker volume*), et permettront au serveur Regovar et à votre pipeline de travailler correctement ensemble. |
| DB_ACCESS | `bool` | `true` ou `false` **\[par défaut]**, ce booléen indique si oui ou non, votre pipeline nécessite un accès à la base de données PostgreSQL de Regovar. Si oui, alors votre conteneur sera relié à la base de données et les informations de connexion seront transmises à votre script. |

## Les types de pipelines
Dans Regovar il existe quatre types de pipelines qui ne seront pas utilisés de la même manière et ne seront pas présentés de la même façon à l'utilisateur.

| Type | Description |
| ---- |  ---------- |
| `job` | **\[Par défaut]** Pipeline générique qui prend en entrée des fichiers dans INPUTS et génère des fichiers dans OUTPUTS (exemple : FASTQ en entrée et VCF en sortie).  |
| `importer` | Pipeline utilisé pour importer un fichier dans la base de données Regovar (par exemple pour parser un fichier VCF et enregistrer les variants et les annotations en base de données). |
| `exporter` |  Pipeline utilisé pour exporter les variants sélectionnés lors du filtrage dynamique (par exemple au format Excel ou CSV). |
| `reporter` | Pipeline utilisé pour générer un rapport d'analyse à partir des variants sélectionnés lors du filtrage dynamique. |

## Le fichier form.json (optionnel)
Ce fichier optionnel `form.json` est utile pour les pipelines configurables.

Regovar offre à ses utilisateurs une interface simple et conviviale pour démarrer et superviser soi-même les pipelines. 

La configuration se déroule en trois étapes :
- choix du pipeline parmi la liste des pipelines installés sur le serveur ;
- choix des fichiers sur lesquels devra travailler le pipeline ;
- configuration du pipeline via un formulaire spécifique à celui-ci.

Pour cette troisième et dernière étape, les développeurs doivent fournir avec leur pipeline un fichier `form.json` qui va décrire les paramètres du pipeline. Regovar pourra grâce à celui-ci générer le formulaire correspondant afin de récupérer les réglages de l'utilisateur. Ces valeurs sont stockées dans un fichier qui se nommera [`config.json`](tuto_002.md#inputsconfigjson) et qui se trouvera dans le répertoire INPUTS du conteneur du pipeline.

L'exemple ci-dessous montre la structure attendue pour le fichier `form.json` ainsi que les différents types de paramètres supportés.
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
            "description": "Les types integer pour les entiers et number pour les réels (float)",
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

Pour saisir des réels (float).
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

Pour saisir du texte (string).
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

Pour proposer une liste à choix unique (liste de strings).
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

Pour les enum, vous pouvez soit proposer une liste de valeurs manuellement comme dans l'exemple, soit opter pour les listes générées automatiquement grâce aux mots-clés suivants :

- `__INPUTS_FILES__` va générer la liste des fichiers qui ont été sélectionnés lors de l'étape précédente de la configuration du pipeline. Cela permet ainsi de pouvoir sélectionner un fichier en particulier parmi plusieurs et de l'indiquer au pipeline.
```
    "enum": "__INPUTS_FILES__",
```

- `__GENOMES_REFS__` va générer la liste des génomes de références (par exemple hg19 ou hg38) qui ont été installés sur le serveur et dont les fichiers et bases de données associés seront accessibles par le pipeline via le répertoire DATABASES.
```
    "enum": "__GENOMES_REFS__",
```

## Le fichier Dockerfile

Dockeriser un pipeline est une tâche dont la complexité dépend largement de votre pipeline. Nous vous conseillons de lire la [documentation de Docker](https://docs.docker.com/engine/reference/builder/). En cas de besoin, vous pouvez demander de l'aide sur leur forum ou sur le forum [Biostars](https://www.biostars.org/). Nous vous recommandons aussi de partir d'une [image docker biocontainers de base](https://hub.docker.com/u/biocontainers/) qui correspond le mieux à votre pipeline afin de vous faciliter le travail.
Le tutoriel ci-dessous présente un exemple d'encapsulation de pipeline. Vous trouverez un autre exemple dans la suite de cette documentation : [exemple de pipeline non paramétrable](tuto_004.md).

###Termes utilisés
- Nous appellons HOST, le serveur sur lequel Docker est installé et sur lequel la machine virtuelle est déployée.
- Nous appellons CONTAINER, la machine virtuelle qui contient et exécute votre pipeline.

###Commandes de base de Docker
Résumé des commandes Docker qui peuvent vous servir :

```
docker run             # Télécharger et déployer une nouvelle machine virtuelle avec un OS de base prêt à l'emploi
docker exec            # Exécuter une commande dans la machine virtuelle depuis le serveur
docker ls              # Donner la liste des CONTAINERS actuellement déployés sur votre HOST
docker rm              # Désinstaller et supprimer un CONTAINER
docker stop            # Stopper brutalement l'exécution d'un CONTAINER (équivaut à éteindre votre PC)
docker pause           # Suspendre l'exécution d'un CONTAINER (sauvegarde l'état de sa RAM)
docker start           # Démarrer ou reprendre l'éxécution d'un CONTAINER qui a été freezé

docker add             # Copier un fichier de votre HOST vers un CONTAINER
lxc file pull          # Copier un fichier de votre CONTAINER vers le HOST

$ docker image ls      # Lister les images installées sur votre HOST
$ docker rmi           # Supprimer une image
$ docker image export  # Exporter une image au format tar.gz
$ docker image import  # Installer une image au format tar.gz sur votre HOST

```

À chaque étape de votre processus de dockerisation, vous pouvez tester votre pipeline en suivant les instructions ci-dessous.

###Testez votre Dockerfile

Pour tester votre Dockerfile, il est indispensable de travailler sur un ordinateur où est installé Docker.

**1.** Placez-vous dans le répertoire où se trouve le Dockerfile
**2.** Construisez l'image du conteneur. Cela utilise le Dockerfile que vous avez préparé. Vous pouvez donner le nom que vous souhaitez à l'image, par exemple ici `my_example_pipeline`.
    
```sh
docker build -t my_example_pipeline .
```
**3.** Exécutez votre pipeline en remplaçant les variables ci-dessous par celles de votre pipeline.

```sh
docker run -a stdin -a stdout -it -v INPUTS_SUR_LE_HOST:INPUTS_SUR_LE_CONTAINER:ro -v OUTPUTS_SUR_LE_HOST:OUTPUTS_SUR_LE_CONTAINER -v DATABASES_SUR_LE_HOST:DATABASES_SUR_LE_CONTAINER:ro -v /tmp/logs:/LOGS --name NOM_CONTAINER --user $(id -u):$(id -g) NOM_IMAGE
```

Par exemple, pour tester MyExamplePipeline, nous vous proposons d'utiliser les répertoires `/tmp/inputs`, `/tmp/outputs`, `/tmp/databases` et `/tmp/logs` du HOST comme répertoires d'entrée, de sortie, de bases de données et de logs respectivement :

```sh
docker run -a stdin -a stdout -it -v /tmp/inputs:/regovar/inputs:ro -v /tmp/outputs:/regovar/outputs -v /tmp/databases:/regovar/databases:ro -v /tmp/logs:/regovar/logs --name regovar_test --user $(id -u):$(id -g) my_example_pipeline
```

**4.** Vérifier que tout se déroule correctement et que le résultat est correctement généré dans le répertoire `OUTPUTS_SUR_LE_HOST` (`/tmp/outputs`) du HOST.

Si vous souhaitez supprimer le conteneur après le test, vous pouvez exécuter : `docker rm NOM_CONTAINER` (`docker rm regovar_test`)


## Le zip du package

Une fois ces fichiers préparés, zippez-les ensemble pour construire le package :

```sh
zip -r MyExamplePipeline_v1.0.0.zip MyExamplePipeline_v1.0.0/*
```

Il ne vous reste plus qu'à télécharger votre archive sur le serveur Regovar et à l'[installer](tuto_001.md).

## INPUTS/config.json
Le fichier `INPUTS/config.json` sera généré par Regovar pour tous les types de pipelines. Il permet de transmettre au pipeline les paramètres saisis par l'utilisateur, ainsi que des paramètres techniques spécifiques au serveur comme les paramètres pour se connecter à la base de données PostgreSQL, ou bien l'URL à utiliser pour les notifications en temps réel de la progression du pipeline.

Voici à quoi ressemble le fichier `config.json` (si on considère le fichier `form.json` vu précédemment).

```
{
    "parameters":
    {
        "param1_key": 20,
        "param2_key": "",
        "param3_key": "choix 1",
        "param4_key": 1.75
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
