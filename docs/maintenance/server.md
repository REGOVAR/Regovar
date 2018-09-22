# Maintenance du serveur

## Mise à jour du serveur
Pour mettre à jour le serveur dans le cas où vous utilisez une installation via SaltStack, nous vous invitons à suivre les instructions sur le [README.md](https://github.com/REGOVAR/ServerConfiguration/blob/master/README.md#update-the-computer-and-the-configuration-as-root-on-debian-or-ubuntu)

## Mise à jour de la base de données
Il faut également mettre à jour la base de données. Vous trouverez la liste des mises à jour dans `Regovar/install/updates`.

```sh
psql -U $DATABASE_USERNAME -d $DATABASE_NAME -f "Regovar/install/updates/6.5 to 6.6.sql"
``` 
Par défaut :
- `$DATABASE_NAME` est `regovar`
- `$DATABASE_USERNAME` est `regovar`

## Changement du message du serveur
Vous pouvez changer le message de bienvenue du serveur. Ce message peut être affiché par le client lorsque celui-ci se connecte.

```sh
MESSAGE='{"type":"info", "message": "Bienvenue sur le serveur!"}'
psql -U $DATABASE_USERNAME -d $DATABASE_NAME -c "UPDATE parameter SET value='$MESSAGE' WHERE key='message';"
```
Par défaut :
- `$DATABASE_NAME` est `regovar`
- `$DATABASE_USERNAME` est `regovar`
