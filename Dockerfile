# syntax=docker/dockerfile:1.3-labs
FROM docker.io/python:3.10-slim-bookworm
MAINTAINER @penguincoder:hive.beehaw.org
LABEL org.opencontainers.image.source https://github.com/db0/pictrs-safety

ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN <<EOF
    set -eu
    apt-get -qq update
    apt-get -qq upgrade
    apt-get -qq install --no-install-recommends apt-utils dumb-init dnsutils > /dev/null
    apt-get -qq autoremove
    apt-get clean
    ln -s /usr/lib/libssl.so /usr/lib/libssl.so.1.1
    rm -rf /var/lib/apt/lists/*
    groupadd -r -g 991 pictrs
    useradd -r -u 991 -g 991 -s /sbin/false -M pictrs
    chown -R 991:991 /app
EOF

COPY --chown=991:991 . .
ENV PYTHONPATH='/app'
RUN pip install --no-cache-dir -r requirements.txt
USER pictrs
ENTRYPOINT [ "/usr/bin/dumb-init", "--" ]
STOPSIGNAL SIGINT
EXPOSE 14051
CMD ["python", "api_server.py", "-vvi"]
