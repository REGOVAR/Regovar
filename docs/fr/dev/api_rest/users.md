API REST : Ressource Users 
==========================
Fichier principal : `/regovar/web/handlers/user_handler.py`

---
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

---

`GET /users`
------------
*Retourne la liste des utilisateurs de l'application Regovar.*
Core feature : [`regovar.users.get`]()
| Authentification | Lazy Loading | Pagination | Filtrage | Ordonnancement |
|------------------|--------------|------------|----------|----------------|
|non requis | Oui | Oui | Oui | Oui | 
* Erreurs retournées:
    * E301001 : si les paramètres de *Lazy Loading* sont incorrects;
    * E301002 : si les paramètres de pagination sont incorrects;
    * E301003 : si les paramètres de filtrage sont incorrects;
    * E301004 : si les paramtères d'ordonnancement sont incorrects.
* Exemples de requêtes:
    * [/users](http://test.regovar.org/users) : retourne la liste des users;
    * [/users?range=10-15](http://test.regovar.org/users?range=10-15) : retourne la liste des users, du 10ème au 15ème;




---

`POST /users`
-------------
*Cré un nouveau user.*
Core feature : [`regovar.users.create_or_update`]()
| Authentification | Lazy Loading | Pagination | Filtrage | Ordonnancement |
|------------------|--------------|------------|----------|----------------|
|Admin | Non | Non | Non | Non | 

Post Body
| Part name | Part type | Description |
|-----------|-----------|-------------|
| `login` | int | Requis. Ce paramêtre est nécessaire à la création de l'utilisateur. Si il n'est pas fournis, ou si il est déjà utilisé par un autre utilisateur déjà en base de donnée, l'action échouera.
| `firstname` | string | Optionnel. Le prénom du nouvel utilisateur.
| `lastname` | string | Optionnel. Le nom de famille du nouvel utilisateur.
| `email` | string | Optionnel. L'email du nouvel utilisateur. Attention celui-ci doit être unique. C'est à dire que si un autre utilisateur déjà présent en base de donnée à le même email, la création de l'utilisateur échouera.
| `function` | string | Optionnel. La fonction du nouvel utilisateur.
| `location` | string | Optionnel. La localisation du nouvel utilisateur.
| `password` | string | Optionnel. Le password du nouvel utilisateur.
| `avatar` | bytes array | Optionnel. L'image à utiliser utiliser comme avatar pour le nouvel utilisateur
* Erreurs retournées:
    * E100002 : Si la création de l'utilisateur à échouée (mauvais login ou email)
    * E101002 : Si les données fournis au serveur ne sont pas lisible.

* Exemples de requêtes:
    * *A FAIRE*


---

`GET /users/{user_id}`
----------------------
*Récupère les détails concernant un user identifié par `{user_id}`.*
Core feature : [`regovar.users.create_or_update`]()
| Authentification | Lazy Loading | Pagination | Filtrage | Ordonnancement |
|------------------|--------------|------------|----------|----------------|
|Authenfication requise | Non | Non | Non | Non | 
* Erreurs retournées:
    * E101001 : si l'id fournis n'existe pas en base de donnée.
* Exemples de requêtes:
    * *A FAIRE*



---

`PUT /users/{user_id}`
----------------------
*Met à jour les information concernant un user.*
Core feature : [`regovar.users.create_or_update`]()
| Authentification | Lazy Loading | Pagination | Filtrage | Ordonnancement |
|------------------|--------------|------------|----------|----------------|
|Authenfication requise | Non | Non | Non | Non | 

Put Body
| Part name | Part type | Description |
|-----------|-----------|-------------|
| `login` | int | Optionel. Ce paramêtre ne sera pris en compte que si l'utilisateur qui exécute la requête est un administrateur.
| `firstname` | string | Optionnel. Le prénom du nouvel utilisateur.
| `lastname` | string | Optionnel. Le nom de famille du nouvel utilisateur.
| `email` | string | Optionnel. L'email du nouvel utilisateur. Attention celui-ci doit être unique. C'est à dire que si un autre utilisateur déjà présent en base de donnée à le même email, la création de l'utilisateur échouera.
| `function` | string | Optionnel. La fonction du nouvel utilisateur.
| `location` | string | Optionnel. La localisation du nouvel utilisateur.
| `password` | string | Optionnel. Le password du nouvel utilisateur.
| `avatar` | bytes array | Optionnel. L'image à utiliser utiliser comme avatar pour le nouvel utilisateur
* Erreurs retournées:
    * E100002 : Si la mise à jour de l'utilisateur à échouée (mauvais login ou email)
    * E101002 : Si les données fournis au serveur ne sont pas lisible.
    * E101006 : *A FAIRE*
    * E101007 : *A FAIRE*
* Exemples de requêtes:
    * *A FAIRE*
    
    
---

`POST /users/login`
-------------------
*Permet de s'authentifier auprès du server. Si le login et mot de passe son correctes, une session sera ouverte pour l'utilisateur. Sinon une erreur HTTP 403 sera retournée.*
Core feature : -
| Authentification | Lazy Loading | Pagination | Filtrage | Ordonnancement |
|------------------|--------------|------------|----------|----------------|
| Non | Non | Non | Non | Non | 
* Erreurs retournées:
    * HTTP 403 : si le login et le mot de passe ne permettent pas d'authentifier l'utilisateur.
* Exemples de requêtes:
    * *A FAIRE*


---

`GET /users/logout`
-------------------
*Détruit la session de l'utilisateur qui exécute la requête.*
Core feature : -
| Authentification | Lazy Loading | Pagination | Filtrage | Ordonnancement |
|------------------|--------------|------------|----------|----------------|
|Authenfication requise | Non | Non | Non | Non | 
* Erreurs retournées:
    * Aucune. Renvoie toujours succès.
* Exemples de requêtes:
    * *A FAIRE*



---

`DELETE /users/{user_id}`
-------------------
Delete a user
*Détruit l'utilisateur ayant l'identifiant `{user_id}`.*
Core feature : [`regovar.users.delete`]()
| Authentification | Lazy Loading | Pagination | Filtrage | Ordonnancement |
|------------------|--------------|------------|----------|----------------|
|Admin | Non | Non | Non | Non | 
* Erreurs retournées:
    * E101001 : si l'id fournis n'existe pas en base de donnée;
    * E101003 : si l'utilisateur qui fait l'action n'a pas les droits suffisant;
    * E101005 : les admins n'ont pas le droit de s'auto détruire. C'est un autre admin qui doit le faire.
* Exemples de requêtes:
    * *A FAIRE*




