FROM python:3.6

# Install Docker binaries inside the container
RUN apt-get update && \
    apt-get -y install apt-transport-https \
        ca-certificates \
        curl \
        gnupg2 \
        software-properties-common && \
    curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg > /tmp/dkey; apt-key add /tmp/dkey && \
    add-apt-repository \
        "deb [arch=amd64] https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") \
        $(lsb_release -cs) \
        stable" && \
    apt-get update && \
    apt-get -y install docker-ce




# Regovar directories
RUN cd /
RUN git clone https://github.com/REGOVAR/Regovar.git
RUN mkdir -p /Regovar/{cache,downloads,files,pipelines,jobs,databases/hg18,databases/hg19,databases/hg38}
# RUN mkdir -p /Regovar/cache
# RUN mkdir -p /Regovar/downloads
# RUN mkdir -p /Regovar/files
# RUN mkdir -p /Regovar/pipelines
# RUN mkdir -p /Regovar/jobs
# RUN mkdir -p /Regovar/databases/hg18
# RUN mkdir -p /Regovar/databases/hg19
# RUN mkdir -p /Regovar/databases/hg38



WORKDIR /Regovar
RUN cd /Regovar
RUN pip install -r requirements.txt
RUN pip install -r requirements-dev.txt


# Expose disks volumes and ports
VOLUME  ["/Regovar/regovar", "/Regovar/cache", "/Regovar/downloads", "/Regovar/files", "/Regovar/pipelines", "/Regovar/jobs", "/Regovar/databases"]


EXPOSE 80
EXPOSE 443