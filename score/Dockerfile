FROM iconloop/tbears:1.7.2 as base
WORKDIR /work
COPY tests/config/entry.sh /usr/local/bin
RUN chmod +x /usr/local/bin/entry.sh
RUN mkdir scripts
COPY tests/config/register_preps.py /work/scripts
