"""Reading dnsmasq.leases, including without a dhcp-hosts file."""

import json
import os
from datetime import datetime

import pytest

import dnsmasq_leases_ui as app_module
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
        assert set(rows[0]) == {
            "staticIP",
            "leasetime",
            "macAddress",
            "ipAddress",
            "name",
            "webUrl",
        }
        assert {row["name"]: row["staticIP"] for row in rows} == {
            "dynamic-b": False,
            "reserved-a": True,
            "reserved-c": True,
            "reserved-d": True,
        }


class TestUnreadableFiles:
    """A mount typo or a permission problem is a deployment fault, not a crash."""

    def test_missing_leases_file_returns_503(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            app_module, "DNSMASQ_LEASES_FILE", str(tmp_path / "does-not-exist.leases")
        )
        with app.test_client() as client:
            response = client.get("/leases")
        assert response.status_code == 503
        assert json.loads(response.get_data(as_text=True))["error"]

    @pytest.mark.skipif(os.geteuid() == 0, reason="root ignores file permissions")
    def test_unreadable_leases_file_returns_503(self, tmp_path, monkeypatch):
        leases_file = tmp_path / "dnsmasq.leases"
        leases_file.write_text(IPV4_LEASES)
        leases_file.chmod(0o000)
        monkeypatch.setattr(app_module, "DNSMASQ_LEASES_FILE", str(leases_file))
        try:
            with app.test_client() as client:
                assert client.get("/leases").status_code == 503
        finally:
            leases_file.chmod(0o644)

    @pytest.mark.skipif(os.geteuid() == 0, reason="root ignores file permissions")
    def test_unreadable_hosts_file_is_ignored(self, tmp_path, monkeypatch):
        """The dhcp-hosts file is optional, so it must not break the page."""
        leases_file = tmp_path / "dnsmasq.leases"
        leases_file.write_text(IPV4_LEASES)
        hosts_file = tmp_path / "dnsmasq.dhcphosts"
        hosts_file.write_text(IPV4_HOSTS)
        hosts_file.chmod(0o000)
        monkeypatch.setattr(app_module, "DNSMASQ_LEASES_FILE", str(leases_file))
        monkeypatch.setattr(app_module, "DNSMASQ_HOSTS_FILE", str(hosts_file))
        try:
            with app.test_client() as client:
                response = client.get("/leases")
            assert response.status_code == 200
            rows = json.loads(response.get_data(as_text=True))["leases"]
            # Falls back to the infinite-lease signal only.
            assert {row["name"]: row["staticIP"] for row in rows}["reserved-c"] is True
        finally:
            hosts_file.chmod(0o644)


class TestCorruptLines:
    def test_non_numeric_lease_time_is_skipped(self, leases):
        entries = leases(
            "notanumber 02:aa:00:00:00:09 172.31.77.109 corrupt-a 01:02:aa:00:00:00:09\n"
            "-5 02:aa:00:00:00:0a 172.31.77.110 corrupt-b 01:02:aa:00:00:00:0a\n" + IPV4_LEASES
        )
        assert "corrupt-a" not in entries
        assert "corrupt-b" not in entries
        assert len(entries) == 4
