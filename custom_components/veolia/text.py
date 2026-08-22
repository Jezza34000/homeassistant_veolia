"""Text entities for Veolia integration."""

from dataclasses import dataclass
from typing import Final

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VeoliaConfigEntry
from .const import LOGGER
from .entity import VeoliaEntity


@dataclass(frozen=True, kw_only=True)
class VeoliaTextEntityDescription(TextEntityDescription):
    """Represents a Veolia text entity."""

    status: str | None = None
    threshold: str | None = None
    notification_sms_method: str | None = None
    notification_email_method: str | None = None


TEXT_TYPES: Final[tuple[VeoliaTextEntityDescription, ...]] = (
    VeoliaTextEntityDescription(
        key="daily_threshold_text",
        name="Daily Threshold",
        translation_key="daily_threshold_text",
        icon="mdi:water-alert",
        native_max=6,
        native_min=1,
        pattern="^(?:0|[1-9][0-9]{2,3}|10000)$",
        status="daily_enabled",
        threshold="daily_threshold",
        notification_sms_method="daily_notif_sms",
        notification_email_method="daily_notif_email",
    ),
    VeoliaTextEntityDescription(
        key="monthly_threshold_text",
        name="Monthly Threshold",
        translation_key="monthly_threshold_text",
        icon="mdi:water-check",
        native_max=6,
        native_min=1,
        pattern="^(?:0|[1-9][0-9]{2,3}|10000)$",
        status="monthly_enabled",
        threshold="monthly_threshold",
        notification_sms_method="monthly_notif_sms",
        notification_email_method="monthly_notif_email",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VeoliaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up text platform."""
    LOGGER.debug("Setting up text platform")
    coordinator = entry.runtime_data
    texts = [VeoliaTextEntity(coordinator, description) for description in TEXT_TYPES]
    async_add_entities(texts)


class VeoliaTextEntity(VeoliaEntity, TextEntity):
    """Representation of a Veolia text entity."""

    @property
    def native_value(self) -> str:
        """Return the current threshold value."""
        return str(
            getattr(
                self.coordinator.data.alert_settings, self.entity_description.threshold
            )
            or 0
        )

    async def async_set_value(self, value: str) -> None:
        """Set the threshold value."""
        alert_settings = self.coordinator.data.alert_settings

        if int(value) == 0:
            setattr(alert_settings, self.entity_description.status, False)
        else:
            setattr(alert_settings, self.entity_description.status, True)
            setattr(alert_settings, self.entity_description.threshold, value)
            setattr(
                alert_settings, self.entity_description.notification_sms_method, True
            )
            setattr(
                alert_settings,
                self.entity_description.notification_email_method,
                False,
            )
        await self._async_push_alert_settings()
