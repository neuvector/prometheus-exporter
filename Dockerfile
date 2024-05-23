FROM alpine:3.20.0
MAINTAINER support@neuvector.com

RUN apk add --no-cache python3 && \
    if [ ! -e /usr/bin/python ]; then ln -sf python3 /usr/bin/python ; fi && \
    python3 -m venv .venv && \
    source .venv/bin/activate && \
    pip3 install --upgrade pip setuptools prometheus_client requests
COPY startup.sh /usr/local/bin
COPY nv_exporter.py /usr/local/bin
ENTRYPOINT ["startup.sh"]
