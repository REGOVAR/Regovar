# Packager son pipeline dans Regovar (partie 2/2 : encapsulation du pipeline avec Docker)

Une fois les notions de base assimilées, voyons les différentes étapes pour encapsuler son pipeline (de type `job`).


## La base Docker

- Pour ce qui ne connaissent pas Docker ou pour savoir comment l'installer, merci de vous référer à [la documentation officielle](https://docs.docker.com/get-started/)
- Nous appellons HOST, le serveur sur lequel Docker est installé et sur lequel la machine virtuelle est déployée.
- Nous appellons CONTAINER, la machine virtuelle (qui contient et execute votre pipeline).
- Nous appellons PACKAGE le fichier zip à produire pour utiliser votre pipeline dans Regovar.

Résumé des commandes Docker qui peuvent nous servir :

```
docker run             # Télécharger et déployer une nouvelle machine virtuelle avec un OS de base prêt à l'emploi
docker exec            # Exécuter une commande dans la machine virtuelle depuis le serveur
docker ls              # Donner la liste des CONTAINERS actuellement déployés sur votre HOST
docker rm              # Désinstaller et supprimer un CONTAINER
docker stop            # Stopper brutalement l'exécution d'un CONTAINER (équivalent à éteindre votre PC)
docker pause           # Suspendre l'exécution d'un CONTAINER (sauvegarde l'état de sa RAM, etc.)
docker start           # Démarrer ou reprendre l'éxécution d'un CONTAINER qui a été freezé

docker add             # Copier un fichier de votre HOST vers un CONTAINER
lxc file pull          # Copier un fichier de votre CONTAINER vers l'HOST

$ docker image ls      # Donner la liste des images installées sur votre HOST
$ docker rmi           # Supprimer une image
$ docker image export  # Exporter une image au format tar.gz
$ docker image import  # Installer une image au format tar.gz sur votre HOST

```


## Prérequis
- Vous travaillez sur un ordinateur (LOCAL) où est installé Docker.
- Vous avez dockerisé votre pipeline grâce à un fichier `Dockerfile`.
- Vous avez identifié dans le CONTAINER les répertoires INPUTS, OUTPUTS, LOGS et DATABASES pour votre pipeline.
  - Votre pipeline est capable de récupérer si besoin ses paramètres depuis un fichier `config.json` qui se trouve dans le répertoire INPUTS
  - Votre pipeline s'attend à trouver les fichiers à analyser dans le réperoire INPUTS (à noter que ce répertoire sera en read-only dans le conteneur. Il ne faut donc pas que votre pipeline essaye d'écrire quoi que ce soit dedans).
  - Votre pipeline produit ses résultats dans le répertoire OUTPUTS.
  - Les logs de votre pipeline sont placés dans le répertoire LOGS.

**Comment « dockeriser » mon pipeline ?**

Malheureusement, nous ne pouvons pas traiter cette partie ici. C'est la tâche la plus compliquée et qui dépend largement de votre pipeline. Pour cela, nous vous conseillons d'abord de lire la [documentation de Docker](https://docs.docker.com/engine/reference/builder/) et de demander de l'aide sur leur forum ou sur le forum [biostars](https://www.biostars.org/). Nous vous recommandons aussi de partir d'une [image docker biocontainers de base](https://hub.docker.com/u/biocontainers/) qui correspond le mieux à votre pipeline afin de vous faciliter le travail. Enfin, vous pouvez vous inspirer de notre tutoriel qui présente l'encapsultation de pipeline pas à pas : [Exemple de pipeline non paramétrable](tuto_004.md)

## Procédure

**1.** Commencez par créer le dossier `mypipeline_v1.0`qui va contenir toutes données nécessaire à la création du pipeline. (cf [exigences de base](tuto_002.md#exigences-et-options))
```
MyPipeline_v1.0/
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

**2.** Tester votre PACKAGE. 
   - Créer un répertoire `/tmp/inputs/` avec dedans vos fichiers de tests (et un fichier `config.json` [si besoin](tuto_002.md#inputsconfigjson))
   - Placez-vous à la racine de votre dossier PACKAGE
   - Construisez l'image du container
    
```
docker build -t regovar_pipe_test .
```
   - Executez votre pipeline
```
docker run -a stdin -a stdout -it -v /tmp/inputs:/INPUTS:ro -v /tmp/outputs:/OUTPUTS -v /var/regovar/databases:/DATABASES:ro -v /tmp/logs:/LOGS --network regovar_net --name regovar_test --user 1000:1000 regovar_pipe_test
```

**3.** Vérifier que tout se déroule correctement et que le résultat est correctement généré dans le répertoire /tmp/outputs du HOST. En cas de problème, supprimez le container `docker rm regovar_test --force` et recommancez l'étape 2.

**4.** Créez le zip du PACKAGE
```
zip -r MyPipeline_v1.0.zip MyPipeline_v1.0
```

Et voilà il ne vous reste plus qu'à télécharger votre archive sur le serveur Regovar et à [l'installer](tuto_001.md)


 
