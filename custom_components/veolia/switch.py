"""Switch platform for Veolia."""

from dataclasses import dataclass
from typing import Any, Final

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VeoliaConfigEntry
from .const import LOGGER
from .entity import VeoliaEntity


@dataclass(frozen=True, kw_only=True)
class VeoliaSwitchEntityDescription(SwitchEntityDescription):
    """Represents a Veolia switch."""

    icon_off: str | None = None
    notification_method: str | None = None
    status: str | None = None
    threshold: str | None = None


SWITCH_TYPES: Final[tuple[VeoliaSwitchEntityDescription, ...]] = (
    VeoliaSwitchEntityDescription(
        key="daily_sms_alert_switch",
        name="Daily SMS Alert",
        translation_key="daily_sms_alert_switch",
        icon="mdi:comment-check",
        icon_off="mdi:comment-off",
        notification_method="daily_notif_sms",
        status="daily_enabled",
        threshold="daily_threshold",
    ),
    VeoliaSwitchEntityDescription(
        key="monthly_sms_alert_switch",
        name="Monthly SMS Alert",
        translation_key="monthly_sms_alert_switch",
        icon="mdi:comment-check",
        icon_off="mdi:comment-off",
        notification_method="monthly_notif_sms",
        status="monthly_enabled",
        threshold="monthly_threshold",
    ),
)

UNOCCUPIED_ALERT_SWITCH_DESCRIPTION = VeoliaSwitchEntityDescription(
    key="unoccupied_alert_switch",
    name="Unoccupied Alert",
    translation_key="unoccupied_alert_switch",
    icon="mdi:comment-check",
    icon_off="mdi:comment-off",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VeoliaConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Set up switch platform."""
    LOGGER.debug("Setting up switch platform")
    coordinator = entry.runtime_data
    switches = [
        VeoliaSMSAlertSwitch(coordinator, description) for description in SWITCH_TYPES
    ]
    switches.append(
        UnoccupiedAlertSwitch(coordinator, UNOCCUPIED_ALERT_SWITCH_DESCRIPTION)
    )
    async_add_devices(switches)


class VeoliaSMSAlertSwitch(VeoliaEntity, SwitchEntity):
    """Representation of the Veolia SMS alert switch."""

    @property
    def icon(self) -> str:
        """Return the icon of the switch."""
        if bool(
            getattr(
                self.coordinator.data.alert_settings,
                self.entity_description.notification_method,
            )
        ):
            return self.entity_description.icon
        return self.entity_description.icon_off

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return bool(
            getattr(
                self.coordinator.data.alert_settings,
                self.entity_description.notification_method,
            )
        )

    @property
    def available(self) -> bool:
        """Return true if the switch is available."""
        LOGGER.debug(
            "Checking availability for %s: %s",
            self.__class__.__name__,
            self.entity_description.status,
        )
        alert_settings = self.coordinator.data.alert_settings
        status = getattr(alert_settings, self.entity_description.status)
        threshold = getattr(alert_settings, self.entity_description.threshold)
        return not (status and threshold == 0) and status

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        setattr(
            self.coordinator.data.alert_settings,
            self.entity_description.notification_method,
            True,
        )
        await self._async_push_alert_settings()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        setattr(
            self.coordinator.data.alert_settings,
            self.entity_description.notification_method,
            False,
        )
        await self._async_push_alert_settings()


class UnoccupiedAlertSwitch(VeoliaEntity, SwitchEntity):
    """Representation of the switch to activate the unoccupied alert."""

    @property
    def icon(self) -> str:
        """Return the icon of the switch."""
        if (
            self.coordinator.data.alert_settings
            and bool(self.coordinator.data.alert_settings.daily_enabled)
            and self.coordinator.data.alert_settings.daily_threshold == 0
        ):
            return self.entity_description.icon
        return self.entity_description.icon_off

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return (
            self.coordinator.data.alert_settings.daily_enabled
            and self.coordinator.data.alert_settings.daily_threshold == 0
        )

    @property
    def available(self) -> bool:
        """Return true if the switch is available."""
        return self.coordinator.data.alert_settings is not None

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        self.coordinator.data.alert_settings.daily_enabled = True
        self.coordinator.data.alert_settings.daily_threshold = 0
        self.coordinator.data.alert_settings.daily_notif_sms = True
        self.coordinator.data.alert_settings.daily_notif_email = True
        await self._async_push_alert_settings()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        self.coordinator.data.alert_settings.daily_enabled = False
        await self._async_push_alert_settings()
