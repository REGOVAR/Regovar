# Compilation du client QRegovar

## Sur Windows

Vous avez besoin de Qt 5.10.1. ou d'une version supérieure.

Pour cela, téléchargez le paquet open source sur le [site Internet de Qt](https://www.qt.io/download). Suivez les instructions pour l'installer.

QtCreator demande de configurer le projet. Acceptez les paramètres par défaut.

Ouvrez le projet `app/QRegovar.pro` avec QtCreator and et lancez la compilation de QRegovar (raccourci `ctrl + R`).

## Sur Ubuntu 16.04 LTS (Xenial) et 18.04 LTS (Bionic)

Vous avez besoin de quelques packages Qt 5.10 (ou version supérieure), qui ne sont pas encore distribués avec le dépôt officiel d'Ubuntu (notez qu'en procédant ainsi, vous faites confiance à [Stephan Binner](https://launchpad.net/~beineri) qui fournit gentiment les packages compilés):

```sh
sudo add-apt-repository ppa:beineri/opt-qt-5.11.0-$(lsb_release -cs)
sudo apt install qt511charts-no-lgpl qt511graphicaleffects qt511quickcontrols qt511quickcontrols2 qt511websockets
```

Ensuite, créez l'envirtonnement Qt pour compiler QRegovar:

```sh
source /opt/qt511/bin/qt511-env.sh
```

### Sans QtCreator

Compilation:

```sh
cd app
qmake
make
```

Lancement de QRegovar:

```sh
./QRegovar
```

### En utilisant QtCreator

Si vous n'avez pas encore QtCreator, vous devez l'installer :

```sh
sudo apt install qt511creator
```

Lancement de QtCreator:

```sh
qtcreator
```

QtCreator demande de configurer le projet. Acceptez les paramètres par défaut.

Ouvrez le projet `app/QRegovar.pro` avec QtCreator and et lancez la compilation de QRegovar (raccourci `ctrl + R`).

## Sur ArchLinux

Téléchargez les dépendances :

```sh
sudo pacman -S qt5-quickcontrols2 qt5-charts qt5-graphicaleffects qt5-websockets
```

Compilation :

```sh
cd app
qmake
make
```

Lancement de QRegovar:

```sh
./QRegovar
```