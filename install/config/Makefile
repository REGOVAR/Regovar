#Regovar/Regovar/install/config/Makefile
database_name=$(shell sed -n 's/^\s*DATABASE_NAME\s*=\s*"\([^"]\+\)".*/\1/p' config.py)
database_path=$(shell sed -n 's/^\s*DATABASES_DIR\s*=\s*"\([^"]\+\)".*/\1/p' config.py)

# Docker manual command
# docker run -a stdin -a stdout -it -v /var/regovar:/var/regovar:rw -v /home/olivier/git/Regovar/regovar:/var/regovar_app:rw -w /var/regovar_app --network regovar_net -p 8500:8500 --name regovar_app --user 1000:1000 regovar_img python regovar.py

start:
	docker rm -f regovar_app
	docker start regovar_app


debug:
	docker rm -f regovar_app
	docker start -ai regovar_app


stop:
	docker stop regovar_app


#Database utils
terminate_queries:
	docker exec regovar_pg psql -U regovar -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$(database_name)'"



list_db:
	docker exec regovar_pg psql -U regovar -d $(database_name) -c "SELECT relname as Table, pg_size_pretty(pg_total_relation_size(relid)) As Size, pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as ExternalSize, rowcount as RowCount \
    FROM pg_catalog.pg_statio_user_tables  \
    LEFT JOIN ( \
        SELECT table_name, n_tup_ins - n_tup_del as rowcount  \
        FROM (SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name) AS _t  \
        LEFT JOIN pg_stat_all_tables ON table_name=relname ORDER BY table_name) AS _sub ON table_name=relname \
    ORDER BY table_name ASC"

download_hpo:
	wget http://purl.obolibrary.org/obo/hp.obo -O $(database_path)/hpo.obo
	wget http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/data_version.txt -O $(database_path)/hpo_version.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/phenotype_annotation.tab -O $(database_path)/hpo_annotation.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/negative_phenotype_annotation.tab -O $(database_path)/hpo_annotation_neg.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations.monthly/lastStableBuild/artifact/annotation/ALL_SOURCES_ALL_FREQUENCIES_diseases_to_genes_to_phenotypes.txt -O $(database_path)/hpo_disease.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations.monthly/lastStableBuild/artifact/annotation/ALL_SOURCES_ALL_FREQUENCIES_phenotype_to_genes.txt -O $(database_path)/hpo_phenotype.txt

install_hpo: download_hpo
	python3 update_hpo.py /var/regovar/databases/ "`cat $(database_path)/hpo_version.txt`"

update_hpo: download_hpo
	docker stop regovar_update_hpo || true && docker rm regovar_update_hpo || true
	docker run -a stdin -a stdout -it -v /var/regovar:/var/regovar:rw -v /home/olivier/git/Regovar/regovar:/var/regovar_app:rw -w /var/regovar_app --network regovar_net --name regovar_update_hpo --user 1000:1000 regovar python update_hpo.py /var/regovar/databases/ "`cat $(database_path)/hpo_version.txt`"


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



.PHONY: start debug stop terminate_queries list_db install_hpo update_hpo test
