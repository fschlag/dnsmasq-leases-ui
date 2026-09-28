"""Matching dnsmasq.leases entries against dnsmasq.dhcphosts reservations."""

from dnsmasq_leases_ui import DhcpReservations
from tests.samples import IPV4_HOSTS, IPV4_LEASES, IPV6_HOSTS, IPV6_LEASES


def parse(*lines: str) -> DhcpReservations:
    reservations = DhcpReservations()
    for line in lines:
        reservations.add_line(line)
    return reservations


class TestDhcpHostsParsing:
    def test_mac_ip_and_hostname_are_collected(self):
        r = parse("02:aa:00:00:00:01,172.31.77.201,reserved-a")
        assert r.identifiers == {"02:aa:00:00:00:01"}
        assert r.ips == {"172.31.77.201"}
        assert r.names == {"reserved-a"}

    def test_trailing_lease_time_is_not_a_hostname(self):
        r = parse(
            "02:aa:00:00:00:03,172.31.77.203,reserved-c,infinite",
            "02:aa:00:00:00:04,172.31.77.204,reserved-d,12h",
            "02:aa:00:00:00:05,172.31.77.205,reserved-e,45m",
            "02:aa:00:00:00:06,172.31.77.206,reserved-f,3600",
        )
        assert r.names == {"reserved-c", "reserved-d", "reserved-e", "reserved-f"}

    def test_lease_time_only_reservation_records_no_hostname(self):
        r = parse("02:aa:00:00:00:07,172.31.77.207,12h")
        assert r.names == set()
        assert r.ips == {"172.31.77.207"}

    def test_ipv6_address_in_brackets_is_collected(self):
        r = parse("02:aa:00:00:00:11,[fd00:77::abc],iPhone-Micha")
        assert r.ips == {"fd00:77::abc"}
        assert r.names == {"iphone-micha"}

    def test_reservation_without_address(self):
        r = parse("02:aa:00:00:00:12,iPhone-Two")
        assert r.ips == set()
        assert r.names == {"iphone-two"}

    def test_comments_and_blank_lines_are_ignored(self):
        r = parse("# just a comment", "", "   ", "02:aa:00:00:00:01,host-a # trailing")
        assert r.names == {"host-a"}

    def test_ignore_keyword_is_not_a_hostname(self):
        r = parse("02:aa:00:00:00:08,ignore")
        assert r.names == set()
        assert r.identifiers == {"02:aa:00:00:00:08"}

    def test_tag_and_option_fields_are_not_hostnames(self):
        r = parse("set:special,02:aa:00:00:00:09,172.31.77.209", "tag:red,02:aa:00:00:00:0a,host-j")
        assert r.names == {"host-j"}


class TestMatching:
    def test_hostname_match_is_case_insensitive(self):
        r = parse("02:aa:00:00:00:12,iPhone-Two")
        assert r.matches(identifier="18", ip="fd00:77::113", name="iphone-TWO", client_id="00:01")

    def test_trailing_dot_in_lease_hostname_still_matches(self):
        r = parse("02:aa:00:00:00:12,iPhone-Two")
        assert r.matches(identifier="18", ip="fd00:77::113", name="iPhone-Two.", client_id="00:01")

    def test_unknown_host_does_not_match(self):
        r = parse("02:aa:00:00:00:12,iPhone-Two")
        assert not r.matches(identifier="19", ip="fd00:77::199", name="stranger", client_id="00:01")

    def test_empty_reservations_match_nothing(self):
        r = parse()
        assert not r.matches(
            identifier="02:aa:00:00:00:01", ip="172.31.77.201", name="a", client_id="*"
        )


class TestIpv4Leases:
    def test_reservation_with_finite_lease_is_flagged(self, leases):
        """The bug behind issue #7: a reservation served out of the dhcp-range
        lease time is not an infinite lease, but it is still a reservation."""
        entries = leases(IPV4_LEASES, IPV4_HOSTS)
        assert entries["reserved-a"].staticIP is True
        assert entries["reserved-a"].leasetime != "Never"

    def test_reservation_with_lease_time_field_is_flagged(self, leases):
        entries = leases(IPV4_LEASES, IPV4_HOSTS)
        assert entries["reserved-d"].staticIP is True

    def test_infinite_lease_reservation_is_flagged(self, leases):
        entries = leases(IPV4_LEASES, IPV4_HOSTS)
        assert entries["reserved-c"].staticIP is True
        assert entries["reserved-c"].leasetime == "Never"

    def test_dynamic_lease_is_not_flagged(self, leases):
        entries = leases(IPV4_LEASES, IPV4_HOSTS)
        assert entries["dynamic-b"].staticIP is False

    def test_mac_address_is_upper_cased(self, leases):
        entries = leases(IPV4_LEASES, IPV4_HOSTS)
        assert entries["dynamic-b"].macAddress == "02:AA:00:00:00:02"


class TestIpv6Leases:
    def test_lease_matched_by_hostname(self, leases):
        """DHCPv6: the lease holds an IAID and a dynamic address, so neither
        the identifier nor the address appears in dhcp-hosts."""
        entries = leases(IPV6_LEASES, IPV6_HOSTS)
        assert entries["iPhone-Two"].ipAddress == "fd00:77::113"
        assert entries["iPhone-Two"].staticIP is True

    def test_lease_matched_by_hostname_despite_lease_time_field(self, leases):
        entries = leases(IPV6_LEASES, IPV6_HOSTS)
        assert entries["iPhone-Three"].staticIP is True

    def test_unknown_client_is_not_flagged(self, leases):
        entries = leases(IPV6_LEASES, IPV6_HOSTS)
        assert entries["stranger"].staticIP is False

    def test_nameless_lease_is_not_flagged(self, leases):
        entries = leases(IPV6_LEASES, IPV6_HOSTS)
        assert entries["*"].staticIP is False

    def test_server_duid_line_is_skipped(self, leases):
        entries = leases(IPV6_LEASES, IPV6_HOSTS)
        assert len(entries) == 4
        assert not any(name.startswith("duid") for name in entries)


class TestDuidKeyedReservations:
    """dnsmasq key DHCPv6 reservations by DUID as "id:<hex>"; the lease line
    carry that DUID in its client-id field."""

    DUID = "00:01:00:01:32:4d:7c:26:02:aa:00:00:00:12"

    def test_duid_is_stored_as_an_identifier(self):
        r = parse(f"id:{self.DUID},iPhone-Renamed")
        assert self.DUID in r.identifiers
        assert r.names == {"iphone-renamed"}

    def test_lease_matched_by_duid_when_hostname_differs(self):
        r = parse(f"id:{self.DUID},iPhone-Renamed")
        # Lease reports a different hostname and a dynamic address.
        assert r.matches(
            identifier="18",
            ip="fd00:77::113",
            name="iPhone-Two",
            client_id=self.DUID,
        )

    def test_duid_match_is_case_insensitive(self):
        r = parse(f"id:{self.DUID.upper()},iPhone-Renamed")
        assert r.matches(identifier="18", ip="fd00:77::113", name="x", client_id=self.DUID)

    def test_wildcard_client_id_is_not_stored(self):
        """A leases file write "*" for a lease without a client-id, so "id:*"
        must not turn every such lease into a reservation."""
        r = parse("id:*,172.31.77.250,any-client")
        assert "*" not in r.identifiers
        assert not r.matches(
            identifier="02:aa:00:00:00:99", ip="192.168.0.1", name="other", client_id="*"
        )

    def test_ipv4_client_id_reservation(self, leases):
        entries = leases(
            "1790623935 02:aa:00:00:00:02 172.31.77.101 dynamic-b 01:02:aa:00:00:00:02\n",
            "id:01:02:aa:00:00:00:02,some-other-name\n",
        )
        assert entries["dynamic-b"].staticIP is True


class TestDegenerateInput:
    def test_line_of_separators_only(self):
        assert parse(",").names == set()

    def test_empty_bracketed_field(self):
        r = parse("02:aa:00:00:00:01,[]")
        assert r.identifiers == {"02:aa:00:00:00:01"}
        assert r.names == set()

    def test_bare_client_id_first_field(self):
        # A client-id written without the "id:" prefix is still an identifier.
        r = parse("01:02:aa:00:00:00:02,some-name")
        assert "01:02:aa:00:00:00:02" in r.identifiers

    def test_unparseable_lease_address_falls_through(self):
        r = parse("02:aa:00:00:00:01,172.31.77.201,reserved-a")
        assert not r.matches(identifier="x", ip="not-an-ip", name="nope", client_id="nope")


class TestIdentifierOnlyMatch:
    def test_mac_match_when_address_is_not_in_dhcp_hosts(self):
        """The MAC branch: a reservation whose host now hold a different
        address, e.g. after the subnet is renumbered."""
        r = parse("02:aa:00:00:00:01,172.31.77.201,reserved-a")
        assert r.matches(
            identifier="02:aa:00:00:00:01",
            ip="10.0.0.5",
            name="renamed-host",
            client_id="*",
        )
