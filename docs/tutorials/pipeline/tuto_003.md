# Créer un pipeline pour Regovar avec LXD

Ce tutoriel présente tout ce qu'il faut connaitre sur la technologie LXC/LXD pour encapsuler son pipeline. 

## La base LXC

- Pour ce qui ne connaissent pas LXC/LXD, ou savoir comment l'installer, il est recommandé de lire [la doc officielle](https://linuxcontainers.org/lxd/getting-started-cli/) avant de commencer
- Nous appellons HOST, le serveur sur lequel vous installé LXC/LXD et sur lequel est déployé la machine virtuelle
- Nous appellons CONTAINER, la machine virtuelle.

Résumé des commandes LXD qui vont nous servir

```

$ lxc launch        # Télécharge et déployer une nouvelle machine virtuelle avec un OS de base prêt à l'emploi
$ lxc exec          # Exécuter une commande dans la machine virtuelle depuis le serveur
$ lxc list          # Donne la liste des CONTAINERS actuellement déployés sur votre HOST
$ lxc delete        # Désinstalle et supprime un CONTAINER
$ lxc stop          # Stop "brutalement" l'exécution d'un CONTAINER (équivalent à éteindre votre PC)
$ lxc freeze        # Suspens l'exécution d'un CONTAINER (sauvegarde l'état de sa RAM etc)
$ lxc start         # Démarrer ou reprend l'éxécution d'un CONTAINER qui a été freeze
$ lxc publish       # Crée une image de votre CONTAINER afin de faciliter son déploiement sur d'autre HOST

lxc file push       # Copie un fichier de votre HOST vers un CONTAINER
lxc file pull       # Copie un fichier de votre CONTAINER vers l'HOST

$ lxc image list    # Donne la liste des images installées sur votre HOST
$ lxc image delete  # Supprime une image
$ lxc image export  # Exporte une image au format tar.gz
$ lxc image import  # Installe une image au format tar.gz sur votre HOST

```

## Les recommandations et contraintes
En plus des respecter les [exigences de base](tuto_002.md#exigences-et-options) de regovar, le CONTAINER utilisant LXC doivent avoir d'installé le paquet `curl`afin de permettre au CONTAINER de notifier Regovar quand le pipeline démarre et se termine.




## Prérequis
- Dans l'idéal, vous travaillez sur un ordinateur (LOCAL) où sont installé et fonctionnent parfaitement LXC/LXD et votre pipeline.
- Vous avez identifier localement les répertoires INPUTS, OUTPUTS, LOGS et DATABASES pour votre pipeline.
  - Votre pipeline est capable de récupérer si besoin ses paramètres depuis un fichier `config.json` qui se trouve dans le répertoire INPUTS
  - Votre pipeline s'attends à trouver les fichiers à analyser dans le réperoire INPUTS (à noter que ce répertoire sera en read-only dans le container. Il ne faut donc pas que votre pipeline essaye d'écrire quoi que ce soit dedans)
  - Votre pipeline produit ses résultats dans le répertoire OUTPUTS
  - Les logs de votre pipeline sont placés dans le répertoire LOGS

## INPUTS/config.json et notification temps-réel
Le fichier config.
Si vous voulez que la progression de votre pipeline soit mis à jour en temps réel, il faut que votre pipeline récu

## Procédure
```
# Création du CONTAINER
lxc launch images:ubuntu/xenial mypipelineVM

# Démarrer la console en mode interractif sur le conteneur
lxc exec mypipelineVM /bin/bash

# Création des dossiers imposés par l'API Regovar
mkdir -p /pipeline/{job,inputs,outputs,logs,db}

# Installation des paquets nécessaires au pipeline et à Regovar
apt install curl ... --fix-missing
exit # sortir du container

# Copier le pipeline dans le CONTAINER
lxc image push LOCAL/mypeline/* mypipelineVM/pipeline/job/*

# Tester votre pipeline dans votre container afin de vérifier qu'il fonctionne:
# Copier si besoin des fichiers d'entrées
lxc file push LOCAL/inputsTests/* mypipelineVM/INPUTS/*
lxc file push LOCAL/configTest/config.json mypipelineVM/INPUTS/config.json

# Exécuter la ligne de commande JOB
lxc exec mypipelineVM JOB

# Vérifier les fichiers produits par votre pipeline
lxc exec mypipelineVM ls -la OUTPUTS

# Vérifier les logs produits par votre pipeline
lxc exec mypipelineVM ls -la LOGS

# Nettoyer votre container (il convient d'alléger au maximum votre image)
lxc exec mypipelineVM rm -Rf INPUTS/*
lxc exec mypipelineVM rm -Rf OUTPUTS/*
lxc exec mypipelineVM rm -Rf LOGS/*
lxc exec mypipelineVM rm -Rf /tmp/*

# Créer une image LXC depuis votre Container
lxc stop mypipelineVM
lxc publish mypipelineVM --alias=MyPipelineV1.0
lxc image export MyPipelineV1.0 # celà va vous créer un fichier du genre <a8d44d24fcs...8fzef54e5>.tar.gz

# Création du package final
mkdir MyPipeline
mv <a8d44d24fcs...8fzef54e5>.tar.gz MyPipeline/lxc_image.tar.gz

# Ajouter dans le répertoire MyPipeline le fichier manifest.json, form.json, LICENSE, README, ... 

# Créer le zip final
zip -r  MyPipelineV1.0.zip MyPipeline/*
exit
```
Et voilà il ne vous reste plus qu'à télécharger votre archive sur le serveur Regovar et à [l'installer](tuto_001.md)


 
