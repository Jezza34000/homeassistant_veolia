"""VeoliaEntity class."""

from dataclasses import asdict

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER, NAME
from .coordinator import VeoliaDataUpdateCoordinator


class VeoliaEntity(CoordinatorEntity[VeoliaDataUpdateCoordinator]):
    """Representation of a Veolia entity."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: VeoliaDataUpdateCoordinator, description: EntityDescription
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description

        config_entry = coordinator.config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            manufacturer=NAME,
            name=f"{NAME} {coordinator.data.id_abonnement}",
        )

    async def _async_push_alert_settings(self) -> None:
        """Send the current alert settings to the API and refresh state."""
        alert_settings = self.coordinator.data.alert_settings
        LOGGER.debug(
            "Pushing alert settings for %s: %s",
            self.__class__.__qualname__,
            asdict(alert_settings),
        )
        res = await self.coordinator.client_api.set_alerts_settings(alert_settings)
        if not res:
            message = f"Failed to set alert= {self.__class__.__qualname__} settings= {asdict(alert_settings)}"
            raise HomeAssistantError(message)
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()
