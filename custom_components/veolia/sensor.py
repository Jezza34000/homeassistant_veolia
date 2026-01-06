"""Sensor platform for Veolia."""

from homeassistant.components.recorder.statistics import (
    StatisticMeanType,
    StatisticMetaData,
    async_import_statistics,
)
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import UnitOfVolume
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.unit_conversion import VolumeConverter

from .const import DOMAIN, LOGGER
from .entity import VeoliaMesurements


async def async_setup_entry(hass, entry, async_add_devices) -> None:
    """Set up sensor platform."""
    LOGGER.debug("Setting up sensor platform")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = [
        LastIndexSensor(coordinator, entry),
        DailyConsumption(coordinator, entry),
        MonthlyConsumption(coordinator, entry),
        AnnualConsumption(coordinator, entry),
        LastDateSensor(coordinator, entry),
    ]
    async_add_devices(sensors)


class LastIndexSensor(VeoliaMesurements):
    """LastIndexSensor sensor."""

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.entry_id}_last_index"

    @property
    def has_entity_name(self) -> bool:
        """Indicate that entity has name defined."""
        return True

    @property
    def translation_key(self) -> str:
        """Translation key for this entity."""
        return "veolia_index"

    @property
    def native_value(self) -> float | None:
        """Return sensor value."""
        value = self.coordinator.data.computed.last_index_m3
        LOGGER.debug("Sensor %s value : %s", self.__class__.__name__, value)
        return value

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state."""
        comp = self.coordinator.data.computed
        return {
            "data_type": comp.daily_fiability,
            "last_report": comp.last_date.isoformat() if comp.last_date else None,
        }

    @property
    def state_class(self) -> str:
        """Return the state_class of the sensor."""
        return SensorStateClass.TOTAL_INCREASING

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit_of_measurement of the sensor."""
        return UnitOfVolume.CUBIC_METERS

    @property
    def suggested_display_precision(self) -> int:
        """Return the suggested display precision."""
        return 3

    @property
    def icon(self) -> str | None:
        """Set icon."""
        return "mdi:counter"

    # NOT WORKING
    # async def async_added_to_hass(self) -> None:
    #     """Start historical update on HA add."""
    #     await self._update_historical_data()
    #     await super().async_added_to_hass()

    @callback
    async def _update_historical_data(self) -> None:
        """Update historical values."""
        LOGGER.debug("Update_historical_data for %s", self.__class__.__name__)
        stats = self.coordinator.data.computed.index_stats_m3
        if not stats:
            LOGGER.debug("No data update for %s", self.__class__.__name__)
            return
        metadata = StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_sum=True,
            name=None,
            source="recorder",
            statistic_id=self.entity_id,
            unit_class=VolumeConverter.UNIT_CLASS,
            unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        )
        LOGGER.debug("-> StatisticMetaData %s Data : %s", metadata, stats)
        async_import_statistics(self.hass, metadata, stats)


class DailyConsumption(VeoliaMesurements):
    """DailyConsumption sensor."""

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.entry_id}_daily_consumption"

    @property
    def has_entity_name(self) -> bool:
        """Indicate that entity has name defined."""
        return True

    @property
    def translation_key(self) -> str:
        """Translation key for this entity."""
        return "daily_consumption"

    @property
    def native_value(self) -> int | None:
        """Return sensor value."""
        value = self.coordinator.data.computed.daily_today_liters
        LOGGER.debug("Sensor %s value : %s", self.__class__.__name__, value)
        return value

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state."""
        comp = self.coordinator.data.computed
        return {
            "data_type": comp.daily_today_fiability,
            "last_report": comp.last_date.isoformat() if comp.last_date else None,
        }

    async def async_added_to_hass(self) -> None:
        """Start historical update on HA add."""
        await self._update_historical_data()
        await super().async_added_to_hass()

    @callback
    async def _update_historical_data(self) -> None:
        """Update historical values."""
        LOGGER.debug("Update_historical_data for %s", self.__class__.__name__)
        stats = self.coordinator.data.computed.daily_stats_liters
        if not stats:
            LOGGER.debug("No data update for %s", self.__class__.__name__)
            return
        metadata = StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_sum=True,
            name=None,
            source="recorder",
            statistic_id=self.entity_id,
            unit_class=VolumeConverter.UNIT_CLASS,
            unit_of_measurement=UnitOfVolume.LITERS,
        )
        LOGGER.debug("-> StatisticMetaData %s Data : %s", metadata, stats)
        async_import_statistics(self.hass, metadata, stats)

    @property
    def state_class(self) -> str:
        """Return the state_class of the sensor."""
        return SensorStateClass.TOTAL

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit_of_measurement of the sensor."""
        return UnitOfVolume.LITERS

    @property
    def suggested_display_precision(self) -> int:
        """Return the suggested display precision."""
        return 0

    @property
    def icon(self) -> str | None:
        """Set icon."""
        return "mdi:water"


class MonthlyConsumption(VeoliaMesurements):
    """MonthlyConsumption sensor."""

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.entry_id}_monthly_consumption"

    @property
    def has_entity_name(self) -> bool:
        """Indicate that entity has name defined."""
        return True

    @property
    def translation_key(self) -> str:
        """Translation key for this entity."""
        return "monthly_consumption"

    @property
    def native_value(self) -> float | None:
        """Return sensor value."""
        value = self.coordinator.data.computed.monthly_latest_m3
        LOGGER.debug("Sensor %s value : %s", self.__class__.__name__, value)
        return value

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state."""
        return {"data_type": self.coordinator.data.computed.monthly_fiability}

    @property
    def state_class(self) -> str:
        """Return the state_class of the sensor."""
        return SensorStateClass.TOTAL

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit_of_measurement of the sensor."""
        return UnitOfVolume.CUBIC_METERS

    @property
    def suggested_display_precision(self) -> int:
        """Return the suggested display precision."""
        return 3

    @property
    def icon(self) -> str | None:
        """Set icon."""
        return "mdi:water"

    async def async_added_to_hass(self) -> None:
        """Start historical update on HA add."""
        await self._update_historical_data()
        await super().async_added_to_hass()

    @callback
    async def _update_historical_data(self) -> None:
        """Update historical values."""
        LOGGER.debug("Update_historical_data for %s", self.__class__.__name__)
        stats = self.coordinator.data.computed.monthly_stats_cubic_meters
        if not stats:
            LOGGER.debug("No data update for %s", self.__class__.__name__)
            return
        metadata = StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_sum=True,
            name=None,
            source="recorder",
            statistic_id=self.entity_id,
            unit_class=VolumeConverter.UNIT_CLASS,
            unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        )
        LOGGER.debug("-> StatisticMetaData %s Data : %s", metadata, stats)
        async_import_statistics(self.hass, metadata, stats)


class AnnualConsumption(VeoliaMesurements):
    """AnnualConsumption sensor."""

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.entry_id}_annual_consumption"

    @property
    def has_entity_name(self) -> bool:
        """Indicate that entity has name defined."""
        return True

    @property
    def translation_key(self) -> str:
        """Translation key for this entity."""
        return "annual_consumption"

    @property
    def native_value(self) -> float | None:
        """Return sensor value."""
        value = self.coordinator.data.computed.annual_total_m3
        LOGGER.debug("Sensor %s value : %s", self.__class__.__name__, value)
        return value

    @property
    def state_class(self) -> str:
        """Return the state_class of the sensor."""
        return SensorStateClass.TOTAL

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit_of_measurement of the sensor."""
        return UnitOfVolume.CUBIC_METERS

    @property
    def suggested_display_precision(self) -> int:
        """Return the suggested display precision."""
        return 3

    @property
    def icon(self) -> str | None:
        """Set icon."""
        return "mdi:water"


class LastDateSensor(CoordinatorEntity, SensorEntity):
    """LastDateSensor sensor."""

    def __init__(self, coordinator, config_entry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.config_entry = config_entry

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.entry_id}_last_date"

    @property
    def has_entity_name(self) -> bool:
        """Indicate that entity has name defined."""
        return True

    @property
    def translation_key(self) -> str:
        """Translation key for this entity."""
        return "last_consumption_date"

    @property
    def native_value(self) -> str | None:
        """Return sensor value."""
        value = self.coordinator.data.computed.last_date
        LOGGER.debug("Sensor %s value : %s", self.__class__.__name__, value)
        return value

    @property
    def icon(self) -> str | None:
        """Set icon."""
        return "mdi:calendar"
