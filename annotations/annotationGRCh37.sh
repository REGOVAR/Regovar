#! /bin/sh

if [ $# -ne 2 ]; then
    echo "Usage: $(basename $0) input.vcf output.vcf" >&2
    exit 1
fi

input="$(readlink -f $1)"
output="$(readlink -f $2)"

# VEP
/opt/ensembl/91/vep/homo_sapiens_merged/91_GRCh37/  \
    --fork 30 \
    --buffer_size 200000 \
    --cache --dir /opt/ensembl/vep/91/homo_sapiens_merged/91_GRCh37/ --offline \
    --fasta FIXME \
    --db_version 91 \
    --species homo_sapiens \
    --assembly GRCh37 \
    --no_escape \
    --vcf_info_field CSQ \
    --terms ensembl \
    --hgvs \
    --hgvsg \
    --shift_hgvs 1 \
    --transcript_version \
    --protein \
    --symbol \
    --ccds \
    --uniprot \
    --appris \
    --canonical \
    --biotype \
    --check_existing \
    --af \
    --max_af \
    --af_1kg \
    --af_esp \
    --af_gnomad \
    --af_exac \
    --pubmed \
    --all_refseq \
    --exclude_predicted \
    --allow_non_variant \
    --format vcf \
    --vcf \
    --compress_output bgzip \
    --no_stats \
    -i "$input" \
-o "$output"

# SnpEff
java -jar -Xmx16g ~/tools/snpEff/snpEff.jar \
     eff GRCh37.75 \
     -t \
     -i vcf \
     -o vcf \
     -nodownload \
     -sequenceOntology \
     -lof \
     -noStats \
     "$input" \
> "$output"


