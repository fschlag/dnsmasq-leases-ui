"""Reading dnsmasq.leases, including without a dhcp-hosts file."""

import json
from datetime import datetime

from dnsmasq_leases_ui import app
from tests.samples import IPV4_HOSTS, IPV4_LEASES


class TestWithoutHostsFile:
    """The dhcp-hosts mount is optional, so an upgrade without it must not
    silently empty the reservation column."""

    def test_infinite_lease_is_still_a_reservation(self, leases):
        entries = leases(IPV4_LEASES)
        assert entries["reserved-c"].staticIP is True
        assert entries["reserved-c"].leasetime == "Never"

    def test_dynamic_lease_is_not_a_reservation(self, leases):
        entries = leases(IPV4_LEASES)
        assert entries["dynamic-b"].staticIP is False

    def test_reservations_with_a_finite_lease_are_unknown(self, leases):
        # Nothing in the leases file distinguishes these without dhcp-hosts.
        entries = leases(IPV4_LEASES)
        assert entries["reserved-a"].staticIP is False
        assert entries["reserved-d"].staticIP is False

    def test_all_leases_are_still_listed(self, leases):
        assert len(leases(IPV4_LEASES)) == 4


class TestLeaseEnd:
    def test_infinite_lease_reads_never(self, leases):
        assert leases(IPV4_LEASES, IPV4_HOSTS)["reserved-c"].leasetime == "Never"

    def test_expiry_is_formatted_in_local_time(self, leases):
        entry = leases(IPV4_LEASES, IPV4_HOSTS)["dynamic-b"]
        expected = datetime.fromtimestamp(1790623935).strftime("%Y-%m-%d %H:%M:%S")
        assert entry.leasetime == expected


class TestMalformedLines:
    def test_lines_without_five_fields_are_skipped(self, leases):
        entries = leases(
            "duid 00:01:00:01:32:4d:7b:ee:00:00:00:00:00:00\n"
            "\n"
            "1790623935 02:aa:00:00:00:02 172.31.77.101\n"
            "1790623935 02:aa:00:00:00:02 172.31.77.101 dynamic-b 01:02:aa:00:00:00:02\n"
        )
        assert list(entries) == ["dynamic-b"]


class TestLeasesEndpoint:
    def test_returns_every_field_the_table_reads(self, leases):
        leases(IPV4_LEASES, IPV4_HOSTS)
        with app.test_client() as client:
            response = client.get("/leases")
        assert response.status_code == 200
        rows = json.loads(response.get_data(as_text=True))["leases"]
        assert len(rows) == 4
        assert set(rows[0]) == {"staticIP", "leasetime", "macAddress", "ipAddress", "name"}
        assert {row["name"]: row["staticIP"] for row in rows} == {
            "dynamic-b": False,
            "reserved-a": True,
            "reserved-c": True,
            "reserved-d": True,
        }
