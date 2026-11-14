"""Tests for the pure Veolia history helpers (no Home Assistant needed).

Run with: python -m pytest tests
"""

from datetime import date, timedelta
import importlib.util
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

_PATH = (
    Path(__file__).resolve().parents[1] / "custom_components" / "veolia" / "history.py"
)
_SPEC = importlib.util.spec_from_file_location("veolia_history", _PATH)
history = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = history
_SPEC.loader.exec_module(history)

TZ = ZoneInfo("Europe/Paris")
TODAY = date(2026, 11, 14)


def _build(readings, base_sum=0.0):
    return history.build_daily_stats(readings, base_sum=base_sum, today=TODAY, tz=TZ)


def test_readings_from_records_skips_invalid():
    """Records without a valid day or volume are ignored."""
    records = [
        {"date_releve": "2026-11-01", "consommation": {"litre": 198}},
        {"consommation": {"litre": 50}},
        {"date_releve": "2026-11-02", "consommation": {"litre": None}},
        {"date_releve": "2026-11-03", "consommation": {"litre": "abc"}},
    ]
    readings = history.readings_from_records(
        records, date_key="date_releve", conso_key="consommation", litre_key="litre"
    )
    assert readings == [(date(2026, 11, 1), 198.0)]


def test_first_import_starts_at_base():
    """A first import starts the running sum at zero."""
    stats = _build([(date(2026, 11, 1), 198), (date(2026, 11, 2), 141)])
    assert [s.state for s in stats] == [0.198, 0.141]
    assert [s.sum for s in stats] == [0.198, 0.339]


def test_base_sum_continues_cumul():
    """A re-import continues from the sum stored before the window."""
    stats = _build([(date(2026, 11, 1), 198), (date(2026, 11, 2), 141)], 10.0)
    assert [s.sum for s in stats] == [10.198, 10.339]


def test_excludes_today_and_future():
    """Only complete days (before today) are imported."""
    stats = _build(
        [
            (date(2026, 11, 13), 100),
            (date(2026, 11, 14), 100),
            (date(2026, 11, 15), 100),
        ]
    )
    assert [s.start.date() for s in stats] == [date(2026, 11, 13)]


def test_duplicate_day_last_wins():
    """A day received twice is counted once, last value wins."""
    stats = _build([(date(2026, 11, 1), 100), (date(2026, 11, 1), 150)])
    assert len(stats) == 1
    assert stats[0].state == 0.15


def test_gap_keeps_cumul():
    """Missing days create no row and keep the running sum."""
    stats = _build([(date(2026, 11, 1), 100), (date(2026, 11, 5), 200)])
    assert [s.start.date() for s in stats] == [date(2026, 11, 1), date(2026, 11, 5)]
    assert [s.sum for s in stats] == [0.1, 0.3]


def test_corrected_day_shifts_following_sums():
    """A corrected day shifts every following sum."""
    first = _build(
        [(date(2026, 11, 1), 100), (date(2026, 11, 2), 100), (date(2026, 11, 3), 100)]
    )
    assert [s.sum for s in first] == [0.1, 0.2, 0.3]
    corrected = _build(
        [(date(2026, 11, 1), 100), (date(2026, 11, 2), 400), (date(2026, 11, 3), 100)]
    )
    assert [s.sum for s in corrected] == [0.1, 0.5, 0.6]


def test_local_midnight_across_dst():
    """Rows start at local midnight on both sides of a DST change."""
    stats = _build([(date(2026, 3, 28), 100), (date(2026, 3, 30), 100)])
    assert [s.start.hour for s in stats] == [0, 0]
    assert stats[0].start.utcoffset() == timedelta(hours=1)
    assert stats[1].start.utcoffset() == timedelta(hours=2)


def test_window_start():
    """The window starts at the first complete day."""
    readings = [
        (date(2026, 11, 5), 10),
        (date(2026, 11, 1), 10),
        (date(2026, 11, 14), 10),
    ]
    assert history.window_start(readings, today=TODAY) == date(2026, 11, 1)
    assert history.window_start([], today=TODAY) is None
