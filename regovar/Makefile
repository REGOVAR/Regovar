install:
	cp ../install/config.default ./config.py
	echo "Please, edit the $PWD/config.py file before starting the server with the command 'make app'"

app:
	python regovar_server.py

drop:
	psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'regovar'"
	psql -U postgres -c "DROP DATABASE regovar"
	psql -U postgres -c "CREATE DATABASE regovar OWNER regovar"
	psql -U regovar -d regovar -f ../install/create_all.sql
	

list_db:
	psql -U regovar -d regovar -c "SELECT relname as Table, pg_size_pretty(pg_total_relation_size(relid)) As Size, pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as ExternalSize, rowcount as RowCount \
    FROM pg_catalog.pg_statio_user_tables  \
    LEFT JOIN ( \
        SELECT table_name, n_tup_ins - n_tup_del as rowcount  \
        FROM (SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name) AS _t  \
        LEFT JOIN pg_stat_all_tables ON table_name=relname ORDER BY table_name) AS _sub ON table_name=relname \
    ORDER BY pg_total_relation_size(relid) DESC"



.PHONY: install app clear 
