API REST : Vue d'ensemble
=========================

Le server Regovar expose une API Rest via aioHTTP. Tout le code concernant l'API se trouve dans le répertoire `/regovar/web`. L'API permet d'accéder et de gérer les resources de Regovar ainsi que de réaliser toute les fonctionnalités proposée par le server via une interface web. 

Pour connaître les détails concernant les resources et fonctionnalités de Regovar, lire la [section concernant le `core`]()



Principaux points d'entrés
==========================
Les points d'entrés principaux de l'API sont les suivants :
 * [`/users`]() : pour la manipulation des utilisateurs de Regovar
 * [`/projects`]() : pour la manipulation des projets de Regovar
 * *... à venir ...*


Règles générales
================

CRUD
----
```
	GET 	Read
	POST	Create
	PUT 	Update
	DELETE	Delete
```




Réponses et prise en charge des erreurs
---------------------------------------
Les seuls codes d'erreur HTTP retournés par le server sont :
| Code | Description |
|------| ----------- |
|`200` | *"OK"*, le server fonctionne bien et vous a répondu (ce qui ne veut pas dire qu'il n'y a pas eu d'erreur)|
|`404` | *"request not found"*, l'url saisie n'existe pas |
|`403` |*"authentication required"*, l'utilisateur doit être identifié pour accéder au service, ou bien l'authentification a échoué (mauvais login/mot de passe saisis)|
|`5XX` | *"server errors"*, une erreur non gérée côté server est survenue et a "cassé" le server... ça craint.|
    

Donc en théorie, quand tout fonctionne normalement, le server doit toujours renvoyer du JSON (utf8), avec code HTTP valant `200`.
La structure de la réponse JSON est toujours la même :

**En cas de succès** du traitement de la requête
```javascript=
HTTP code = 200
{
    "success" : True, // boolean à vrai pour indiquer le traitement avec succès
    
    // Optionnel si resultat attendu
    "data" : json, // toujours formaté en JSON
    
    // Optionnel si pagination du resultat
    "range_offset" : int, // l'offset de départ des résultats
    "range_limit"  : int, // la limit autorisée du nombre de résultats renvoyés utilisé par la requête (1000 par défaut)
    "range_total"  : int, // le nombre total d'éléments en base de donnée (à e pas confondre avec le nombre d'élement retournée par la requête)
}
```


**En cas d'erreur** (gérée) lors du traitement de la requête
```javascript=
HTTP code = 200
{
    "success" : False,    // boolean à faux 
    "msg": string,        // un message d'erreur humainement compréhensible en anglais
    "error_code": string, // le code d'erreur
    "error_url": string,  // l'url de la doc en ligne concernant l'erreur
    "error_id": string    // l'identifiant unique de l'erreur qui permet de localiser facilement l'erreur dans les logs.
}
```


Lazy Loading
------------
Par défaut une requête va retourner les ressources avec un certains nombre de champs renseignés. Pour économiser de la bande passante il est parfois nécessaire de ne récupérer que les infos dont on a besoin. Par défaut les requêtes qui renvoient des listes de résultat ne fournissent qu'un nombre limité d'information, alors que les requêtes qui retourne un seul résultat vont retourner l'ensemble des infos disponibles. Mais tout ceci est détaillé dans les pages dédiées aux points d'accès des différentes ressources.

Pour les requêtes qui supportent le lazy loading (par exemple `/users` qui retourne la liste des utilisateurs), il est possible de spécifier quels champs à retourner dans la réponse.

**Query Parameter** : `?fields={fieldname}[,{fieldname2},...]`
```javascript=
Exemple : 

GET regovar.org/users
{
    "success" : True,
    "data": [{
        "id" : int;
        "firstname": string,
        "lastname" : string,
        "function" : string,
        "location" : string,
        "email" : string,
        "roles" : json,
        // ...
    }]
}

GET regovar.org/users?fields=id,email
{
    "success" : True,
    "data": [
        {"id" : 1, "email" : "user1@mail.com"},
        {"id" : 2, "email" : "user2@mail.com"}, 
        {"id" : 3, "email" : "user3@mail.com"}, 
        ...]
}
```


Pagination
----------
Pour les requêtes qui la supporte (par exemple `/users`), il est possible de spécifier la plage de résultat à retourner.

**Query Parameter** : `?range={first}-{end}`
 * Retourne la liste des résultat allant du `{first}` au `{end}` inclus (à noter que le premier élément à pour index 0).
```javascript=
Exemple : 

GET regovar.org/alphabet
{
    "success" : True,
    "data": ["a", "b", ... "z"] // total = 26 éléments
}

GET regovar.org/alphabet?range=2-6
{
    "success" : True,
    "data": ["c", "d", "e", "f"],
    "range_offset" : 2,
    "range_limit"  : 4, // = min ({end}-{first}, Default_limite=1000)
    "range_total"  : 26
}
```


Filtrage 
--------
Pour les requêtes qui la supporte (par exemple `/users`), il est possible de spécifier des paramètres de filtrage pour ne retourner qu'une certaine partie des résultats.

**Query Parameter** : `?{fieldname}={value}[,{or_value},...][&{fieldname2...}]`
 * On peut filtrer en précisant en paramètre un champs de la ressource et la valeur attendue. La liste des champs filtrable est fournis par la requêtes principale sans aucun arguments (dans notre exemple la requête `/users`). Seul les attributs directs de la ressource peuvent être filtrés.;
 * On peut filtrer sur plusieurs champs à la fois en les séparant avec le `&`. Dans ce cas le moteur de filtrage appliquera implicement la condition `AND` entre chaque champs filtrés;
 * On peut filtrer sur plusieurs valeurs pour un même champs, en les séparant avec le symble `,`. Pour le moteur de filtrage il s'agira d'appliquer un `OR` pour chacune de ces valeurs; 
 * il n'est pas possible de faire du filtrage complexe via ce systeme. Ainsi pour les recherche ou filtrage nécessitant l'usage d'expression régulière, d'opérateur type `>=`, etc, si la ressource le permet, une requete dédié sera proposée (par exemple **`POST`**`/users/search`).
```javascript=
Exemple : 

GET regovar.org/users?firstname=Toto
// Return list of user with firstname == "Toto"
{
    "success" : True,
    "data": [
        {
            "id" : 15,
            "firstname" : "Toto",
            "lastname" : "TOTO",
        }, 
        {
            "id" : 16,
            "firstname" : "Toto",
            "lastname" : "TATA",
        }]
}

GET regovar.org/users?firstname=Toto,Titi&lastname=TATA
// Return list of user with (firstname == "Toto" or "Titi") and with lastname == "TATA"
{
    "success" : True,
    "data": [
        {
            "id" : 16,
            "firstname" : "Toto",
            "lastname" : "TATA",
        }]
}
```



Ordonner 
--------
Pour les requêtes qui la supporte (par exemple `/users`), il est possible de spécifier des paramètres pour ordonner les résultats selon certains champs par ordre croissant ou décroissant.

**Query Parameter** : `?sort={field1}[,{field2},...][&desc={fieldX}[,{fieldY}]]`
* L'attribut `sort` permet de lister les champs dans l'ordre suivant lequel les résultats vont être ordonnés (par ordre croissant pour chaque champs);
* L'attribut `desc` liste les champs (parmis ceux avec l'attributs sort qui doivent suivrent l'ordre décroissant et non croissant)
```javascript=
Exemple : 

GET regovar.org/users?sort=lastname,firstname
// Retourne la liste des utilisateur par ordre alphabétique des Nom, puis des Prénoms

GET regovar.org/users?sort=lastname,firstname&desc=lastname
// Retourne la liste des utilisateur par ordre alphabétique inversé des Nom, puis par ordre alphabétique des Prénoms
```

		

Search
------
*à définir ...*







Identification et authentification
==================================
Qui dit internet, dit authenticatification des utilisateurs à distance, session et mot de passe. Tout cela est gérer via le point d'entrée [`/users`](), grâce aux actions :
 * **`POST`**`/users/login` : permet l'authentification grâce aux paramètres `login` et `password` à fournir dans le corps de la requête. Si l'authentification échoue, une erreur 403 est retournée (Forbidden); si elle réussi, 
 * **`GET`**`/users/logout` : tue la session de l'utilisateur.
 *à détailler ..., coockie, authorisation, aiohttp, clés sécurité, cryptage pwd*
 
