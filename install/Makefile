RED=\033[0;31m
NC=\033[0m
database_name=$(shell sed -n 's/^\s*DATABASE_NAME\s*=\s*"\([^"]\+\)".*/\1/p' docker/config.py)
database_path=/var/regovar/databases
#database_path=$(shell sed -n 's/^\s*DATABASES_DIR\s*=\s*"\([^"]\+\)".*/\1/p' docker/config.py)


# Init
init:
	curl http://hgdownload.soe.ucsc.edu/goldenPath/hg19/database/refGene.txt.gz | gunzip > $(database_path)/hg19/refGene.txt:
	curl http://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/refGene.txt.gz | gunzip > $(database_path)/hg38/refGene.txt:
	cp config.default docker/config.py
	echo "\n${RED}INIT DONE: Please check the `pwd`/docker/config.py and `pwd`/docker/regovar.yml files before continue the installation with the command 'make install'${NC}"


terminate_queries:
	docker exec regovar_pg psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$(database_name)'"


clear_db: terminate_queries
	cp *.sql docker/
	docker exec regovar_pg psql -U postgres -c "DROP DATABASE IF EXISTS $(database_name)"
	docker exec regovar_pg psql -U postgres -c "CREATE DATABASE $(database_name) OWNER regovar"
	docker exec regovar_pg psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""
	docker exec regovar_pg psql -U regovar -d $(database_name) -f /var/regovar/install/create_all.sql
	docker exec regovar_pg psql -U regovar -d $(database_name) -f /var/regovar/install/install_hg19.sql
	docker exec regovar_pg psql -U regovar -d $(database_name) -f /var/regovar/install/install_hg38.sql
	rm docker/*.sql


update_hpo:
	#rm $(database_path)/hpo_*
	wget http://purl.obolibrary.org/obo/hp.obo -O $(database_path)/hpo.obo
	wget http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/data_version.txt -O $(database_path)/hpo_version.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/phenotype_annotation.tab -O $(database_path)/hpo_annotation.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/negative_phenotype_annotation.tab -O $(database_path)/hpo_annotation_neg.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations.monthly/lastStableBuild/artifact/annotation/ALL_SOURCES_ALL_FREQUENCIES_diseases_to_genes_to_phenotypes.txt -O $(database_path)/hpo_disease.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations.monthly/lastStableBuild/artifact/annotation/ALL_SOURCES_ALL_FREQUENCIES_phenotype_to_genes.txt -O $(database_path)/hpo_phenotype.txt
	docker cp update_hpo.py regovar_app:update_hpo.py
	chmod u+x update_hpo.py
	python3 update_hpo.py $(database_path)/ "`cat $(database_path)/hpo_version.txt`"
	rm update_hpo.py
	

#Install
install: clear_db install_hpo

update_hpo: terminate_queries install_hpo

#Clean up
clear_files:
	rm -rf /var/regovar/files/*
	rm -rf /var/regovar/downloads/*
	rm -rf /var/regovar/pipelines/*
	rm -rf /var/regovar/jobs/*
	
	
	
	
install_travis:
	sudo -u postgres psql -c "DROP DATABASE IF EXISTS $(database_name)"
	sudo -u postgres psql -c "CREATE DATABASE $(database_name) OWNER regovar"
	sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""
	psql -U regovar -d $(database_name) -f ../install/create_all.sql
	psql -U regovar -d $(database_name) -f ../install/install_hg38.sql
	
	
	