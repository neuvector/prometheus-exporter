FROM alpine:3.19.1
MAINTAINER support@neuvector.com

RUN apk add --no-cache python3 && \
    if [ ! -e /usr/bin/python ]; then ln -sf python3 /usr/bin/python ; fi && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --no-cache --upgrade pip setuptools prometheus_client requests
COPY nv_exporter.py /usr/local/bin
ENTRYPOINT ["python3", "-u", "/usr/local/bin/nv_exporter.py"]
