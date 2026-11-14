"""DataUpdateCoordinator for veolia."""

from datetime import date, timedelta
from typing import Any

from dateutil.relativedelta import relativedelta
from veolia_api import VeoliaAPI
from veolia_api.exceptions import VeoliaAPIError, VeoliaAPIGetDataError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import CONF_PORTAL_URL, DOMAIN, LOGGER
from .model import VeoliaModel
from .statistics import async_import_daily_consumption

SCAN_INTERVAL = timedelta(hours=6)
# Veolia keeps about two years of daily readings.
INITIAL_HISTORY_MONTHS = 24
FALLBACK_HISTORY_MONTHS = 12


class VeoliaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass, logger=LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL
        )
        LOGGER.debug("Initializing client VeoliaAPI")
        self.client_api: Any
        self._initial_historical_fetch = False
        self.session = async_get_clientsession(hass)

    async def _async_setup(self) -> None:
        """Coordinator setup."""
        self.client_api = VeoliaAPI(
            username=self.config_entry.data[CONF_USERNAME],
            password=self.config_entry.data[CONF_PASSWORD],
            session=self.session,
            portal_url=self.config_entry.data.get(CONF_PORTAL_URL),
        )

    async def _async_update_data(self) -> VeoliaModel:
        """Fetch and calculate data."""
        try:
            now = dt_util.now()

            end_date = date(now.year, now.month, 1)
            if not self._initial_historical_fetch:
                # First init
                LOGGER.debug("Initial fetch %s months", INITIAL_HISTORY_MONTHS)
                try:
                    await self.client_api.fetch_all_data(
                        end_date - relativedelta(months=INITIAL_HISTORY_MONTHS),
                        end_date,
                    )
                except VeoliaAPIGetDataError as err:
                    LOGGER.warning(
                        "Veolia refused %s months of history (%s), fetching %s months",
                        INITIAL_HISTORY_MONTHS,
                        err,
                        FALLBACK_HISTORY_MONTHS,
                    )
                    await self.client_api.fetch_all_data(
                        end_date - relativedelta(months=FALLBACK_HISTORY_MONTHS),
                        end_date,
                    )
                self._initial_historical_fetch = True
            else:
                # Regular fetch
                LOGGER.debug("Periodic fetch - 2 months")
                await self.client_api.fetch_all_data(
                    end_date - relativedelta(months=1), end_date
                )

            account_data = self.client_api.account_data
            try:
                await async_import_daily_consumption(self.hass, account_data)
            except (ValueError, TypeError, KeyError, HomeAssistantError) as err:
                LOGGER.warning("Could not import Veolia statistics: %s", err)
            today = dt_util.now().date()
            return VeoliaModel.from_account_data(account_data, today=today)
        except VeoliaAPIGetDataError as err:
            raise UpdateFailed(str(err)) from err
        except VeoliaAPIError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
