#!/bin/sh

# Start Postgresql server
su - postgres -c '/usr/lib/postgresql/9.6/bin/pg_ctl -D /etc/postgresql/9.6/main/ -l /etc/postgresql/9.6/main/log.txt start'

# Loading public genomes references files
cd /var/regovar/databases/hg19/
wget http://hgdownload.soe.ucsc.edu/goldenPath/hg19/database/refGene.txt.gz
gunzip refGene.txt.gz
cd /var/regovar/databases/hg38/
wget http://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/refGene.txt.gz
gunzip refGene.txt.gz

chmod 777 -R /var/regovar/databases

# Init Regovar database
su - postgres -c "psql -c \"CREATE USER regovar PASSWORD 'regovar'\""
su - postgres -c "psql -c \"GRANT admin TO regovar;\""
su - postgres -c "psql -c \"CREATE DATABASE regovar OWNER regovar\""
su - postgres -c "psql -U regovar -d regovar -f /var/regovar/app/install/create_all.sql"
su - postgres -c "psql -U regovar -d regovar -f /var/regovar/app/install/install_hg19.sql"
su - postgres -c "psql -U regovar -d regovar -f /var/regovar/app/install/install_hg38.sql"



# Run server
cd /var/regovar/app/regovar
python -Wdefault regovar_server.py