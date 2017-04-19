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
	





.PHONY: install app clear 
