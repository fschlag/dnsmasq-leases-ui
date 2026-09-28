# Changelog

## [1.1.0](https://github.com/fschlag/dnsmasq-leases-ui/compare/v1.0.0...v1.1.0) (2026-09-28)


### Features

* Add support for dnsmasq.dhcphosts to properly display DHCP reservations. - [#7](https://github.com/fschlag/dnsmasq-leases-ui/issues/7) ([#8](https://github.com/fschlag/dnsmasq-leases-ui/issues/8)) ([35d41cb](https://github.com/fschlag/dnsmasq-leases-ui/commit/35d41cb225136daea4cf348bdb302b578e28199d))
* **parser:** match reservations keyed by duid ([8c6dbe9](https://github.com/fschlag/dnsmasq-leases-ui/commit/8c6dbe9e4a2bbb87e8aee86bf01f533614c6c634))


### Bug Fixes

* **deps:** pick up dependency bumps for release ([afd354a](https://github.com/fschlag/dnsmasq-leases-ui/commit/afd354a20feda9456d6de53afdb13833ce9b65eb))
* keep flagging infinite leases without a dhcp-hosts file ([aee6360](https://github.com/fschlag/dnsmasq-leases-ui/commit/aee63602c3f9fdf26d8e5f1342ae5ba3d3eebdce))
* **parser:** ignore per-host lease time in dhcp-hosts entries ([6b9f4f0](https://github.com/fschlag/dnsmasq-leases-ui/commit/6b9f4f0822f3c992a2b2b5efb3c4c04903ff8528))
* return 503 instead of a traceback when leases file unreadable ([846ddc8](https://github.com/fschlag/dnsmasq-leases-ui/commit/846ddc8e8c8d41a668ebec9e86dc8925e83dade5))
* **ui:** show the real lease end for DHCP reservations ([d6c25b6](https://github.com/fschlag/dnsmasq-leases-ui/commit/d6c25b6b37d26a506411ce7798a12f311365ff32))

## 1.0.0 (2026-05-23)


### Features

* click on table header to sort on that element. ([#5](https://github.com/fschlag/dnsmasq-leases-ui/issues/5)) ([d82c6a2](https://github.com/fschlag/dnsmasq-leases-ui/commit/d82c6a2c511074720c61c9cbc6634dbb6354c9d6))
* improve sorting ([56ed40c](https://github.com/fschlag/dnsmasq-leases-ui/commit/56ed40ca7ff3ce52b1ae70ba419f7df0ff42b5ed))
* local dev setup ([35c772b](https://github.com/fschlag/dnsmasq-leases-ui/commit/35c772b55d2d7c4c5500a285ce0ed76327f3c1c4))
* **ui:** a11y, dark-mode toggle, error UI; credit Feather Icons ([eee687c](https://github.com/fschlag/dnsmasq-leases-ui/commit/eee687cdaf47ae4432b0b263435a6254b8db0464))
* **ui:** sticky header, search filter, footer with version; expand sample to 200 entries ([0b52a50](https://github.com/fschlag/dnsmasq-leases-ui/commit/0b52a506ab9bc0aacb706a4bec4f8487bc0c6618))


### Documentation

* update README ([cd0ad4f](https://github.com/fschlag/dnsmasq-leases-ui/commit/cd0ad4f4f41870e141cb7c889d84a4540d71af1d))
