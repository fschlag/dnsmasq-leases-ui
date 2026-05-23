# dnsmasq-leases-ui

[![release](https://img.shields.io/github/v/release/fschlag/dnsmasq-leases-ui)](https://github.com/fschlag/dnsmasq-leases-ui/releases)
[![ghcr](https://img.shields.io/badge/ghcr.io-fschlag%2Fdnsmasq--leases--ui-blue?logo=github)](https://github.com/fschlag/dnsmasq-leases-ui/pkgs/container/dnsmasq-leases-ui)
[![docker hub](https://img.shields.io/docker/pulls/fschlag/dnsmasq-leases-ui?logo=docker)](https://hub.docker.com/r/fschlag/dnsmasq-leases-ui)
[![license](https://img.shields.io/github/license/fschlag/dnsmasq-leases-ui)](LICENSE)

Tiny web UI for the [dnsmasq](https://thekelleys.org.uk/dnsmasq/doc.html) DHCP leases file. Sortable, searchable table with dark mode and a JSON endpoint.

![Screenshot](https://raw.githubusercontent.com/fschlag/docs/master/dnsmasq-leases-ui-docs/screenshot_1.png)

## Features

- Sortable, searchable table of all active DHCP leases
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
  ghcr.io/fschlag/dnsmasq-leases-ui:latest
  # or: fschlag/dnsmasq-leases-ui:latest  (Docker Hub)
```

Open `http://<host>:5000`.

### docker-compose

```yaml
services:
  dnsmasq-leases-ui:
    image: ghcr.io/fschlag/dnsmasq-leases-ui:latest
    ports: ["5000:5000"]
    volumes:
      - /var/lib/misc/dnsmasq.leases:/var/lib/misc/dnsmasq.leases:ro
    restart: unless-stopped
```

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
| `HOST`                | `0.0.0.0`                        | Dev-server bind host (gunicorn ignores)  |
| `PORT`                | `5000`                           | Dev-server bind port (gunicorn ignores)  |

Behind a reverse proxy on a subpath, set `SCRIPT_NAME` in your proxy / WSGI config — the UI honors `request.script_root`.

## Contributing

Issues and PRs welcome. See [CLAUDE.md](CLAUDE.md) for the dev setup, commit conventions, and release flow.

## Credits

Theme-toggle icons: [Feather Icons](https://feathericons.com/) (MIT, see [NOTICE](NOTICE)).

## License

MIT — see [LICENSE](LICENSE).
