# Le contexte
Avec l'évolution des technologies de séquençage haut débit, la bioinformatique et l'informatique prend une place prépondérante en biologie et en médecine pour le diagnostic moléculaire. Cependant, les logiciels existants nécessitent pour la plupart des compétences informatiques hors de portée d'un non-bioinformaticien ou bien payants. Les licenses de ces logiciels ne sont pas données ce qui est un problème pour les CHU. Les bio-informaticiens quant à eux sont débordés et passent plus de temps à aider les biologistes à utiliser les outils, plutôt qu'à améliorer et développer leurs pipelines.

Regovar est un projet collaboratif, libre, gratuit et ouvert de logiciel d’analyse de données de séquençage haut débit pour les panels de gènes, l’exome et le génome (DPNI, recherche de SNV, CNV, SV...). Il vise à impliquer et fédérer les différentes communautés concernées (généticiens cliniciens, biologistes et bioinformaticiens), sans limites institutionnelles ou géographiques.


# Les objectifs de Regovar




# L'organisation du projet




# Exemple de mise en place dans un CHU
![Architecture système de Regovar](https://raw.githubusercontent.com/REGOVAR/Regovar/master/docs/assets/img/archi_system.png)
* Tout est dans le réseau local du CHU.
* Les utilisateurs accèdent au serveur régovar via le réseau local du CHU grâce au client Regovar prévu à cet effet.
* Un système de batch et de dossier partagés entre les séquenceur et le serveur Regovar peut être mis en place pour automatiser la récupération des "RUN" dans l'application Regovar, Des mails peuvent être automatiquement envoyé pour prévenir les biologistes que leurs données sont prêtes à être analysées.
* Selon le même principe, un batch peut être mis en place pour que tout les weekend par exemple les données n'étant plus utilisées depuis un certains temps soient archivés et supprimé du server Regovar afin de libérer de la place. Ces mêmes batchs peuvent surveiller l'état du serveur et envoyer des alertes par mails aux administrateurs si nécessaire.
* Les batchs ne font qu'utiliser les services proposés par le serveur Regovar afin d'automatiser certaines tâches. L'ensemble de ses tâches (d'ajout et de suppression de données) peuvent être faites manuellement par les utilisateurs.


# 
