Developer Guide
###############



Solution organisation
=====================
 * The core team of Annso project:
    * As sub project of Revogar, the core team of Annso, is the same as for Regovar : Ikit, dridk, Oodnadatta and Arkanosis. All of them are both consultant and developer.
 * Coding Rules : 
    * https://www.python.org/dev/peps/pep-0008/
 * Git branching strategy : 
    * Dev on master, 
    * One branch by release; with the version number as name (by example branch "v1.0.0" for the v1.0.0)
 * Discussion : 
    * https://regovar.slack.com/
    * dev@regovar.org
 


Architecture
============

See dedicated page


Model
=====



Analyse
------
|   **Static property :**
|      public_fields <str[]> : liste des champs exportable pour le enduser (client annso)
|      
|   **Public properties :**
|      id <int> : id of the sample in the database
|      name <str> : (required) name of the sample when imported (name in the vcf file by example)
|      comment <str> : user can add some comments about the sample
|      is_mosaic <bool> : true if the sample is [mosaic](https://www.wikiwand.com/en/Mosaic_(genetics)); false otherwithe
|      
|   **Internal properties :**
|      -
|
|   **Static methods :**
|      from_id(pipe_id) : return a Pipeline object from the database
|      
|   **Internal methods :**
|      export_server_data(self)
|      export_client_data(self)
|      import_data(self, data)
|      url(self) : return the url that shall be used to download the pipeline package
|      upload_url(self) : return the url that shall be used to upload the pipeline on the server


Sample
------
|   **Static property :**
|      public_fields <str[]> : liste des champs exportable pour le enduser (client annso)
|      
|   **Public properties :**
|      id <int> : id of the sample in the database
|      name <str> : (required) name of the sample when imported (name in the vcf file by example)
|      comment <str> : user can add some comments about the sample
|      is_mosaic <bool> : true if the sample is [mosaic](https://www.wikiwand.com/en/Mosaic_(genetics)); false otherwithe
|      
|   **Internal properties :**
|      -
|
|   **Static methods :**
|      from_id(pipe_id) : return a Pipeline object from the database
|      
|   **Internal methods :**
|      export_server_data(self)
|      export_client_data(self)
|      import_data(self, data)
|      url(self) : return the url that shall be used to download the pipeline package
|      upload_url(self) : return the url that shall be used to upload the pipeline on the server


      


API
===

See dedicated page for the current api implemented.

 * How to update current api
 * Implement a new version of the api



TUS.IO protocol
===============


