# PROPLENS SHARED REPORTING PERIOD
#
# WHY THIS FILE EXISTS
# Before this improvement, some reports used a fixed end date in October.
# New API readings could reach DuckDB while the charts remained unchanged.
# This file chooses ONE reporting period and saves it as a small JSON file.
# Every report can then use the same dates and expected number of hours.
#
# HOW THE END DATE IS CHOSEN
# We look for dates that are not today, since today is not a complete day.
# For each configured station and pollutant pair, we check whether DuckDB
# contains all 24 distinct UTC hour timestamps on that date. We choose the
# latest date that meets this condition for EVERY configured target.
#
# WHAT THIS DOES NOT GUARANTEE
# Having 24 timestamps does not mean having 24 valid numeric readings.
# Quality screening and the 90 percent threshold are separate checks.
# Also, the code finds the latest common complete day, not proof that every
# earlier day is complete. The separate quality checks expose missing data.
#
# FILE OUTPUT
# Outputs/reporting_period.json stores the selected start and end dates,
# the exclusive end boundary, and the expected number of hourly readings.
# 'End exclusive' means the next day's midnight, which simplifies SQL filters.

# PROPLENS REPORTING WINDOW
# Keep every report on the same complete calendar-day window.
# The collector may have more recent data than the published reports.

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json
import duckdb

from config import historical_start_date, monitoring_targets

PROJECT = Path(__file__).resolve().parents[1]
DATABASE = PROJECT / "Data/proplens.duckdb"
METADATA = PROJECT / "Outputs/reporting_period.json"


def choose_window():
    """Find the latest completed UTC day with 24 recorded hours for EVERY target.

    This checks timestamp availability, not validity of all numerical readings.
    Quality screening happens later in station_quality.py.
    """
    if not DATABASE.exists():
        raise FileNotFoundError(f"Database does not exist: {DATABASE}")
    targets = {(t['site_code'], t['species_code']) for t in monitoring_targets}
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
    con = duckdb.connect(str(DATABASE), read_only=True)
    try:
        # Collect day, station and pollutant combinations with all 24 hourly timestamps.
        rows = con.execute("""
            SELECT CAST(measured_at AS DATE) AS day, site_code, species_code
            FROM measurements
            WHERE measured_at >= ? AND measured_at < ?
            GROUP BY day, site_code, species_code
            HAVING COUNT(DISTINCT EXTRACT(HOUR FROM measured_at)) = 24
        """, [historical_start_date, (yesterday + timedelta(days=1)).isoformat()]).fetchall()
    finally:
        con.close()
    complete_by_day = {}
    for day, site, species in rows:
        complete_by_day.setdefault(day, set()).add((site, species))
    dates = [day for day, available in complete_by_day.items() if targets.issubset(available)]
    if not dates:
        raise ValueError("No completed UTC day has all 24 hours for every configured target")
    latest = max(dates)
    start = date.fromisoformat(historical_start_date)
    if latest < start:
        raise ValueError("Latest complete day is before historical start")
    end_exclusive = latest + timedelta(days=1)
    return {
        "start_date": start.isoformat(),
        "end_date": latest.isoformat(),
        "end_exclusive": end_exclusive.isoformat(),
        "expected_hours": (end_exclusive - start).days * 24,
        "target_count": len(targets),
        "rule": "latest completed UTC date with 24 stored hourly timestamps for every configured station and pollutant"
    }


def save_window():
    window = choose_window()
    METADATA.parent.mkdir(parents=True, exist_ok=True)
    METADATA.write_text(json.dumps(window, indent=2) + "\n", encoding="utf-8")
    print(f"Reporting window: {window['start_date']} through {window['end_date']} ({window['expected_hours']} expected hours)")
    return window


def read_window():
    if not METADATA.exists():
        raise FileNotFoundError("Reporting window missing. First run: python SRC/update_all.py")
    window = json.loads(METADATA.read_text(encoding="utf-8"))
    if window['expected_hours'] <= 0:
        raise ValueError("Invalid reporting window")
    return window
