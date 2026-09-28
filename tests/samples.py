"""Lease and dhcp-hosts samples captured from a real dnsmasq 2.90 serving
DHCPv4 and DHCPv6 to containers on a docker bridge.
"""

# dnsmasq.leases, DHCPv4. reserved-a/-c/-d are dhcp-host reservations,
# dynamic-b comes from the dhcp-range. Only reserved-c has an infinite lease.
IPV4_LEASES = """\
1790623935 02:aa:00:00:00:02 172.31.77.101 dynamic-b 01:02:aa:00:00:00:02
1790623931 02:aa:00:00:00:01 172.31.77.201 reserved-a 01:02:aa:00:00:00:01
1790667015 02:aa:00:00:00:04 172.31.77.204 reserved-d 01:02:aa:00:00:00:04
0 02:aa:00:00:00:03 172.31.77.203 reserved-c 01:02:aa:00:00:00:03
"""

IPV4_HOSTS = """\
# plain reservation: mac,ip,hostname
02:aa:00:00:00:01,172.31.77.201,reserved-a
# reservation with infinite lease
02:aa:00:00:00:03,172.31.77.203,reserved-c,infinite
# reservation with an explicit lease time as 4th field
02:aa:00:00:00:04,172.31.77.204,reserved-d,12h
"""

# dnsmasq.leases, DHCPv6. The second field is an IAID, not a MAC, and the
# client-id is a DUID. iPhone-Two/-Three hold dynamic addresses that appear
# nowhere in dhcp-hosts, so only the hostname identifies them.
IPV6_LEASES = """\
duid 00:01:00:01:32:4d:7b:ee:00:00:00:00:00:00
1790623870 21 fd00:77::1f7 * 00:01:00:01:32:4d:7c:84:02:aa:00:00:00:15
1790623866 20 fd00:77::1f0 iPhone-Three 00:01:00:01:32:4d:7c:7f:02:aa:00:00:00:14
1790623781 19 fd00:77::199 stranger 00:01:00:01:32:4d:7c:2a:02:aa:00:00:00:13
1790623777 18 fd00:77::113 iPhone-Two 00:01:00:01:32:4d:7c:26:02:aa:00:00:00:12
"""

IPV6_HOSTS = """\
02:aa:00:00:00:11,[fd00:77::abc],iPhone-Micha
02:aa:00:00:00:12,iPhone-Two
02:aa:00:00:00:14,iPhone-Three,12h
"""
