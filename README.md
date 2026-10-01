# dnsmasq-leases-ui

[![release](https://img.shields.io/github/v/release/fschlag/dnsmasq-leases-ui)](https://github.com/fschlag/dnsmasq-leases-ui/releases)
[![ghcr](https://img.shields.io/badge/ghcr.io-fschlag%2Fdnsmasq--leases--ui-blue?logo=github)](https://github.com/fschlag/dnsmasq-leases-ui/pkgs/container/dnsmasq-leases-ui)
[![docker hub](https://img.shields.io/docker/pulls/fschlag/dnsmasq-leases-ui?logo=docker)](https://hub.docker.com/r/fschlag/dnsmasq-leases-ui)
[![license](https://img.shields.io/github/license/fschlag/dnsmasq-leases-ui)](LICENSE)

Tiny web UI for the [dnsmasq](https://thekelleys.org.uk/dnsmasq/doc.html) DHCP leases file. Sortable, searchable table with dark mode and a JSON endpoint.

![Screenshot](https://raw.githubusercontent.com/anonymous-writer/dnsmasq-leases-ui/main/docs/screenshot.png)

## Features

- Sortable, searchable table of all active DHCP leases
- Automatically detects HTTP/HTTPS web interfaces and makes reachable device IPs clickable
- Sticky header, dark / light mode (follows OS, override persisted)
- JSON API at `/leases` for scripts and monitoring
- Static leases listed first, IPv4 sorted numerically
- Multi-arch image: `linux/amd64`, `linux/arm64`, `linux/arm/v7` (Raspberry Pi)
- Tiny (~60 MB), runs as non-root, healthchecked

## Run

### Docker

Pull from either registry:

```bash
docker run -d --name dnsmasq-leases-ui \
  -p 5000:5000 \
  -v /var/lib/misc/dnsmasq.leases:/var/lib/misc/dnsmasq.leases:ro \
  -v /etc/dnsmasq.dhcphosts:/etc/dnsmasq.dhcphosts:ro \
  ghcr.io/fschlag/dnsmasq-leases-ui:latest
  # or: fschlag/dnsmasq-leases-ui:latest  (Docker Hub)
