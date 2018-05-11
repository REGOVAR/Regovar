#/Regovar/Regovar/install/NewMakefile

database_name=$(shell sed -n 's/^\s*DATABASE_NAME\s*=\s*"\([^"]\+\)".*/\1/p' config.py) # PostgreSQL
databases_path=$(shell sed -n 's/^\s*DATABASES_DIR\s*=\s*"\([^"]\+\)".*/\1/p' config.py) # RefGene

download_refgene: \
	$(databases_path)/hg19/refGene.txt \
	$(databases_path)/hg38/refGene.txt
	
$(databases_path)/hg19/refGene.txt:
	curl http://hgdownload.soe.ucsc.edu/goldenPath/hg19/database/refGene.txt.gz | gunzip > $@

$(databases_path)/hg38/refGene.txt:
	curl http://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/refGene.txt.gz | gunzip > $@

download_hpo:
	curl http://purl.obolibrary.org/obo/hp.obo -o $(databases_path)/hpo.obo
	curl http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/data_version.txt -o $(databases_path)/hpo_version.txt
	curl http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/phenotype_annotation.tab -o $(databases_path)/hpo_annotation.txt
	curl http://compbio.charite.de/jenkins/job/hpo.annotations/lastSuccessfulBuild/artifact/misc/negative_phenotype_annotation.tab -o $(databases_path)/hpo_annotation_neg.txt
	curl http://compbio.charite.de/jenkins/job/hpo.annotations.monthly/lastStableBuild/artifact/annotation/ALL_SOURCES_ALL_FREQUENCIES_diseases_to_genes_to_phenotypes.txt -o $(databases_path)/hpo_disease.txt
	curl http://compbio.charite.de/jenkins/job/hpo.annotations.monthly/lastStableBuild/artifact/annotation/ALL_SOURCES_ALL_FREQUENCIES_phenotype_to_genes.txt -o $(databases_path)/hpo_phenotype.txt

install_hpo: download_hpo
	python3 ../regovar/extratools/hpo.py $(databases_path) "`cat $(databases_path)/hpo_version.txt`"
	
init_config:
	cp config.default.py ../config.py

setup_database:
	#psql -U postgres -c "DROP DATABASE IF EXISTS $(database_name)"
	psql -U postgres -c "CREATE DATABASE $(database_name) OWNER regovar"
	psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""
	psql -U regovar -d $(database_name) -f create_all.sql
	psql -U regovar -d $(database_name) -f install_hg19.sql
	psql -U regovar -d $(database_name) -f install_hg38.sql


	
.PHONY: download_refgene download_hpo install_hpo init_config setup_database
