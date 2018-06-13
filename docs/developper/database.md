## Vue d'ensemble
* Technologie [PostgresSQL 9.6](https://www.postgresql.org/docs/9.6/static/index.html)
* [Python SQLAlchemy](http://docs.sqlalchemy.org/en/latest/orm/) pour l'ORM python
* Vous trouverez tous les scripts d'installation SQL dans le dossier `install/`
* On crée d'abord la base de données avec les scripts SQL puis l'ORM Python crée les objets Pythons correspondants (et non l'inverse comme c'est souvent le cas)
* Les classes Pythons correspondants aux tables SQL se trouvent dans `regovar/core/model/`

## Schema
[![Database schema of Regovar](https://raw.githubusercontent.com/REGOVAR/Regovar/master/docs/assets/img/db_schema.png)](https://raw.githubusercontent.com/REGOVAR/Regovar/master/docs/assets/img/db_schema.png)
