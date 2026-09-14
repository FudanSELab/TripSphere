FROM busybox:1.37.0-uclibc AS healthcheck

FROM grafana/loki:3.6.4

COPY --from=healthcheck /bin/wget /bin/wget
