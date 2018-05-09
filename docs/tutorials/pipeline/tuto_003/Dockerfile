# BASE IMAGE
FROM biocontainers/biocontainers:latest

# Install samtools
RUN conda install samtools=1.3.1

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



