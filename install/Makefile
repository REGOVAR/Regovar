install_dir=$(dir $(realpath $(firstword $(MAKEFILE_LIST))))

# PostgreSQL
database_name=$(shell test -f ../regovar/config.py && sed -n 's/^\s*DATABASE_NAME\s*=\s*"\([^"]\+\)".*/\1/p' ../regovar/config.py || echo INVALID)
# RefGene
databases_path=$(shell test -f ../regovar/config.py && sed -n 's/^\s*DATABASES_DIR\s*=\s*"\([^"]\+\)".*/\1/p' ../regovar/config.py || echo INVALID)

init_config:
	cp config/config.default.py ../regovar/config.py

download_databases: \
	$(databases_path)/GRCh37/human_g1k_v37.fasta \
	$(databases_path)/GRCh37/human_g1k_v37.fasta.fai \
	$(databases_path)/hg19/refGene.txt \
	$(databases_path)/hg38/refGene.txt

$(databases_path)/GRCh37/human_g1k_v37.fasta:
	mkdir -p "$(dir $@)"
	curl -L ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/human_g1k_v37.fasta.gz | gunzip > $@

$(databases_path)/GRCh37/human_g1k_v37.fasta.fai:
	mkdir -p "$(dir $@)"
	curl -L ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/human_g1k_v37.fasta.fai > $@

$(databases_path)/hg19/refGene.txt:
	mkdir -p "$(dir $@)"
	curl -L http://hgdownload.soe.ucsc.edu/goldenPath/hg19/database/refGene.txt.gz | gunzip > $@

$(databases_path)/hg38/refGene.txt:
	mkdir -p "$(dir $@)"
	curl -L http://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/refGene.txt.gz | gunzip > $@

create_database:
	#psql -U postgres -c "DROP DATABASE IF EXISTS $(database_name)"
	psql -c "CREATE DATABASE $(database_name) OWNER regovar"
	psql -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""

fill_database:	
	psql -d $(database_name) -f create_all.sql
	psql -d $(database_name) -f install_hg19.sql
	psql -d $(database_name) -f install_hg38.sql

download_hpo:
	curl -L http://purl.obolibrary.org/obo/hp.obo -o $(databases_path)/hpo.obo
	curl -L http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/data_version.txt -o $(databases_path)/hpo_version.txt
	curl -L http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/phenotype_annotation.tab -o $(databases_path)/hpo_annotation.txt
	curl -L http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/negative_phenotype_annotation.tab -o $(databases_path)/hpo_annotation_neg.txt
	curl -L http://compbio.charite.de/jenkins/job/hpo.annotations.monthly/lastStableBuild/artifact/annotation/ALL_SOURCES_ALL_FREQUENCIES_diseases_to_genes_to_phenotypes.txt -o $(databases_path)/hpo_disease.txt
	curl -L http://compbio.charite.de/jenkins/job/hpo.annotations.monthly/lastStableBuild/artifact/annotation/ALL_SOURCES_ALL_FREQUENCIES_phenotype_to_genes.txt -o $(databases_path)/hpo_phenotype.txt

install_hpo:
	PYTHONPATH="$(CURDIR):$${PYTHONPATH}" python3 ../regovar/extradata.py hpo $(databases_path)/ "`cat $(databases_path)/hpo_version.txt`"

/etc/systemd/system/regovar.service:
	sed "s;{root};$(shell dirname $(install_dir));" $(install_dir)/systemd/regovar.service > $@

install_service: /etc/systemd/system/regovar.service

.PHONY: create_database download_databases download_hpo fill_database init_config install_hpo install_service
