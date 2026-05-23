# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Run locally (venv at `.venv/`, already provisioned):
```
.venv/bin/python dnsmasq-leases-ui.py
```
Recreate if missing: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
Serves on `0.0.0.0:5000`. Reads `/var/lib/misc/dnsmasq.leases` (path hardcoded in `DNSMASQ_LEASES_FILE`).

Docker build/run:
```
docker build -t dnsmasq-leases-ui .
docker run -p 5000:5000 -v /var/lib/misc/dnsmasq.leases:/var/lib/misc/dnsmasq.leases:ro dnsmasq-leases-ui
```

Local Docker test with sample leases:
```
./run-local.sh          # port 5000
./run-local.sh 8080     # override host port
```
Builds image, mounts `dnsmasq.leases.sample` as the leases file, runs foreground (`--rm -it`).

No tests, no linter configured.

Local testing without real dnsmasq: `dnsmasq.leases.sample` ships fixture lines (IPv4 dynamic, IPv4 static, IPv6, server `duid` line). Override the hardcoded path via env-edit or symlink:
```
sudo ln -s "$PWD/dnsmasq.leases.sample" /var/lib/misc/dnsmasq.leases
```
or patch `DNSMASQ_LEASES_FILE` for the session.

## Architecture

Single-file Flask app (`dnsmasq-leases-ui.py`) + one Jinja template (`templates/index.html`).

- `/` → renders `index.html`. Client-side JS (jQuery from CDN) fetches `/leases` and builds the table in the browser. Template itself contains no lease data.
- `/leases` → parses dnsmasq leases file on each request, returns JSON.

Lease file format expected: space-separated `leasetime mac ip name client-id` per line. Lines without exactly 5 fields are skipped — this filters out the IPv6 `duid ...` server-id line that dnsmasq writes when serving IPv6 (see commit 3639347).

`LeaseEntry.staticIP` is `True` when `leasetime == '0'`. Sort key (`leaseSort`) prefixes static entries with `'0'` so they list before dynamic entries, then sorts by IP string (lexicographic, not numeric — `192.168.0.10` sorts before `192.168.0.2`).
