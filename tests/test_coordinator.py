"""Tests for the Veolia coordinator error handling (needs Home Assistant).

Run with: pip install -r requirements_test.txt && python -m pytest tests
"""

from types import SimpleNamespace

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from sqlalchemy.exc import OperationalError
from veolia_api.exceptions import VeoliaAPIGetDataError

from custom_components.veolia import coordinator as coordinator_module
from custom_components.veolia.const import DOMAIN
from custom_components.veolia.coordinator import VeoliaDataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed


class FakeClient:
    """Stand-in for VeoliaAPI recording the requested ranges."""

    def __init__(self, failures: int, *, logged_in: bool) -> None:
        """Fail the first `failures` fetches."""
        self.failures = failures
        self.calls: list[tuple] = []
        self.account_data = SimpleNamespace(
            id_abonnement="1045345",
            date_debut_abonnement="1986-01-01" if logged_in else None,
            daily_consumption=[],
            monthly_consumption=[],
        )

    async def fetch_all_data(self, start, end) -> None:
        """Record the range, fail while failures remain."""
        self.calls.append((start, end))
        if len(self.calls) <= self.failures:
            raise VeoliaAPIGetDataError("call to= consommations failed")


def _coordinator(
    hass: HomeAssistant, client: FakeClient
) -> VeoliaDataUpdateCoordinator:
    entry = MockConfigEntry(domain=DOMAIN, data={"username": "u", "password": "p"})
    entry.add_to_hass(hass)
    coordinator = VeoliaDataUpdateCoordinator(hass, entry)
    coordinator.client_api = client
    return coordinator


async def test_no_history_fallback_when_login_failed(hass: HomeAssistant) -> None:
    """A data error before the account is loaded is not retried with 12 months."""
    client = FakeClient(failures=5, logged_in=False)
    coordinator = _coordinator(hass, client)
    await coordinator.async_refresh()
    assert not coordinator.last_update_success
    assert isinstance(coordinator.last_exception, UpdateFailed)
    assert len(client.calls) == 1


async def test_history_fallback_to_12_months(hass: HomeAssistant) -> None:
    """A refused 24-month history is retried with 12 months."""
    client = FakeClient(failures=1, logged_in=True)
    coordinator = _coordinator(hass, client)
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    (start24, end), (start12, end12) = client.calls
    assert end == end12
    assert (end.year - start24.year) * 12 + end.month - start24.month == 24
    assert (end.year - start12.year) * 12 + end.month - start12.month == 12


async def test_statistics_db_error_keeps_sensors_updating(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A recorder error during the import does not fail the whole refresh."""

    async def broken_import(*_args) -> None:
        raise OperationalError("SELECT", {}, Exception("database is locked"))

    monkeypatch.setattr(
        coordinator_module, "async_import_daily_consumption", broken_import
    )
    client = FakeClient(failures=0, logged_in=True)
    coordinator = _coordinator(hass, client)
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.data.raw is client.account_data
