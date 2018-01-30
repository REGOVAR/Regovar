#!/bin/sh


# Start postgresql service
/etc/init.d/postgresql start



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
su - postgres -c "psql -c \"CREATE DATABASE regovar OWNER regovar\""
su - postgres -c "psql -d regovar -f /var/regovar/app/install/create_all.sql"
su - postgres -c "psql -d regovar -f /var/regovar/app/install/install_hg19.sql"
su - postgres -c "psql -d regovar -f /var/regovar/app/install/install_hg38.sql"
exit



# Run server
python -Wdefault /var/regovar/app/regovar/regovar_server.py