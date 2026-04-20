"""Config flow for veolia integration."""

import aiohttp
from veolia_api import VeoliaAPI
from veolia_api.exceptions import VeoliaAPIInvalidCredentialsError, VeoliaAPITokenError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, LOGGER


class VeoliaFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for veolia."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Initialize."""
        self._errors = {}
        self._postal_code = None
        self._communes = []

    async def async_step_user(self, user_input=None) -> dict:
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            self._postal_code = user_input["postal_code"]
            return await self.async_step_select_commune()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("postal_code"): str}),
            errors=self._errors,
        )

    async def async_step_select_commune(self, user_input=None) -> dict:
        """Handle the selection of a commune."""
        LOGGER.debug("Check city postal to for integration compatibility")
        if user_input is not None:
            selected_commune = next(
                (
                    commune
                    for commune in self._communes
                    if commune["libelle"] == user_input["commune"]
                ),
                None,
            )
            if selected_commune["type_commune"] in ("NON_REDIRIGE", "REDIRIGE"):
                return await self.async_step_credentials()

            if selected_commune["type_commune"] == "NON_DESSERVIE":
                self._errors["base"] = "commune_not_veolia"
            else:
                self._errors["base"] = "commune_not_supported"

        async with (
            aiohttp.ClientSession() as session,
            session.get(
                f"https://prd-ael-sirius-refcommunes.istefr.fr/communes-nationales?q={self._postal_code}"
            ) as response,
        ):
            self._communes = await response.json()

        if not self._communes:
            self._errors["base"] = "no_communes_found"

        commune_options = {
            commune["libelle"]: commune["libelle"] for commune in self._communes
        }

        return self.async_show_form(
            step_id="select_commune",
            data_schema=vol.Schema({vol.Required("commune"): vol.In(commune_options)}),
            errors=self._errors,
        )

    async def async_step_credentials(self, user_input=None) -> dict:
        """Handle the input of credentials."""
        LOGGER.debug("Request credentials")
        if user_input is not None:
            try:
                api = VeoliaAPI(
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                    async_get_clientsession(self.hass),
                )
                valid = await api.login()

                if valid:
                    return self.async_create_entry(
                        title=user_input[CONF_USERNAME],
                        data=user_input,
                    )
            except (VeoliaAPIInvalidCredentialsError, VeoliaAPITokenError):
                self._errors["base"] = "invalid_credentials"
            except Exception:  # noqa: BLE001
                LOGGER.debug("Unknown exception")
                self._errors["base"] = "unknown"

            return await self._show_credentials_form(user_input)

        return await self._show_credentials_form(user_input)

    async def _show_credentials_form(self, user_input) -> dict:
        """Show the configuration form to input credentials."""
        return self.async_show_form(
            step_id="credentials",
            data_schema=vol.Schema(
                {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str},
            ),
            errors=self._errors,
        )
