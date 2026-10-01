# dnsmasq-leases-ui

[![release](https://img.shields.io/github/v/release/fschlag/dnsmasq-leases-ui)](https://github.com/fschlag/dnsmasq-leases-ui/releases)
[![ghcr](https://img.shields.io/badge/ghcr.io-fschlag%2Fdnsmasq--leases--ui-blue?logo=github)](https://github.com/fschlag/dnsmasq-leases-ui/pkgs/container/dnsmasq-leases-ui)
[![docker hub](https://img.shields.io/docker/pulls/fschlag/dnsmasq-leases-ui?logo=docker)](https://hub.docker.com/r/fschlag/dnsmasq-leases-ui)
[![license](https://img.shields.io/github/license/fschlag/dnsmasq-leases-ui)](LICENSE)

Tiny web UI for the [dnsmasq](https://thekelleys.org.uk/dnsmasq/doc.html) DHCP leases file. Sortable, searchable table with dark mode and a JSON endpoint.

![Screenshot](https://raw.githubusercontent.com/fschlag/dnsmasq-leases-ui/main/docs/screenshot.png)

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
```

Open `http://<host>:5000`.

The `dnsmasq.dhcphosts` mount is optional. Without it only reservations with an
infinite lease are recognised, because that is all the leases file reveals; mount
it to also flag reservations that are served with a normal lease time. Override
either path with `DNSMASQ_LEASES_FILE` / `DNSMASQ_HOSTS_FILE`.

For IPv6 web-interface detection, the container must be able to reach the host's
IPv6 LAN. With Docker or Podman, host networking can be used:

```bash
docker run -d --name dnsmasq-leases-ui \
  --network host \
  -e PORT=5000 \
  -v /var/lib/misc/dnsmasq.leases:/var/lib/misc/dnsmasq.leases:ro \
  -v /etc/dnsmasq.dhcphosts:/etc/dnsmasq.dhcphosts:ro \
  ghcr.io/fschlag/dnsmasq-leases-ui:latest
```

When using host networking, do not use `-p` because the application listens
directly on the host network.

### docker-compose

```yaml
services:
  dnsmasq-leases-ui:
    image: ghcr.io/fschlag/dnsmasq-leases-ui:latest
    ports: ["5000:5000"]
    volumes:
      - /var/lib/misc/dnsmasq.leases:/var/lib/misc/dnsmasq.leases:ro
      - /etc/dnsmasq.dhcphosts:/etc/dnsmasq.dhcphosts:ro
    restart: unless-stopped
```

For IPv6 web-interface detection, use host networking:

```yaml
services:
  dnsmasq-leases-ui:
    image: ghcr.io/fschlag/dnsmasq-leases-ui:latest
    network_mode: host
    environment:
      - PORT=5000
    volumes:
      - /var/lib/misc/dnsmasq.leases:/var/lib/misc/dnsmasq.leases:ro
      - /etc/dnsmasq.dhcphosts:/etc/dnsmasq.dhcphosts:ro
    restart: unless-stopped
```

With `network_mode: host`, the `ports` mapping is not used. The application
listens directly on the configured `PORT`.

### From source

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python dnsmasq_leases_ui.py
```

## Endpoints

| Path      | Returns                  |
|-----------|--------------------------|
| `/`       | HTML UI                  |
| `/leases` | JSON `{ leases: [...] }` |

## Configuration

| Env var               | Default                          | Description                              |
|-----------------------|----------------------------------|------------------------------------------|
| `DNSMASQ_LEASES_FILE` | `/var/lib/misc/dnsmasq.leases`   | Path to the leases file                  |
| `DNSMASQ_HOSTS_FILE`  | `/etc/dnsmasq.dhcphosts`         | Path to the dnsmasq hosts file           |
| `HOST`                | `0.0.0.0`                        | Dev-server bind host (gunicorn ignores)  |
| `PORT`                | `5000`                           | Dev-server bind port (gunicorn ignores)  |

The `dnsmasq.dhcphosts` file is optional. If it is not available, the UI
continues to work, but reservations configured only in that file cannot be
detected. Infinite leases (`lease time 0`) are still shown as DHCP reservations.

For automatic detection of device web interfaces, the application checks
HTTP and HTTPS on the lease IP addresses. IPv6 web-interface detection requires
IPv6 connectivity from the container to the LAN.

With Docker or Podman, `network_mode: host` can be used when the host's IPv6
network must be reached. This gives the container access to the host's network
interfaces and IPv6 routes.

Behind a reverse proxy on a subpath, set `SCRIPT_NAME` in your proxy / WSGI config — the UI honors `request.script_root`.

## Contributing

Issues and PRs welcome. See [CLAUDE.md](CLAUDE.md) for the dev setup, commit conventions, and release flow.

## Credits

- Theme-toggle icons: [Feather Icons](https://feathericons.com/) (MIT)
- Favicon: [Lucide](https://lucide.dev/) (ISC)

Full attributions in [NOTICE](NOTICE).

## License

MIT — see [LICENSE](LICENSE).
