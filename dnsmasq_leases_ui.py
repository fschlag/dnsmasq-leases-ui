"""Web UI for dnsmasq leases file."""

from ipaddress import ip_address
import os
from dataclasses import asdict, dataclass
from datetime import datetime

from flask import Flask, jsonify, render_template

__version__ = os.environ.get("APP_VERSION", "dev")
__release_date__ = os.environ.get("APP_RELEASE_DATE", "")
REPO_URL = "https://github.com/fschlag/dnsmasq-leases-ui"

DNSMASQ_LEASES_FILE = os.environ.get("DNSMASQ_LEASES_FILE", "/var/lib/misc/dnsmasq.leases")
DNSMASQ_HOSTS_FILE = os.environ.get("DNSMASQ_HOSTS_FILE", "/etc/dnsmasq.dhcphosts")

app = Flask(__name__)


@dataclass
class LeaseEntry:
    staticIP: bool
    leasetime: str
    macAddress: str
    ipAddress: str
    name: str

    @classmethod
    def from_line(
        cls,
        leasetime: str,
        mac: str,
        ip: str,
        name: str,
        reserved_ips: set[str],
        reserved_names: set[str],
    ) -> "LeaseEntry":
        # A lease is considered "static" when dnsmasq itself reports an
        # infinite lease OR when the address is explicitly reserved in
        # dhcphosts. The latter is important because dnsmasq can give a
        # reserved address a normal, finite lease time.
        static = leasetime == "0" or ip in reserved_ips or name in reserved_names
        # Keep the lease end visible for finite DHCP reservations. Only an
        # actual infinite lease (leasetime=0) has no expiry timestamp.
        ts = "" if leasetime == "0" else datetime.fromtimestamp(int(leasetime)).strftime("%Y-%m-%d %H:%M:%S")
        return cls(static, ts, mac.upper(), ip, name)


def read_reservations() -> tuple[set[str], set[str]]:
    """Return IP addresses and hostnames reserved by dnsmasq dhcp-host entries."""
    reserved_ips: set[str] = set()
    reserved_names: set[str] = set()

    try:
        with open(DNSMASQ_HOSTS_FILE) as f:
            for line in f:
                # Ignore comments, including inline comments.
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue

                fields = [field.strip() for field in line.split(",")]
                for field in fields:
                    candidate = field.strip("[]")
                    try:
                        reserved_ips.add(str(ip_address(candidate)))
                    except ValueError:
                        continue

                # In dhcp-host entries the hostname is normally the final
                # non-option field. Ignore tags/options such as set:foo and
                # id:bar. Matching the hostname also lets us recognize an
                # IPv6 lease when the dhcphosts entry uses a different IPv6
                # representation for the same host.
                for field in reversed(fields):
                    if field and not field.startswith(("set:", "tag:", "id:")):
                        try:
                            ip_address(field.strip("[]"))
                        except ValueError:
                            reserved_names.add(field)
                        break
    except FileNotFoundError:
        # Keep the original behaviour when no dhcphosts file is mounted.
        pass

    return reserved_ips, reserved_names


def read_leases() -> list[LeaseEntry]:
    leases: list[LeaseEntry] = []
    reserved_ips, reserved_names = read_reservations()
    with open(DNSMASQ_LEASES_FILE) as f:
        for line in f:
            parts = line.split()
            if len(parts) == 5:
                leases.append(
                    LeaseEntry.from_line(
                        parts[0], parts[1], parts[2], parts[3], reserved_ips, reserved_names
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
