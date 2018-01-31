FROM python:3.6

RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN apt-get update -qy && apt-get install -y wget zip gzip postgresql-9.6


# Regovar directories
RUN mkdir -p /var/regovar/app
RUN mkdir -p /var/regovar/cache
RUN mkdir -p /var/regovar/downloads
RUN mkdir -p /var/regovar/files
RUN mkdir -p /var/regovar/pipelines
RUN mkdir -p /var/regovar/jobs
RUN mkdir -p /var/regovar/databases/hg19
RUN mkdir -p /var/regovar/databases/hg38





# Init Postgresql 
RUN mkdir -p /var/regovar/sqldb
RUN chown postgres /var/regovar/sqldb
RUN mv /etc/postgresql/9.6/main/ /etc/postgresql/9.6/old
RUN su - postgres -c '/usr/lib/postgresql/9.6/bin/pg_ctl -D /etc/postgresql/9.6/main/ initdb'





# Copy regovar files
COPY . /var/regovar/app/
RUN cp /var/regovar/app/install/config.default /var/regovar/app/regovar/config.py
RUN sed -i s/127\.0\.0\.1/0\.0\.0\.0/p /var/regovar/app/regovar/config.py
RUN sed -i s/8500/80/p /var/regovar/app/regovar/config.py
RUN chmod a+rwx -R /var/regovar/app/install
RUN chmod a+x /var/regovar/app/*.sh
RUN chmod a+x /var/regovar/app/regovar/*.py


WORKDIR /var/regovar/app
RUN pip install -r /var/regovar/app/requirements.txt
RUN pip install -r /var/regovar/app/requirements-dev.txt


# Expose disks volumes and ports
VOLUME  ["/var/regovar/app", "/var/regovar/cache", "/var/regovar/downloads", "/var/regovar/files", "/var/regovar/pipelines", "/var/regovar/jobs", "/var/regovar/databases", "/etc/postgresql/9.6/main"]


EXPOSE 80