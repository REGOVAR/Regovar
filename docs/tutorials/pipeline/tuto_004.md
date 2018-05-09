# Ex1: Créer un pipeline simple

Dans ce tutoriel, nous allons créer un pipeline simple, qui génère un rapport [multiqc](http://multiqc.info/).

Difficultés abordées par ce tutoriel :
- [x] Dockerisation d'un pipeline bioinformatique
- [x] Fichiers INPUTS (type bam)
- [x] Génèration OUTPUTS (rapport html)
- [ ] Génèration de LOGS
- [ ] Paramètres personnalisables
- [ ] Notifications temps réel de la progression
- [ ] Connection base de donnée Regovar


## Les instructions

Voici d'emblé tout ce qu'il faut faire. Les explications sont dans la section suivante

Etape 1: init package folder
```
mkdir ~/mypipeline
cd ~/mypipeline
mkdir doc
cd doc
wget https://raw.githubusercontent.com/REGOVAR/Regovar/master/docs/tutorials/pipeline/tuto_003/about.html
wget https://raw.githubusercontent.com/REGOVAR/Regovar/master/docs/tutorials/pipeline/tuto_003/help.html
wget https://raw.githubusercontent.com/REGOVAR/Regovar/master/docs/tutorials/pipeline/tuto_003/icon.png
cd ..
```
Etape 2: create docker file
```
nano Dockerfile
```
Ecrire le contenu suivant dans le fichier
```
FROM biocontainers/samtools:latest

# Install multiqc
USER root
RUN \
  apt-get update && apt-get install -y --no-install-recommends \
  g++ \
  git \
  wget \
  && wget --quiet -O /opt/get-pip.py https://bootstrap.pypa.io/get-pip.py \
  && python /opt/get-pip.py \
  && rm -rf /var/lib/apt/lists/* /opt/get-pip.py
RUN pip install git+git://github.com/ewels/MultiQC.git
RUN mkdir /outputs && chown biodocker:biodocker /outputs

# Generate start script sh
USER biodocker
RUN echo "#!/bin/sh\nmkdir /tmp/analysis\nsamtools stats /data/*.bam > /outputs/report.bam.sas.txt\nmultiqc ." > /home/biodocker/run.sh
RUN chmod +x /home/biodocker/run.sh

WORKDIR /outputs/
CMD ["/home/biodocker/run.sh"]
```
Etape 3: create manifest
```
nano manifest.json
```
Ecrire le contenu suivant dans le fichier
```
{
    "name" : "Multiqc",
    "description" : "Aggregate bioinformatics results across many samples into a single report.",
    "version": "1.0",
    "type": "job",
    "contacts" : [],
    "regovar_db_access": False,
    "inputs" : "/data/",
    "outputs" : "/outputs/",
    "databases": "/tmp/regovar_db/",
    "logs" : "/tmp/regovar_logs/"
}
```
Etape 4 (optionnel): test with docker
```

mkdir /tmp/test_inputs 
# put a bam+bai in this folder
mkdir /tmp/test_ouputs
ls -l /tmp/test_ouputs
docker build -t regovar_pipe_test .
docker image ls
docker run -a stdin -a stdout -it -v /tmp/test_inputs:/data -v /tmp/test_ouputs:/outputs --name regovar_test --user 1000:1000 regovar_pipe_test
ls -l /tmp/test_ouputs
docker rm --force regovar_test
docker rmi regovar_pipe_test
```
Etape 5: create package
```
cd ..
zip -r multiqc_pipeline_1.0.zip mypipeline
```

Voilà, il ne reste plus qu'à [tester dans Regovar](tuto_001.md)




## Explications

###Etape 1


###Etape 2


###Etape 3


###Etape 4


###Etape 5


 
