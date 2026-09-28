"""The page must load the lease-table module and keep the backend's lease end."""

import pathlib

import pytest

from dnsmasq_leases_ui import app

STATIC = pathlib.Path(__file__).resolve().parent.parent / "static"


@pytest.fixture
def page() -> str:
    with app.test_client() as client:
        return client.get("/").get_data(as_text=True)


def test_page_loads_the_lease_table_module(page):
    assert "/static/app.js" in page


def test_page_passes_the_script_root_to_the_module(page):
    # The module builds its /leases URL from this, so a subpath deployment works.
    assert "data-script-root" in page


def test_reservation_column_is_rendered(page):
    assert "DHCP Reservation" in page
    assert "Lease ends on" in page


def test_static_assets_are_served():
    with app.test_client() as client:
        for path in ("/static/app.js", "/static/leases.js", "/static/icon.svg"):
            assert client.get(path).status_code == 200, path


def test_lease_end_is_not_overridden_for_reservations():
    # The backend already reports "Never" for an infinite lease, so the table
    # must not blank out the real expiry of every reservation.
    js = "\n".join(path.read_text() for path in sorted(STATIC.glob("*.js")))
    assert "staticIP ? 'Never'" not in js
    assert "row.leasetime" in (STATIC / "leases.js").read_text()


def test_footer_carries_version_and_repo(page):
    assert "dev" in page  # APP_VERSION default
    assert "github.com/fschlag/dnsmasq-leases-ui" in page
