"""Shared fixtures."""

import pytest

import dnsmasq_leases_ui as app_module


@pytest.fixture
def leases(tmp_path, monkeypatch):
    """Point the app at a leases file, and optionally a dhcp-hosts file."""

    def _write(leases_text: str, hosts_text: str | None = None):
        leases_file = tmp_path / "dnsmasq.leases"
        leases_file.write_text(leases_text)
        monkeypatch.setattr(app_module, "DNSMASQ_LEASES_FILE", str(leases_file))

        hosts_file = tmp_path / "dnsmasq.dhcphosts"
        if hosts_text is not None:
            hosts_file.write_text(hosts_text)
        monkeypatch.setattr(app_module, "DNSMASQ_HOSTS_FILE", str(hosts_file))

        return {entry.name: entry for entry in app_module.read_leases()}

    return _write
