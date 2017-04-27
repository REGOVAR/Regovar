REST API : Ressource Users 
==========================
La ressource `user` défini les utilisateurs de l'application Regovar. Un user est défini de la manière suivante :
| Champs | Type | Description |
|--------|------|-------------|
| **`id`** | qint32 | **Obligatoire, unique, non null**. Identifiant unique de l'utilisateur en base de donnée. `0` est la valeur utilisé pour signifier que l'id n'existe pas. Le premier utilisateur à l'identifiant `1` (il s'agit de l'admin root installé par défaut avec la base de donnée).|
|`firstname` | string | Le prénom |
|`lastname` | string | Le nom de famille|
|`function` | string | La fonction de l'utilisateur (son métier)|
|`location` | string | L'adresse |
|`avatar` | string | L'url vers l'avatar |
|`roles` | json | Liste des authorisations de l'utilisateur. Il s'agit d'un dictionnaire où les clés définissent le rôle, et la valeur l'authorisation ("Read" ou "Write"). Si un rôle n'est pas présent dans le dictionnaire, alors l'utilisateur n'a pas du tout les droits pour ça. |


**List des roles**
Voici la liste de tout les rôles défini dans Regovar. Un ou plusieurs roles peuvent être attribué à un utilisateur. Si il n'est pas attribué, il n'a aucun des droits permis par le role. Sinon, le rôle est en général décliné en 2 niveaux d'accès : `Read` et `Write`. Un accès en `Read` permet à l'utilisateur de consulter les données sans jamais pouvoir les modifier. Un accès `Write` donne les pleins pouvoirs. Exception pour le role `Administration` qui, si il est défini pour un utilisateur, aura forcement le droit `Write` dessus. 
| Role | Description |
|------|-------------|
|`Administration` | L'administrateur peut créer de nouveaux utilisateurs, éditer les données de tout les utilisateur.|



`GET /users`
------------
*Retourne la liste des utilisateurs de l'application Regovar.*
Core feature : [`regovar.users.get`]()
| Authentification | Lazy Loading | Pagination | Filtrage | Ordonnancement |
|------------------|--------------|------------|----------|----------------|
|non requis | Oui | Oui | Oui | Oui | 
* Erreurs retournées:
    * E301001 : bad lazy loading's parameters
    * E301002 : bad range's parameters
    * E301003 : bad filter's parameters
    * E301004 : bad sort's parameters
* Exemples de requêtes:
    * [/users](http://test.regovar.org/users) : retourne la liste des users
    * [/users?range=10-15](http://test.regovar.org/users?range=10-15) : retourne la liste des users, du 10ème au 15ème
    * 





`POST /users`
-------------
*Cré un nouveau user.*
Core feature : [`regovar.users.create_or_update`]()
| Authentification | Lazy Loading | Pagination | Filtrage | Ordonnancement |
|------------------|--------------|------------|----------|----------------|
|Admin only | Non | Non | Non | Non | 

Post Body
| Part name | Part type | Description |
|-----------|-----------|-------------|
| `login` | int | Optionel. Ce paramêtre ne sera pris en compte que si l'utilisateur 

* Erreurs retournées:
    * 
* Exemples de requêtes:
    * 

`GET /users/{user_id}`
----------------------
*Récupère les détails concernant un user identifié par `{user_id}`.*
Core feature : [`regovar.users.create_or_update`]()
| Authentification | Lazy Loading | Pagination | Filtrage | Ordonnancement |
|------------------|--------------|------------|----------|----------------|
|Authenfication requise | Non | Non | Non | Non | 

* Erreurs retournées:
    * 
* Exemples de requêtes:
    * 

`PUT /users/{user_id}`
----------------------
Edit user with provided data
*Récupère les détails concernant un user.*
Core feature : [`regovar.users.create_or_update`]()
| Authentification | Lazy Loading | Pagination | Filtrage | Ordonnancement |
|------------------|--------------|------------|----------|----------------|
|Authenfication requise | Non | Non | Non | Non | 

Put Body
| Part name | Part type | Description |
|-----------|-----------|-------------|
| `login` | int | Optionel. Ce paramêtre ne sera pris en compte que si l'utilisateur 

`POST /users/login`
-------------------
Start user's session if provided credentials are correct

`GET /users/logout`
-------------------
Kill user's session


`DELETE /users/{user_id}`
-------------------
Delete a user
