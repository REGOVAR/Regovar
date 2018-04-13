
database_name=$(shell sed -n 's/^\s*DATABASE_NAME\s*=\s*"\([^"]\+\)".*/\1/p' config.py)
database_path=$(shell sed -n 's/^\s*DATABASES_DIR\s*=\s*"\([^"]\+\)".*/\1/p' config.py)

app:
	python3 regovar_server.py

init:
	cp ../install/config.default ./config.py
	echo "Please, edit the $PWD/config.py file before proceed to the installation with the command 'make install'"

#Database utils
terminate_queries:
	sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$(database_name)'"

destroy: terminate_queries
	sudo -u postgres psql -c "DROP DATABASE IF EXISTS $(database_name)"
	sudo -u postgres psql -c "CREATE DATABASE $(database_name) OWNER regovar"
	sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""

list_db:
	psql -U regovar -d $(database_name) -c "SELECT relname as Table, pg_size_pretty(pg_total_relation_size(relid)) As Size, pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as ExternalSize, rowcount as RowCount \
    FROM pg_catalog.pg_statio_user_tables  \
    LEFT JOIN ( \
        SELECT table_name, n_tup_ins - n_tup_del as rowcount  \
        FROM (SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name) AS _t  \
        LEFT JOIN pg_stat_all_tables ON table_name=relname ORDER BY table_name) AS _sub ON table_name=relname \
    ORDER BY table_name ASC"

#Install
install: destroy setup

setup:
	psql -U regovar -d $(database_name) -f ../install/create_all.sql
	psql -U regovar -d $(database_name) -f ../install/install_hg19.sql
	psql -U regovar -d $(database_name) -f ../install/install_hg38.sql

#HPO
install_hpo:
	#rm $(database_path)/hpo_*
	wget http://purl.obolibrary.org/obo/hp.obo -O $(database_path)/hpo.obo
	wget http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/data_version.txt -O $(database_path)/hpo_version.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/phenotype_annotation.tab -O $(database_path)/hpo_annotation.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/negative_phenotype_annotation.tab -O $(database_path)/hpo_annotation_neg.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations.monthly/lastStableBuild/artifact/annotation/ALL_SOURCES_ALL_FREQUENCIES_diseases_to_genes_to_phenotypes.txt -O $(database_path)/hpo_disease.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations.monthly/lastStableBuild/artifact/annotation/ALL_SOURCES_ALL_FREQUENCIES_phenotype_to_genes.txt -O $(database_path)/hpo_phenotype.txt
	cp ../install/update_hpo.py update_hpo.py
	chmod u+x update_hpo.py
	python3 update_hpo.py $(database_path)/ "`cat $(database_path)/hpo_version.txt`"
	rm update_hpo.py
	
update_hpo: terminate_queries install_hpo

#Clean up
clear_files:
	rm -rf /var/regovar/files/*
	rm -rf /var/regovar/downloads/*
	rm -rf /var/regovar/pipelines/*
	rm -rf /var/regovar/jobs/*

#Tests
test:
	test -n $(database_name)
	sudo -u postgres psql -c "DROP DATABASE IF EXISTS $(database_name)_test"
	psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""
	sudo -u postgres psql -c "CREATE DATABASE $(database_name)_test OWNER regovar"
	psql -U regovar -d $(database_name)_test -f ../install/create_all.sql
	psql -U regovar -d $(database_name)_test -f tests/init_fake_data.sql
	sed -i.bak 's/^\(\s*DATABASE_NAME\s*=\s*"[^"]\+\)\(".*\)/\1_test\2/' config.py
	coverage run tests.py
	coverage report
	mv config.py config.test
	mv config.py.bak config.py
	sudo -u postgres psql -c "DROP DATABASE IF EXISTS $(database_name)_test"


install_travis:
	sudo -u postgres psql -c "DROP DATABASE IF EXISTS $(database_name)"
	sudo -u postgres psql -c "CREATE DATABASE $(database_name) OWNER regovar"
	sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""
	psql -U regovar -d $(database_name) -f ../install/create_all.sql
	psql -U regovar -d $(database_name) -f ../install/install_hg38.sql


.PHONY: app clear_files destroy list_db init install install_hpo setup terminate_queries test update_hpo
