
# Installation du client

Le client lourd de Regovar est compatible pour Windows, Linux et macOS.

Actuellement, seules les versions pour Windows, pour Debian et Ubuntu sont prépackagées, mais vous pouvez [compiler l'application](https://regovar.readthedocs.io/fr/latest/developper/client_compilation/) pour d'autres systèmes d'exploitation avec qmake ou QtCreator. Des versions prépackagées pour ArchLinux et macOS sont en préparation et seront prochainement disponibles !

## Installation
###  Pour Windows
Pour l'installer, rien de plus simple, il vous suffit de vous rendre sur [GitHub](https://github.com/REGOVAR/QRegovar/releases) et de choisir le zip qui correspond à votre système d'exploitation. Une fois l'archive dézipée, il n'y a plus qu'à double cliquer sur l'exécutable « QRegovar.exe » et l'application se lance. 

### Pour Debian (Stretch/9) et Ubuntu (Xenial/16.04 et Bionic/18.04)
```sh
curl -s https://arkanosis.net/jroquet.pub.asc | sudo apt-key add -
echo "deb https://apt.regovar.org/ software stable" | sudo tee /etc/apt/sources.list.d/regovar.list
sudo apt update
sudo apt install qregovar
```
Pour le lancer
```sh
qregovar
```

## Première utilisation
Pour la première fois, le client va automatiquement se connecter sur le serveur public de test : [test.regovar.org](http://test.regovar.org). Allez dans Settings > Application > Connection, pour modifier l'adresse du serveur (nécessite de redémarrer l'application).

Vous pouvez ensuite vous connecter au serveur de test en utilisant le nom d'utilisateur « admin », sans mot de passe.