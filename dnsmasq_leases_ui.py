
"""Web UI for dnsmasq leases file."""

from dataclasses import asdict, dataclass
from datetime import datetime
from ipaddress import ip_address
import os
import re

from flask import Flask, jsonify, render_template

__version__ = os.environ.get("APP_VERSION", "dev")
__release_date__ = os.environ.get("APP_RELEASE_DATE", "")
REPO_URL = "https://github.com/fschlag/dnsmasq-leases-ui"

DNSMASQ_LEASES_FILE = os.environ.get(
    "DNSMASQ_LEASES_FILE", "/var/lib/misc/dnsmasq.leases"
)
DNSMASQ_HOSTS_FILE = os.environ.get(
    "DNSMASQ_HOSTS_FILE", "/etc/dnsmasq.dhcphosts"
)

app = Flask(__name__)

MAC_RE = re.compile(r"^(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")


@dataclass
class LeaseEntry:
    dhcpReservation: bool
    leasetime: str
    macAddress: str
    ipAddress: str
    name: str

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
        reserved = reservations.matches(
            identifier=identifier,
            ip=ip,
            name=name,
            client_id=client_id,
        )

        # A reservation can have a finite DHCP lease. Only dnsmasq's
        # lease-time value 0 means "Never".
        if leasetime == "0":
            lease_end = "Never"
        else:
            lease_end = datetime.fromtimestamp(int(leasetime)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        return cls(
            dhcpReservation=reserved,
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
        line = line.split("#", 1)[0].strip()
        if not line:
            return

        fields = [field.strip() for field in line.split(",") if field.strip()]
        if not fields:
            return

        # Explicit IPv4/IPv6 addresses from dhcp-host entries.
        for field in fields:
            candidate = field.strip("[]")
            try:
                self.ips.add(str(ip_address(candidate)))
                continue
            except ValueError:
                pass

            if MAC_RE.fullmatch(candidate):
                self.identifiers.add(self._normalise_identifier(candidate))

        # In the usual dhcp-host syntax the hostname is the final ordinary
        # field. Matching it is important for DHCPv6 because the IPv6 address
        # in the lease file can differ from the address written in dhcp-hosts.
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

            if lower.startswith(
                (
                    "set:",
                    "tag:",
                    "id:",
                    "net:",
                    "bootfile=",
                    "pxe-service=",
                    "dhcp-option=",
                )
            ) or "=" in candidate:
                continue

            self.names.add(self._normalise_name(candidate))
            break

        # Retain non-MAC identifiers in the first field for dhcp-host entries
        # that use a client identifier rather than a MAC address.
        first = fields[0].strip().strip("[]")
        if first and not MAC_RE.fullmatch(first):
            try:
                ip_address(first)
            except ValueError:
                if not first.casefold().startswith(
                    ("set:", "tag:", "id:", "net:", "bootfile=")
                ):
                    self.identifiers.add(self._normalise_identifier(first))

    def matches(
        self,
        identifier: str,
        ip: str,
        name: str,
        client_id: str,
    ) -> bool:
        try:
            if str(ip_address(ip)) in self.ips:
                return True
        except ValueError:
            pass

        # Case-insensitive hostname match. This handles e.g.
        # iPhone-Micha in dhcp-hosts vs iphone-micha in dnsmasq.leases.
        if name and self._normalise_name(name) in self.names:
            return True

        if identifier and self._normalise_identifier(identifier) in self.identifiers:
            return True

        if client_id and self._normalise_identifier(client_id) in self.identifiers:
            return True

        return False


def read_reservations() -> DhcpReservations:
    reservations = DhcpReservations()

    try:
        with open(DNSMASQ_HOSTS_FILE, encoding="utf-8") as f:
            for line in f:
                reservations.add_line(line)
    except FileNotFoundError:
        pass

    return reservations


def read_leases() -> list[LeaseEntry]:
    leases: list[LeaseEntry] = []
    reservations = read_reservations()

    with open(DNSMASQ_LEASES_FILE, encoding="utf-8") as f:
        for line in f:
            parts = line.split()

            # dnsmasq.leases:
            # lease-end identifier ip hostname client-id
            if len(parts) != 5:
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
    return jsonify(leases=[asdict(lease) for lease in read_leases()])


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
    )
