# CLAUDE.md

File guide Claude Code (claude.ai/code) when work code this repo.

## Commands

Run local (venv at `.venv/`, already provisioned):
```
.venv/bin/python dnsmasq_leases_ui.py
```
Recreate if gone: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
Serve `0.0.0.0:5000` (dev = Flask dev server; container = gunicorn). Read `/var/lib/misc/dnsmasq.leases` (path hardcoded in `DNSMASQ_LEASES_FILE`).

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
Build image, mount `local/dnsmasq.leases.sample` as leases file, run foreground (`--rm -it`).

No tests. Lint + format via `ruff` (config in `pyproject.toml`):
```
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check .        # lint
.venv/bin/ruff format .       # auto-format
.venv/bin/ruff format --check . && .venv/bin/ruff check .   # CI-style verify
```

Local test without real dnsmasq: `local/dnsmasq.leases.sample` ship fixture lines (IPv4 dynamic, IPv4 static, IPv6, server `duid` line). Override via env var:
```
DNSMASQ_LEASES_FILE="$PWD/local/dnsmasq.leases.sample" .venv/bin/python dnsmasq_leases_ui.py
```
`HOST` and `PORT` env vars also override dev-server bind (gunicorn ignore; use `-b` instead).

## Architecture

Single-file Flask app (`dnsmasq_leases_ui.py`) + one Jinja template (`templates/index.html`).

- `/` → render `index.html`. Client-side vanilla JS fetch `/leases`, sort + build table in browser via `textContent` (no HTML injection). Template hold no lease data.
- `/leases` → parse dnsmasq leases file per request, return JSON. Sort client-side only.

Lease file format: space-separated `leasetime mac ip name client-id` per line. Lines without exactly 5 fields skipped — filter out IPv6 `duid ...` server-id line dnsmasq write when serve IPv6 (see commit 3639347).

`LeaseEntry.staticIP` = `True` when `leasetime == '0'`. Client `cmp()` put static first, sort IPv4 numerically by octet tuple.

## Commit conventions

- **Conventional Commits**: `type(scope): subject`. Types used: `feat`, `fix`, `chore`, `docs`, `refactor`. Scope optional (e.g. `feat(ui): ...`).
- **Subject**: one line, lowercase, no trailing period, ≤72 chars. Imperative ("add", "fix", not "added"/"fixes").
- **Body**: skip unless *why* not obvious from subject + diff.
- **No co-author / tool attribution lines** (no `Co-Authored-By: Claude …`, no `Generated with …` footers).
- **One topic per commit** when practical. Bundling related UI tweaks (e.g. sticky header + search + footer one commit) fine; mixing unrelated refactors not.
- Examples from repo history:
  - `feat(ui): sticky header, search filter, footer with version; expand sample to 200 entries`
  - `chore: modernize to Python 3.12, Flask 3, gunicorn, ruff; fix XSS in lease table`
  - `feat: improve sorting`
- Never use `--no-verify`, `--amend` on pushed commits, or force-push to `main`.