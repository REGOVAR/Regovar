
app:
	python regovar_server.py

clear:
	rm -rf /var/regovar/regovar/files/*
	rm -rf /var/regovar/regovar/downloads/*
	rm -rf /var/regovar/regovar/pipelines/*
	rm -rf /var/regovar/regovar/jobs/*
	

list_db:
	database_name=$$(sed -n 's/^\s*DATABASE_NAME\s*=\s*"\([^"]\+\)".*/\1/p' config.py) ; \
	psql -U regovar -d $${database_name} -c "SELECT relname as Table, pg_size_pretty(pg_total_relation_size(relid)) As Size, pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as ExternalSize, rowcount as RowCount \
    FROM pg_catalog.pg_statio_user_tables  \
    LEFT JOIN ( \
        SELECT table_name, n_tup_ins - n_tup_del as rowcount  \
        FROM (SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name) AS _t  \
        LEFT JOIN pg_stat_all_tables ON table_name=relname ORDER BY table_name) AS _sub ON table_name=relname \
    ORDER BY pg_total_relation_size(relid) DESC"





init:
	cp ../install/config.default ./config.py
	echo "Please, edit the $PWD/config.py file before proceed to the installation with the command 'make install'"
	
install:
	database_name=$$(sed -n 's/^\s*DATABASE_NAME\s*=\s*"\([^"]\+\)".*/\1/p' config.py) ; \
	sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$${database_name}'" ; \
	sudo -u postgres psql -c "DROP DATABASE $${database_name}" ; \
	sudo -u postgres psql -c "CREATE DATABASE $${database_name} OWNER regovar" ; \
	psql -U regovar -d $$database_name -f ../install/create_all.sql ; \
	psql -U regovar -d $$database_name -f ../install/install_hg19.sql ; \
	psql -U regovar -d $$database_name -f ../install/install_hg38.sql ;
	


test:
	database_name=$$(sed -n 's/^\s*DATABASE_NAME\s*=\s*"\([^"]\+\)".*/\1/p' config.py) ; \
	test -n "$${database_name}" && \
	sudo -u postgres psql -c "DROP DATABASE IF EXISTS $${database_name}_test" && \
	sudo -u postgres psql -c "CREATE DATABASE $${database_name}_test OWNER regovar" && \
	psql -U regovar -d $${database_name}_test -f ../install/create_all.sql && \
	psql -U regovar -d $${database_name}_test -f tests/init_fake_data.sql && \
	sed -i.bak 's/^\(\s*DATABASE_NAME\s*=\s*"[^"]\+\)\(".*\)/\1_test\2/' config.py && \
	python tests.py && \
	mv config.py config.test && \
	mv config.py.bak config.py && \
	sudo -u postgres psql -c "DROP DATABASE IF EXISTS $${database_name}_test"
	


.PHONY: install app clear 
