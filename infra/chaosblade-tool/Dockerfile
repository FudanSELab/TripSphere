FROM ubuntu:24.04

ARG CHAOSBLADE_VERSION=1.8.1
ARG CHAOSBLADE_TARBALL_URL=https://github.com/chaosblade-io/chaosblade/releases/download/v${CHAOSBLADE_VERSION}/chaosblade-${CHAOSBLADE_VERSION}-linux_amd64.tar.gz

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gzip tar \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "${CHAOSBLADE_TARBALL_URL}" -o /tmp/chaosblade.tar.gz \
    && mkdir -p /opt \
    && tar -xzf /tmp/chaosblade.tar.gz -C /opt \
    && blade_dir="$(find /opt -maxdepth 1 -type d -name 'chaosblade-*' | head -n 1)" \
    && test -n "${blade_dir}" \
    && mv "${blade_dir}" /opt/chaosblade \
    && chmod +x /opt/chaosblade/blade \
    && cp /tmp/chaosblade.tar.gz /opt/chaosblade/chaosblade.tar.gz \
    && ln -s /opt/chaosblade/blade /usr/local/bin/blade

ENV PATH="/opt/chaosblade:${PATH}"

CMD ["tail", "-f", "/dev/null"]
