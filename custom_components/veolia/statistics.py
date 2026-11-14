"""Import Veolia daily consumption as a dated external statistic.

Each complete day is stored at local midnight of the real reading day,
so the Energy dashboard shows water on the day it was used, even though
Veolia publishes readings with a delay. The running sum continues from
the last row already stored before the imported window, so re-importing
overlapping windows on every refresh never creates jumps or negative
values.
"""

from datetime import timedelta
from typing import Any

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticData
from homeassistant.components.recorder.statistics import (
    StatisticMeanType,
    StatisticMetaData,
    async_add_external_statistics,
    statistics_during_period,
)
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util, slugify
from homeassistant.util.unit_conversion import VolumeConverter

from .const import CONSO, DATA_DATE, DOMAIN, LITRE, LOGGER
from .history import build_daily_stats, readings_from_records, window_start

# How far back to look for the last stored row before the imported window.
BASE_LOOKBACK_DAYS = 800


def consumption_statistic_id(id_abonnement: str) -> str:
    """Return the external statistic id for a subscription."""
    return f"{DOMAIN}:{slugify(id_abonnement)}_consumption"


async def async_import_daily_consumption(
    hass: HomeAssistant, account_data: Any
) -> None:
    """Import the fetched daily readings into the external statistic."""
    id_abonnement = getattr(account_data, "id_abonnement", None)
    readings = readings_from_records(
        getattr(account_data, "daily_consumption", None) or [],
        date_key=DATA_DATE,
        conso_key=CONSO,
        litre_key=LITRE,
    )
    today = dt_util.now().date()
    first = window_start(readings, today=today)
    if not id_abonnement or first is None:
        LOGGER.debug("No daily reading to import into statistics")
        return

    statistic_id = consumption_statistic_id(str(id_abonnement))
    previous = await get_instance(hass).async_add_executor_job(
        statistics_during_period,
        hass,
        dt_util.start_of_local_day(first - timedelta(days=BASE_LOOKBACK_DAYS)),
        dt_util.start_of_local_day(first),
        {statistic_id},
        "hour",
        None,
        {"sum"},
    )
    rows = previous.get(statistic_id) or []
    base_sum = float(rows[-1].get("sum") or 0.0) if rows else 0.0

    stats = build_daily_stats(
        readings,
        base_sum=base_sum,
        today=today,
        tz=dt_util.get_default_time_zone(),
    )
    metadata = StatisticMetaData(
        mean_type=StatisticMeanType.NONE,
        has_sum=True,
        name=f"Veolia {id_abonnement} consumption",
        source=DOMAIN,
        statistic_id=statistic_id,
        unit_class=VolumeConverter.UNIT_CLASS,
        unit_of_measurement=UnitOfVolume.CUBIC_METERS,
    )
    LOGGER.debug(
        "Importing %s daily rows into %s (%s -> %s, base sum %s)",
        len(stats),
        statistic_id,
        stats[0].start.date(),
        stats[-1].start.date(),
        base_sum,
    )
    async_add_external_statistics(
        hass,
        metadata,
        [StatisticData(start=s.start, state=s.state, sum=s.sum) for s in stats],
    )
