# CLAUDE.md

File guide Claude Code (claude.ai/code) when work code this repo.

## Commands

Run local (venv at `.venv/`, already provisioned):
```
.venv/bin/python dnsmasq_leases_ui.py
```
Recreate if gone: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
Serve `0.0.0.0:5000` (dev = Flask dev server; container = gunicorn). Read `/var/lib/misc/dnsmasq.leases` (`DNSMASQ_LEASES_FILE`) + optional `/etc/dnsmasq.dhcphosts` (`DNSMASQ_HOSTS_FILE`) — missing hosts file not error.

Docker build/run:
```
docker build -t dnsmasq-leases-ui .
docker run -p 5000:5000 -v /var/lib/misc/dnsmasq.leases:/var/lib/misc/dnsmasq.leases:ro dnsmasq-leases-ui
```
`docker build` under the buildx docker-container driver not load image into daemon — add `--load`, else `docker run` fail "pull access denied" (affect `local/run-local.sh` too).

Local Docker test with sample leases:
```
./local/run-local.sh          # port 5000
./local/run-local.sh 8080     # override host port
```
Build image, mount `local/dnsmasq.leases.sample` as leases file, run foreground (`--rm -it`).

Tests via `pytest` (`tests/`, fixtures in `tests/samples.py` captured from a real dnsmasq 2.90):
```
.venv/bin/python -m pytest
.venv/bin/python -m pytest --cov=dnsmasq_leases_ui --cov-report=term-missing   # coverage
node --test 'tests/js/*.test.mjs'   # lease-table js (node 24 reject a bare directory)
```
`leases` fixture (`tests/conftest.py`) monkeypatch the two path globals (read per call, so patch work). Never hardcode a formatted lease-end in test — `datetime.fromtimestamp` is local time, container run UTC.
Table JS live in `static/leases.js` (pure) + `static/app.js` (DOM wiring + fetch); `tests/js/` cover both, the latter through `dom-stub.mjs` (no browser). app.js run its fetch at import time and ESM cache per process, so each import need it own test file. `tests/test_template.py` only assert the page reference the module.

Lint + format via `ruff` (config in `pyproject.toml`):
```
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check .        # lint
.venv/bin/ruff format .       # auto-format
.venv/bin/ruff format --check . && .venv/bin/ruff check .   # CI-style verify
```
`.github/workflows/ci.yml` run three job on every PR and on `main`: `python` (ruff + pytest, 3.12), `js` (`node --test`), `docker` (build image, serve sample leases, assert `/`, `/leases`, both module and the icon answer 200).
`ruff>=0.8` unpinned: local venv 0.15, fresh CI install 0.16 — format rule can drift between them.

Local test without real dnsmasq: `local/dnsmasq.leases.sample` ship fixture lines (IPv4 dynamic, IPv4 static, IPv6, server `duid` line). Override via env var:
```
DNSMASQ_LEASES_FILE="$PWD/local/dnsmasq.leases.sample" .venv/bin/python dnsmasq_leases_ui.py
```
`HOST` and `PORT` env vars also override dev-server bind (gunicorn ignore; use `-b` instead).
On macOS port 5000 is AirPlay Receiver — every request answer 403 and the dev server never bind. Use `PORT=5099` locally.

Validate against real dnsmasq (unit test not cover lease-file shape):
```
docker network create --subnet 172.31.77.0/24 dhcptest     # add --ipv6 --subnet fd00:77::/64 for DHCPv6
# alpine + `apk add dnsmasq dhcpcd`; run `dnsmasq -k` with dhcp-range + dhcp-hostsfile + dhcp-leasefile in a bind-mounted dir, then mount that leases file into the UI container
docker run --mac-address <mac> ... udhcpc -i eth0 -n -q -f -s /bin/true -x hostname:<name>   # DHCPv4 client
docker run --mac-address <mac> --privileged ... dhcpcd -6 -h <name> -t 25 eth0               # DHCPv6 client
```
`dhcpcd -6` need `--privileged` (else `if_init: Read-only file system`); DHCPv6 need `enable-ra` in dnsmasq conf. `docker kill -s HUP` reload dhcp-hostsfile.

## Architecture

Single-file Flask app (`dnsmasq_leases_ui.py`) + one Jinja template (`templates/index.html`) + two ES module in `static/`.

- `/` → render `index.html`, which load `static/app.js` (ES module, `script_root` pass via a `<body data-script-root>` attribute). JS fetch `/leases`, sort + build table via `textContent` (no HTML injection). Template hold no lease data. Pre-paint theme script stay inline on purpose.
- `/leases` → parse dnsmasq leases file per request, return JSON. Sort client-side only. Unreadable leases file → 503 `{"error": ...}` (frontend show its banner); dhcp-hosts file unreadable → ignored, it is optional.

Lease file format: space-separated `leasetime mac ip name client-id` per line. Lines without exactly 5 fields skipped — filter out IPv6 `duid ...` server-id line dnsmasq write when serve IPv6 (see commit 3639347).

DHCPv6 line differ: field 2 = IAID (decimal, not MAC), field 5 = DUID, address often not the one in `dhcp-hosts` — hostname or DUID is the only link to its reservation. `dhcp-host` line may end with per-host lease time (`12h`, `infinite`) which is not a hostname. `dhcp-host=id:<duid>,name` key by client-id/DUID (`id:*` deliberately ignored: leases file write `*` for "no client-id").

`LeaseEntry.staticIP` = `True` when lease match a `dnsmasq.dhcphosts` reservation (IP, hostname, or MAC/DUID) **or** `leasetime == '0'` (infinite lease — keep column work when hosts file not mounted). JSON key keep old name; UI header say "DHCP Reservation". Client `cmp()` put reservations first, sort IPv4 numerically by octet tuple.

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