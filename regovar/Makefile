
database_name=regovar
database_path=/var/prod_regovartest/data/databases

# Docker manual command
# docker run -a stdin -a stdout -it -v /var/regovar:/var/regovar:rw -v /home/olivier/git/Regovar/regovar:/var/regovar_app:rw -w /var/regovar_app --network regovar_net -p 8500:8500 --name regovar_app --user 1000:1000 regovar_img python regovar.py

start:
	docker start testregovar_app


debug:
	docker start -ai testregovar_app


stop: 
	docker stop testregovar_app

pp:
	docker rm -f regovar_debug || true
	docker run -a stdin -a stdout -it -v /var/run/docker.sock:/var/run/docker.sock -v /var/prod_regovartest/data:/var/regovar:rw -v /var/prod_regovartest/Regovar/regovar:/var/regovar_app:rw -w /var/regovar_app --network testregovar_net -p 8550:8550 --name regovar_debug regovar sh




#Database utils
terminate_queries:
	docker exec testregovar_pg psql -U regovar -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$(database_name)'"



list_db:
	docker exec testregovar_pg psql -U regovar -d $(database_name) -c "SELECT relname as Table, pg_size_pretty(pg_total_relation_size(relid)) As Size, pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as ExternalSize, rowcount as RowCount \
    FROM pg_catalog.pg_statio_user_tables  \
    LEFT JOIN ( \
        SELECT table_name, n_tup_ins - n_tup_del as rowcount  \
        FROM (SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name) AS _t  \
        LEFT JOIN pg_stat_all_tables ON table_name=relname ORDER BY table_name) AS _sub ON table_name=relname \
    ORDER BY table_name ASC"


update_hpo: 
	wget http://purl.obolibrary.org/obo/hp.obo -O $(database_path)/hpo.obo
	wget http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/data_version.txt -O $(database_path)/hpo_version.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/phenotype_annotation.tab -O $(database_path)/hpo_annotation.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/negative_phenotype_annotation.tab -O $(database_path)/hpo_annotation_neg.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations.monthly/lastStableBuild/artifact/annotation/ALL_SOURCES_ALL_FREQUENCIES_diseases_to_genes_to_phenotypes.txt -O $(database_path)/hpo_disease.txt
	wget http://compbio.charite.de/jenkins/job/hpo.annotations.monthly/lastStableBuild/artifact/annotation/ALL_SOURCES_ALL_FREQUENCIES_phenotype_to_genes.txt -O $(database_path)/hpo_phenotype.txt
	docker stop regovar_update_hpo || true && docker rm regovar_update_hpo || true
	docker run -a stdin -a stdout -it -v /var/prod_regovartest/data:/var/regovar:rw -v /var/prod_regovartest/Regovar/regovar:/var/regovar_app:rw -w /var/regovar_app --network testregovar_net --name regovar_update_hpo --user 1000:1000 regovar python extradata.py hpo /var/regovar/databases/ "`cat $(database_path)/hpo_version.txt`"
	

update_panels:
	wget https://github.com/REGOVAR/GenesPanel/archive/master.zip -O $(database_path)/panels.zip
	unzip -qq $(database_path)/panels.zip -d $(database_path)
	docker stop regovar_update_panels || true && docker rm regovar_update_panels || true
	docker run -a stdin -a stdout -it -v /var/prod_regovartest/data:/var/regovar:rw -v /var/prod_regovartest/Regovar/regovar:/var/regovar_app:rw -w /var/regovar_app --network testregovar_net --name regovar_update_panels --user 1000:1000 regovar python extradata.py panels
	rm -Rf $(database_path)/GenesPanel-master

	

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


.PHONY: start list_db test update_hpo
