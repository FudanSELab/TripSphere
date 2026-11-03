FROM alpine:3.20

ARG ALPINE_MIRROR_URL=https://mirrors.aliyun.com/alpine

RUN sed -i "s#https://dl-cdn.alpinelinux.org/alpine#${ALPINE_MIRROR_URL}#g" /etc/apk/repositories \
    && apk add --no-cache fio stress-ng
