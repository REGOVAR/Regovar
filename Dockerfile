FROM ubuntu:16.04

RUN apt-get update -qy && apt-get install -y wget
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN apt-get update -qy
RUN apt-get install -y \
	curl \
	postgresql-9.6 \
	python3.5 \
	python3-pip\
	unzip



# Postgresql 
#RUN /etc/init.d/postgresql start
#RUN psql -c "DROP DATABASE IF EXISTS regovar"
#RUN psql -c "CREATE DATABASE regovar OWNER postgres"



# Add VOLUMEs to allow backup of config, logs and databases
VOLUME  ["/etc/postgresql", "/var/log/postgresql", "/var/lib/postgresql"]

# Set the default command to run when starting the container
#CMD ["/usr/lib/postgresql/9.6/bin/postgres", "-D", "/var/lib/postgresql/9.6/main", "-c", "config_file=/etc/postgresql/9.6/main/postgresql.conf"]




# Regovar databases
RUN mkdir -p /var/regovar/{app,cache,downloads,files,pipelines,jobs,databases/hg19,databases/hg38}
RUN curl http://hgdownload.soe.ucsc.edu/goldenPath/hg19/database/refGene.txt.gz | unzip > /var/regovar/databases/hg19/refGene.txt
RUN curl http://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/refGene.txt.gz | unzip > /var/regovar/databases/hg38/refGene.txt

COPY ./* /var/regovar/app
RUN cd /var/regovar/app
RUN sudo -u regovar pip install -r requirements.txt
RUN cd regovar
RUN cp ../install/config.default ./config.py
RUN sed -i 's/^\(\s*DATABASE_NAME\s*=\s*"\)[^"]\+\(".*\)/\1regovar\2/' config.py
#RUN make setup
#RUN make install_hpo

