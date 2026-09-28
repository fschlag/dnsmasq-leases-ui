"""Web UI for dnsmasq leases file."""

import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from ipaddress import ip_address

from flask import Flask, jsonify, render_template

__version__ = os.environ.get("APP_VERSION", "dev")
__release_date__ = os.environ.get("APP_RELEASE_DATE", "")
REPO_URL = "https://github.com/fschlag/dnsmasq-leases-ui"

DNSMASQ_LEASES_FILE = os.environ.get("DNSMASQ_LEASES_FILE", "/var/lib/misc/dnsmasq.leases")
DNSMASQ_HOSTS_FILE = os.environ.get("DNSMASQ_HOSTS_FILE", "/etc/dnsmasq.dhcphosts")

app = Flask(__name__)

MAC_RE = re.compile(r"^(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")


@dataclass
class LeaseEntry:
    # Keep the original JSON field name so the existing frontend continues
    # to work. Its meaning is now "DHCP reservation", not "infinite lease".
    staticIP: bool
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
        # A host is a DHCP reservation when it is found in
        # /etc/dnsmasq.dhcphosts. This also works for DHCPv6 leases whose
        # current IPv6 address is different from the address in dhcp-hosts.
        reserved = reservations.matches(
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
            lease_end = datetime.fromtimestamp(int(leasetime)).strftime("%Y-%m-%d %H:%M:%S")

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
                if not first.casefold().startswith(("set:", "tag:", "id:", "net:", "bootfile=")):
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
        # This is the important part for your DHCPv6 leases:
        #   dhcphosts: iPhone-Micha
        #   leases:    iphone-micha
        if name and self._normalise_name(name) in self.names:
            return True

        # 3. MAC/client identifier match.
        if identifier and self._normalise_identifier(identifier) in self.identifiers:
            return True

        return bool(client_id and self._normalise_identifier(client_id) in self.identifiers)


def read_reservations() -> DhcpReservations:
    reservations = DhcpReservations()

    try:
        with open(DNSMASQ_HOSTS_FILE, encoding="utf-8") as f:
            for line in f:
                reservations.add_line(line)
    except FileNotFoundError:
        # Optional file: preserve the original behaviour if it is not mounted.
        pass

    return reservations


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
