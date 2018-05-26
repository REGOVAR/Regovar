# Installer un pipeline dans Regovar

Ce tutoriel présente comment installer un pipeline déjà existant dans Regovar.
Si vous voulez packager votre propre pipeline, veuillez vous référer au tutoriel suivant : [packager son pipeline](tuto_002.md).

## Installation manuelle depuis le serveur via la console

### Prérequis
* Le pipeline est correctement packagé pour Regovar et vous n'avez plus qu'à le déployer sur le serveur Regovar.
* Vous êtes connecté sur le serveur avec l'utilisateur et les droits suffisants pour exécuter les commandes shell de l'application Regovar.

### Procédure
```
$ regovar pipeline install path/to/my_pipeline_package.zip
```

