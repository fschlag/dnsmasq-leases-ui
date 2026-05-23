# syntax=docker/dockerfile:1.7
FROM python:3.12-alpine

LABEL org.opencontainers.image.title="dnsmasq-leases-ui" \
      org.opencontainers.image.description="Web UI for dnsmasq DHCP leases" \
      org.opencontainers.image.source="https://github.com/fschlag/dnsmasq-leases-ui" \
      org.opencontainers.image.url="https://github.com/fschlag/dnsmasq-leases-ui" \
      org.opencontainers.image.licenses="MIT"

ARG APP_VERSION=dev
ARG APP_RELEASE_DATE=
ENV APP_VERSION=${APP_VERSION} APP_RELEASE_DATE=${APP_RELEASE_DATE}

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY templates ./templates
COPY dnsmasq_leases_ui.py NOTICE ./

USER nobody

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget -qO- http://127.0.0.1:5000/leases >/dev/null || exit 1

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "dnsmasq_leases_ui:app"]
