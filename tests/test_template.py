"""The lease table must show the lease end the backend computed."""

import pytest

from dnsmasq_leases_ui import app


@pytest.fixture
def page() -> str:
    with app.test_client() as client:
        return client.get("/").get_data(as_text=True)


def test_lease_end_cell_comes_from_the_api(page):
    assert "row.leasetime," in page


def test_lease_end_is_not_overridden_for_reservations(page):
    # The backend already reports "Never" for an infinite lease, so the table
    # must not blank out the real expiry of every reservation.
    assert "staticIP ? 'Never'" not in page


def test_reservation_column_is_rendered(page):
    assert "DHCP Reservation" in page
    assert "Lease ends on" in page
