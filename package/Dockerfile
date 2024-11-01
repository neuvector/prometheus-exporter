FROM registry.suse.com/bci/python:3.12

ARG COMMIT
ARG VERSION

RUN python3 -m venv .venv && source .venv/bin/activate && pip3 install --upgrade pip setuptools prometheus_client requests
COPY startup.sh /usr/local/bin
COPY nv_exporter.py /usr/local/bin

LABEL "name"="prometheus-exporter" \
      "vendor"="SUSE Security" \
      "neuvector.image"="neuvector/prometheus-exporter" \
      "neuvector.role"="prometheus-exporter" \
      "neuvector.rev"="${COMMIT}" \
      "io.artifacthub.package.logo-url"=https://avatars2.githubusercontent.com/u/19367275 \
      "io.artifacthub.package.readme-url"="https://raw.githubusercontent.com/neuvector/prometheus-exporter/${VERSION}/README.md" \
      "org.opencontainers.image.description"="SUSE Security Prometheus Exporter" \
      "org.opencontainers.image.title"="SUSE Security Prometheus Exporter" \
      "org.opencontainers.image.source"="https://github.com/neuvector/prometheus-exporter/" \
      "org.opencontainers.image.version"="${VERSION}" \
      "org.opensuse.reference"="neuvector/prometheus-exporter:${VERSION}"

ENTRYPOINT ["startup.sh"]
