# Packager son pipeline dans Regovar (notions de base)

## Qu'est-ce que l'encapsulation ?
Regovar permet d'utiliser n'importe quel pipeline bioinformatique. Pour cela, chaque pipeline doit être « packagé » d'une certaine façon. En effet, pour des raisons de sécurité et de maintenance, chaque pipeline est encapsulé dans un conteneur qui va l'isoler virtuellement du serveur. Cela va vous permettre de démarrer et de superviser l'exécution de votre pipeline.

###Technologies
L'encapsulation repose sur le concept des conteneurs. La technologie utilisé est [Docker](https://www.docker.com/what-docker). Docker a été choisi parce que la communauté autour de cette technologie est très active, la technologie est fiable, relativement simple à utiliser et performante. De nombreux projets bioinformatiques utilisent cette technologie, comme [BioContainers](http://biocontainers.pro) ou [Bioboxes](http://bioboxes.org/), ce qui offre la possibilité de partager les outils avec ces communautés.

###Les points positifs
* Sécurité assurée et maintenance facilitée : chaque pipeline est isolé dans son conteneur, absence de risque de conflits avec les autres logiciels installés sur le serveur.
* Archivage des différentes versions des pipelines.
* Automatisation.
* Facilité d'utilisation pour les utilisateurs non experts.
* Reproductibilité de l'analyse des données.
* Interface commune pour contrôler tous les pipelines.
* Possibilité de surveiller et de contrôler l'exécution des pipelines (logs, pause, start, cancel).
* File d'attente pour l'exécution les pipelines.

###Les points négatifs
* Contrainte à respecter pour l'exécution du pipeline (API).
* Travail supplémentaire pour encapsuler son pipeline. Cela peut prendre 1/2 à 1 journée en fonction des problèmes rencontrés.

## Exigences et options
Votre pipeline encapsulé se présentera sous la forme d'une archive zip respectant l'arborescence suivante :

```
MyPipeline_v1.0.0.zip
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

| Fichier | Type | Description |
| ---- | ---- |  ---------- |
| `doc/` | répertoire | Contient les fichiers relatif à la présentation et à la documentation du pipeline. |
| `icon.jpg` | jpg ou png | Petite icône optionnelle qui sera affichée dans Regovar. |
| `about.html` | html | Page de présentation du pipeline. |
| `help.html` | html | Page d'aide du pipeline. |
| `Dockerfile` | Dockerfile | Fichier [docker](https://docs.docker.com/engine/reference/builder/) nécessaire pour la création de votre pipeline dockerisé. |
| `form.json` | json | Si votre pipeline a des paramètres configurables, vous pouvez décrire ces paramètres dans un fichier json afin que Regovar puisse permettre à l'utilisateur de les régler via un formulaire qui sera automatiquement généré depuis ce fichier json. |
| `LICENSE` | txt | Licence de votre pipeline, par exemple [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.fr.html). |
| `manifest.json` | json | Page d'aide du pipeline. |
| `README` | txt | Si l'installation de votre pipeline nécessite des actions particulières de la part des administrateurs. Par exemple, si votre pipeline nécessite d'accéder en local à des base de données volumineuses, il vous faudra indiquer dans le README où et comment se procurer/générer ces bases. Ces bases doivent impérativement être sous forme de fichiers qui seront installés par les administrateurs et seront par la suite automatiquement accessibles par votre pipeline dans son conteneur via le répertoire DATABASES. |

Seuls les fichiers `Dockerfile`, `manifest.json` et `LICENSE` sont obligatoires, mais tous sont vivement recommandés afin de garantir une meilleure intégration de votre pipeline dans Regovar et une meilleure expérience pour l'utilisateur.

## Le fichier manifest.json
Ce fichier décrit tout ce qui permettra à Regovar de correctement installer et utiliser votre pipeline. Ci-dessous se trouve le format attendu pour le fichier `manifest.json` :

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
| VERSION     | `string` | **\[obligatoire]** Ce renseignement permet de différencier et d'installer plusieurs versions de votre pipeline sur un même serveur. Sans cela, il est impossible d'installer deux pipelines qui ont le même nom sur le serveur. Il est conseillé d'utiliser les numéros de version en suivant les recommandations [SemVer](https://semver.org/). tels que `"1.0.0"`. |
| TYPE | `string` | Le type de pipeline peut être `job` **\[par défaut]**, `importer`, `exporter`, `reporter` (cf. [section consacrée ci-dessous](tuto_002.md#les-types-de-pipelines). |
| CONTACTS | `list` | Liste des personnes (identité + email) à contacter en cas de problème. |
| INPUTS, OUTPUTS, LOGS et DATABASES | `string` | Vous pouvez librement choisir où et comment sont nommés ces répertoires dans votre conteneur. Ces répertoires seront alors partagés (Docker volume) et permettront au serveur Regovar et à votre pipeline de travailler correctement ensemble. |
| DB_ACCESS | `bool` | `true` ou `false` **\[par défaut]**, ce booléen indique si oui ou non votre pipeline nécessite un accès à la base de données PostgreSQL de Regovar. Si oui, alors votre conteneur sera relié à la base de données et les informations de connexion seront transmise à votre script. |

## Les types de pipelines
Dans Regovar il existe quatre types de pipelines qui ne seront pas utilisés de la même manière, et ne seront pas présenté de la même façon à l'utilisateur.

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

Pour cette troisième et dernière étape, les développeurs doivent fournir avec leur pipeline un fichier `form.json` qui va décrire les paramètres de ce dernier. Regovar s'occupera ensuite de générer le formulaire correspondant afin de récupérer les réglages de l'utilisateur. Ces valeurs sont stockées dans un fichier qui se nommera `config.json` et qui se trouvera dans le répertoire INPUTS du conteneur du pipeline.

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
            "description": "Les types integer pour les entiers, et number pour les réels (float)",
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

Pour les enum, vous pouvez soit proposer une liste de valeurs manuellement comme dans l'exemple, soit opter pour les listes générées automatiquement grâce aux mots clés suivant :

- `__INPUTS_FILES__` va générer la liste des fichiers qui ont été sélectionnés lors de l'étape précédente de la configuration du pipeline. Cela permet ainsi de pouvoir sélectionner un fichier en particulier parmi plusieurs et de l'indiquer au pipeline.
```
    "enum": "__INPUTS_FILES__",
```

- `__GENOMES_REFS__` va générer la liste des génomes de références (hg19, hg38, ...) qui ont été installés sur le serveur et dont les fichiers et bases de données associés seront accessibles par le pipeline via le répertoire DATABASES.
```
    "enum": "__GENOMES_REFS__",
```

## INPUTS/config.json
Le fichier `INPUTS/config.json` sera généré par Regovar pour tous les types de pipelines. Il permet de transmettre au pipeline les paramètres saisis par l'utilisateur, ainsi que des paramètres techniques spécifiques au serveur comme les paramètres pour se connecter à la base de données PostgreSQL, ou bien l'URL à utiliser pour les notifications en temps réel de la progression du pipeline.

Voici à quoi ressemblera le fichier `config.json` (si on considère le fichier `form.json` vu précédemment).

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

## Le fichier Dockerfile

Pour créer le fichier Dockerfile, nous vous invitons à poursuivre la lecture de la documentation qui va vous expliquer comment créer un pipeline pour Regovar avec Docker.
