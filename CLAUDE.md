# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Run locally (venv at `.venv/`, already provisioned):
```
.venv/bin/python dnsmasq_leases_ui.py
```
Recreate if missing: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
Serves on `0.0.0.0:5000` (dev mode uses Flask dev server; container uses gunicorn). Reads `/var/lib/misc/dnsmasq.leases` (path hardcoded in `DNSMASQ_LEASES_FILE`).

Docker build/run:
```
docker build -t dnsmasq-leases-ui .
docker run -p 5000:5000 -v /var/lib/misc/dnsmasq.leases:/var/lib/misc/dnsmasq.leases:ro dnsmasq-leases-ui
```

Local Docker test with sample leases:
```
./local/run-local.sh          # port 5000
./local/run-local.sh 8080     # override host port
```
Builds image, mounts `local/dnsmasq.leases.sample` as the leases file, runs foreground (`--rm -it`).

No tests. Lint + format via `ruff` (config in `pyproject.toml`):
```
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check .        # lint
.venv/bin/ruff format .       # auto-format
.venv/bin/ruff format --check . && .venv/bin/ruff check .   # CI-style verify
```

Local testing without real dnsmasq: `local/dnsmasq.leases.sample` ships fixture lines (IPv4 dynamic, IPv4 static, IPv6, server `duid` line). Override via env var:
```
DNSMASQ_LEASES_FILE="$PWD/local/dnsmasq.leases.sample" .venv/bin/python dnsmasq_leases_ui.py
```
`HOST` and `PORT` env vars also override dev-server bind (gunicorn ignores; configure via `-b` instead).

## Architecture

Single-file Flask app (`dnsmasq_leases_ui.py`) + one Jinja template (`templates/index.html`).

- `/` → renders `index.html`. Client-side vanilla JS fetches `/leases`, sorts and builds the table in the browser using `textContent` (no HTML injection). Template itself contains no lease data.
- `/leases` → parses dnsmasq leases file on each request, returns JSON. Sorting is client-side only.

Lease file format expected: space-separated `leasetime mac ip name client-id` per line. Lines without exactly 5 fields are skipped — this filters out the IPv6 `duid ...` server-id line that dnsmasq writes when serving IPv6 (see commit 3639347).

`LeaseEntry.staticIP` is `True` when `leasetime == '0'`. Client `cmp()` puts static entries first, sorts IPv4 numerically by octet tuple.
