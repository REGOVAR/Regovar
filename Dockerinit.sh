#!/bin/sh


# Check application files
if [ "$(ls -A /var/regovar/app)" ]; then
     echo "Using existing version/configuration of /var/regovar/app folder"
else
    # Folder empty, populate it with current regovar version of docker image
    # Moving application files to the mounted app folder
    mv /var/regovar/_app/* /var/regovar/app/
fi


# Start Postgresql server
su - postgres -c '/usr/lib/postgresql/9.6/bin/pg_ctl -D /etc/postgresql/9.6/main/ -l /etc/postgresql/9.6/main/log.txt start'


# Loading/Refresh public genomes references files
cd /var/regovar/databases/hg19/
wget http://hgdownload.soe.ucsc.edu/goldenPath/hg19/database/refGene.txt.gz
gunzip -q refGene.txt.gz
cd /var/regovar/databases/hg38/
wget http://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/refGene.txt.gz
gunzip -q refGene.txt.gz


# Update hpo
wget http://compbio.charite.de/jenkins/job/hpo.annotations.monthly/lastStableBuild/artifact/annotation/ALL_SOURCES_ALL_FREQUENCIES_diseases_to_genes_to_phenotypes.txt -O /var/regovar/databases/hpo_disease.txt
wget http://compbio.charite.de/jenkins/job/hpo.annotations.monthly/lastStableBuild/artifact/annotation/ALL_SOURCES_ALL_FREQUENCIES_phenotype_to_genes.txt -O /var/regovar/databases/hpo_phenotype.txt


# Init Regovar database
# psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""
psql -U postgres -c "CREATE USER regovar PASSWORD 'regovar'"
psql -U postgres -c "CREATE DATABASE regovar OWNER regovar"
psql -U regovar -d regovar -f /var/regovar/app/install/create_all.sql
psql -U regovar -d regovar -f /var/regovar/app/install/install_hg19.sql
psql -U regovar -d regovar -f /var/regovar/app/install/install_hg38.sql
psql -U regovar -d regovar -f /var/regovar/app/install/update_hpo.sql





# Add local user
# Either use the LOCAL_USER_ID if passed in at runtime or fallback
# USER_ID=${LOCAL_USER_ID:-9001}
# echo "Starting with UID : $USER_ID"
# useradd --shell /bin/bash -u $USER_ID -o -c "" -m user
# export HOME=/home/user




# Run server with good user
# chown -R $USER_ID:$USER_ID /var/regovar/app
cd /var/regovar/app/regovar # need it to avoid problem with python import relative path
python -Wdefault regovar_server.py
# exec /usr/local/bin/gosu user python -Wdefault regovar_server.py



