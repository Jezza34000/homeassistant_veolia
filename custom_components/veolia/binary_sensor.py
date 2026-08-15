"""The Veolia binary sensor integration."""

from dataclasses import dataclass
from typing import Final

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VeoliaConfigEntry
from .const import LOGGER
from .entity import VeoliaEntity


@dataclass(frozen=True, kw_only=True)
class VeoliaBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Represents a Veolia binary sensor."""

    icon_off: str | None = None
    status: str | None = None
    threshold: str | None = None


BINARYSENSOR_TYPES: Final[tuple[VeoliaBinarySensorEntityDescription, ...]] = (
    VeoliaBinarySensorEntityDescription(
        key="daily_alert_binary_sensor",
        name="Daily Alert",
        icon="mdi:bell-check",
        icon_off="mdi:bell-cancel",
        translation_key="daily_alert_binary_sensor",
        status="daily_enabled",
        threshold="daily_threshold",
    ),
    VeoliaBinarySensorEntityDescription(
        key="monthly_alert_binary_sensor",
        name="Monthly Alert",
        icon="mdi:bell-check",
        icon_off="mdi:bell-cancel",
        translation_key="monthly_alert_binary_sensor",
        status="monthly_enabled",
        threshold="monthly_threshold",
    ),
    VeoliaBinarySensorEntityDescription(
        key="unoccupied_alert_binary_sensor",
        name="Unoccupied Alert",
        icon="mdi:bell-check",
        icon_off="mdi:bell-cancel",
        translation_key="unoccupied_alert_binary_sensor",
        status="unoccupied_enabled",
        threshold="unoccupied_threshold",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VeoliaConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Set up binary sensor platform."""
    LOGGER.debug("Setting up binary_sensor platform")
    coordinator = entry.runtime_data
    binary_sensors = [
        VeoliaAlerts(coordinator, description) for description in BINARYSENSOR_TYPES
    ]
    async_add_devices(binary_sensors)


class VeoliaAlerts(VeoliaEntity, BinarySensorEntity):
    """Representation of the Veolia alerts binary sensor."""

    @property
    def icon(self) -> str:
        """Return the icon of the binary sensor."""
        if self.is_on:
            return self.entity_description.icon
        return self.entity_description.icon_off

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""

        return (
            getattr(
                self.coordinator.data.alert_settings,
                self.entity_description.status,
                False,
            )
            and getattr(
                self.coordinator.data.alert_settings,
                self.entity_description.threshold,
                0,
            )
            == 0
        )
