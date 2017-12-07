## Vue d'ensemble
* Technologie [PostgresSQL 9.6](https://www.postgresql.org/docs/9.6/static/index.html);
* [Python SqlAlchemy](http://docs.sqlalchemy.org/en/latest/orm/) pour l'ORM python;
* Vous trouverez tout les scripts d'installation sql dans le dossier `install/`;
* On crée d'abord la base de donnée avec les scripts SQL puis ensuite l'ORM python crée les objets pythons correspondant (et non l'inverse comme c'est souvent le cas)
* Les classes pythons correspondant aux tables SQL se trouvent dans `regovar/core/model/`

## Schema
[![Database schema of Regovar](https://raw.githubusercontent.com/REGOVAR/Regovar/master/docs/assets/img/db_schema.png)](https://raw.githubusercontent.com/REGOVAR/Regovar/master/docs/assets/img/db_schema.png)
