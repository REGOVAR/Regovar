# Maintenance du serveur


Vous trouverez la liste des updates dans `Regovar/install/updates`.
Pour mettre à jour le serveur :

```sh
psql -U $DATABASE_USERNAME -d $DATABASE_NAME -f "Regovar/install/updates/6.5 to 6.6.sql"
``` 

Par défaut, `$DATABASE_NAME` est `regovar` et `$DATABASE_USERNAME` est `regovar`.
