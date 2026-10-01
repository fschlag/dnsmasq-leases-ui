"""Web UI for dnsmasq leases file."""

import os
import re
import ssl
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from http.client import HTTPConnection, HTTPSConnection
from ipaddress import ip_address

from flask import Flask, jsonify, render_template


__version__ = os.environ.get("APP_VERSION", "dev")
__release_date__ = os.environ.get("APP_RELEASE_DATE", "")
REPO_URL = "https://github.com/fschlag/dnsmasq-leases-ui"

DNSMASQ_LEASES_FILE = os.environ.get(
    "DNSMASQ_LEASES_FILE",
    "/var/lib/misc/dnsmasq.leases",
)
DNSMASQ_HOSTS_FILE = os.environ.get(
    "DNSMASQ_HOSTS_FILE",
    "/etc/dnsmasq.dhcphosts",
)

# Web UI detection.
#
# These values can be overridden through environment variables:
#
#   WEB_UI_TIMEOUT=0.5
#   WEB_UI_MAX_WORKERS=16
#
WEB_UI_TIMEOUT = float(os.environ.get("WEB_UI_TIMEOUT", "0.5"))
WEB_UI_MAX_WORKERS = int(os.environ.get("WEB_UI_MAX_WORKERS", "16"))


app = Flask(__name__)


MAC_RE = re.compile(r"^(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")

# A dhcp-host line may end with a per-host lease time ("12h", "45m", "3600",
# "infinite"), which is not a hostname.
LEASETIME_RE = re.compile(r"^(?:\d+[smhdw]?|infinite)$", re.IGNORECASE)

# Keywords dnsmasq accepts in a dhcp-host line where a hostname could stand.
DHCP_HOST_KEYWORDS = frozenset({"ignore"})


@dataclass
class LeaseEntry:
    # Keep the original JSON field name so the existing frontend continues
    # to work. Its meaning is now "DHCP reservation", not "infinite lease".
    staticIP: bool
    leasetime: str
    macAddress: str
    ipAddress: str
    name: str
    webUrl: str | None = None

    @classmethod
    def from_line(
        cls,
        leasetime: str,
        identifier: str,
        ip: str,
        name: str,
        client_id: str,
        reservations: "DhcpReservations",
    ) -> "LeaseEntry":
        # A host is a DHCP reservation when it is found in
        # /etc/dnsmasq.dhcphosts. This also works for DHCPv6 leases whose
        # current IPv6 address is different from the address in dhcp-hosts.
        #
        # An infinite lease still counts, so the column keeps working when the
        # dhcp-hosts file is not mounted: dnsmasq only writes lease time 0 for
        # a host configured with an infinite lease, never for a dhcp-range one.
        reserved = leasetime == "0" or reservations.matches(
            identifier=identifier,
            ip=ip,
            name=name,
            client_id=client_id,
        )

        # Keep the actual lease expiry visible. "Never" only means that
        # dnsmasq reported an infinite lease (lease time 0).
        if leasetime == "0":
            lease_end = "Never"
        else:
            lease_end = datetime.fromtimestamp(int(leasetime)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        return cls(
            staticIP=reserved,
            leasetime=lease_end,
            macAddress=identifier.upper(),
            ipAddress=ip,
            name=name,
        )


class DhcpReservations:
    """Reservations parsed from a dnsmasq dhcp-hosts file."""

    def __init__(self) -> None:
        self.ips: set[str] = set()
        self.names: set[str] = set()
        self.identifiers: set[str] = set()

    @staticmethod
    def _normalise_name(value: str) -> str:
        return value.strip().rstrip(".").casefold()

    @staticmethod
    def _normalise_identifier(value: str) -> str:
        return value.strip().casefold()

    def add_line(self, line: str) -> None:
        # Remove comments.
        line = line.split("#", 1)[0].strip()
        if not line:
            return

        fields = [field.strip() for field in line.split(",") if field.strip()]
        if not fields:
            return

        # Store explicit IPv4/IPv6 addresses and MAC addresses.
        for field in fields:
            candidate = field.strip("[]")

            try:
                self.ips.add(str(ip_address(candidate)))
                continue
            except ValueError:
                pass

            if MAC_RE.fullmatch(candidate):
                self.identifiers.add(self._normalise_identifier(candidate))

        # In the dhcp-host syntax used by this dnsmasq setup, the hostname
        # is the last ordinary field. Hostname matching is essential for
        # DHCPv6 because dnsmasq.leases can contain an IAID/DUID and an
        # IPv6 address that is not textually identical to dhcp-hosts.
        for field in reversed(fields):
            candidate = field.strip().strip("[]")
            lower = candidate.casefold()

            if not candidate:
                continue

            try:
                ip_address(candidate)
                continue
            except ValueError:
                pass

            if MAC_RE.fullmatch(candidate):
                continue

            # Skip a trailing lease time: "02:aa:...:14,iPhone-Three,12h"
            # names the host iPhone-Three, not 12h.
            if LEASETIME_RE.fullmatch(candidate) or lower in DHCP_HOST_KEYWORDS:
                continue

            if (
                lower.startswith(
                    (
                        "set:",
                        "tag:",
                        "id:",
                        "net:",
                        "bootfile=",
                        "pxe-service=",
                        "dhcp-option=",
                    )
                )
                or "=" in candidate
            ):
                continue

            self.names.add(self._normalise_name(candidate))
            break

        # Preserve non-MAC identifiers in the first field as well.
        first = fields[0].strip().strip("[]")

        if first and not MAC_RE.fullmatch(first):
            try:
                ip_address(first)
            except ValueError:
                lower = first.casefold()

                if lower.startswith("id:"):
                    # dnsmasq keys a reservation by client-id or DUID as
                    # "id:<hex>", and the leases file carries that same value
                    # in its client-id field.
                    client_id = first[3:].strip()

                    if client_id and client_id != "*":
                        self.identifiers.add(self._normalise_identifier(client_id))

                elif not lower.startswith(
                    ("set:", "tag:", "net:", "bootfile=")
                ):
                    self.identifiers.add(self._normalise_identifier(first))

    def matches(
        self,
        identifier: str,
        ip: str,
        name: str,
        client_id: str,
    ) -> bool:
        # 1. Exact IP match.
        try:
            if str(ip_address(ip)) in self.ips:
                return True
        except ValueError:
            pass

        # 2. Hostname match.
        if name and self._normalise_name(name) in self.names:
            return True

        # 3. MAC/client identifier match.
        if (
            identifier
            and self._normalise_identifier(identifier)
            in self.identifiers
        ):
            return True

        return bool(
            client_id
            and self._normalise_identifier(client_id)
            in self.identifiers
        )


def read_reservations() -> DhcpReservations:
    reservations = DhcpReservations()

    try:
        with open(DNSMASQ_HOSTS_FILE, encoding="utf-8") as f:
            for line in f:
                reservations.add_line(line)
    except OSError:
        # Optional file: preserve the original behaviour when it is not
        # mounted, and do not fail the page when it is there but unreadable.
        pass

    return reservations


def _check_http(host: str, use_https: bool) -> str | None:
    """
    Check whether a host responds as an HTTP/HTTPS server.

    Returns the corresponding URL if a valid HTTP response is received.
    Returns None otherwise.

    HTTPS certificate verification is intentionally disabled here because
    local devices commonly use self-signed certificates.
    """
    connection = None

    try:
        if use_https:
            context = ssl._create_unverified_context()
            connection = HTTPSConnection(
                host,
                443,
                timeout=WEB_UI_TIMEOUT,
                context=context,
            )
        else:
            connection = HTTPConnection(
                host,
                80,
                timeout=WEB_UI_TIMEOUT,
            )

        connection.request(
            "GET",
            "/",
            headers={
                "Connection": "close",
                "User-Agent": "dnsmasq-leases-ui",
            },
        )

        response = connection.getresponse()

        # Reading one byte is enough to make sure we actually received an
        # HTTP response without downloading an entire web page.
        response.read(1)

        if 100 <= response.status <= 599:
            scheme = "https" if use_https else "http"

            # IPv6 URLs require square brackets.
            if ":" in host:
                return f"{scheme}://[{host}]"

            return f"{scheme}://{host}"

    except (OSError, ValueError):
        pass
    finally:
        if connection is not None:
            try:
                connection.close()
            except OSError:
                pass

    return None


def check_web_ui(ip: str) -> str | None:
    """
    Check whether an HTTP or HTTPS web UI is available.

    HTTP is checked first. If no HTTP server is found, HTTPS is checked.
    """
    try:
        parsed_ip = ip_address(ip)
        host = str(parsed_ip)
    except ValueError:
        return None

    url = _check_http(host, use_https=False)

    if url is not None:
        return url

    return _check_http(host, use_https=True)


def add_web_urls(leases: list[LeaseEntry]) -> None:
    """
    Check all lease IPs in parallel and attach a web URL where available.
    """
    if not leases:
        return

    worker_count = min(
        max(1, WEB_UI_MAX_WORKERS),
        len(leases),
    )

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        urls = list(
            executor.map(
                lambda lease: check_web_ui(lease.ipAddress),
                leases,
            )
        )

    for lease, url in zip(leases, urls):
        lease.webUrl = url


def read_leases() -> list[LeaseEntry]:
    leases: list[LeaseEntry] = []
    reservations = read_reservations()

    with open(DNSMASQ_LEASES_FILE, encoding="utf-8") as f:
        for line in f:
            parts = line.split()

            # dnsmasq.leases format:
            # lease-end identifier ip hostname client-id
            if len(parts) != 5:
                continue

            # A corrupt lease time must not take down the whole page.
            # dnsmasq writes a plain integer (0 for an infinite lease).
            if not parts[0].isdigit():
                continue

            leases.append(
                LeaseEntry.from_line(
                    parts[0],
                    parts[1],
                    parts[2],
                    parts[3],
                    parts[4],
                    reservations,
                )
            )

    add_web_urls(leases)

    return leases


@app.route("/")
def index():
    return render_template(
        "index.html",
        version=__version__,
        release_date=__release_date__,
        repo_url=REPO_URL,
    )


@app.route("/leases")
def get_leases():
    try:
        leases = read_leases()
    except OSError as exc:
        # A missing or unreadable leases file is a deployment problem
        # (mount typo, permissions), not a crash.
        app.logger.warning(
            "cannot read %s: %s",
            DNSMASQ_LEASES_FILE,
            exc,
        )
        return jsonify(error="leases file unavailable"), 503

    return jsonify(
        leases=[asdict(lease) for lease in leases]
    )


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
    )
