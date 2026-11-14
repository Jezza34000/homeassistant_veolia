"""Pure helpers turning Veolia daily readings into dated statistic rows.

This module only uses the standard library so it can be unit tested
without Home Assistant.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, tzinfo


@dataclass(frozen=True, slots=True)
class DailyStat:
    """One statistic row: the consumption of one day, in cubic meters."""

    start: datetime
    state: float
    sum: float


def readings_from_records(
    records: Iterable[dict], *, date_key: str, conso_key: str, litre_key: str
) -> list[tuple[date, float]]:
    """Extract (day, liters) pairs, skipping records without a valid day or volume."""
    readings: list[tuple[date, float]] = []
    for record in records or []:
        try:
            day = datetime.strptime(record[date_key][:10], "%Y-%m-%d").date()
            liters = float(record[conso_key][litre_key])
        except (KeyError, TypeError, ValueError):
            continue
        readings.append((day, liters))
    return readings


def window_start(readings: Iterable[tuple[date, float]], *, today: date) -> date | None:
    """Return the first complete day (before today) of the readings, if any."""
    days = [day for day, _ in readings if day < today]
    return min(days) if days else None


def build_daily_stats(
    readings: Iterable[tuple[date, float]],
    *,
    base_sum: float,
    today: date,
    tz: tzinfo,
) -> list[DailyStat]:
    """Build one row per complete day, dated at local midnight of the real day.

    The running sum starts from ``base_sum`` (the sum already stored right
    before the first day), so overlapping re-imports stay continuous.
    """
    by_day = {day: liters for day, liters in readings if day < today}
    stats: list[DailyStat] = []
    total_m3 = 0.0
    for day in sorted(by_day):
        day_m3 = by_day[day] / 1000
        total_m3 += day_m3
        stats.append(
            DailyStat(
                start=datetime.combine(day, time(), tzinfo=tz),
                state=round(day_m3, 3),
                sum=round(base_sum + total_m3, 3),
            )
        )
    return stats
