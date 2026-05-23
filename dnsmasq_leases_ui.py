"""Web UI for dnsmasq leases file."""

import os
from dataclasses import asdict, dataclass
from datetime import datetime

from flask import Flask, jsonify, render_template

DNSMASQ_LEASES_FILE = os.environ.get("DNSMASQ_LEASES_FILE", "/var/lib/misc/dnsmasq.leases")

app = Flask(__name__)


@dataclass
class LeaseEntry:
    staticIP: bool
    leasetime: str
    macAddress: str
    ipAddress: str
    name: str

    @classmethod
    def from_line(cls, leasetime: str, mac: str, ip: str, name: str) -> "LeaseEntry":
        static = leasetime == "0"
        ts = "" if static else datetime.fromtimestamp(int(leasetime)).strftime("%Y-%m-%d %H:%M:%S")
        return cls(static, ts, mac.upper(), ip, name)


def read_leases() -> list[LeaseEntry]:
    leases: list[LeaseEntry] = []
    with open(DNSMASQ_LEASES_FILE) as f:
        for line in f:
            parts = line.split()
            if len(parts) == 5:
                leases.append(LeaseEntry.from_line(parts[0], parts[1], parts[2], parts[3]))
    return leases


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/leases")
def get_leases():
    return jsonify(leases=[asdict(lease) for lease in read_leases()])


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
    )
