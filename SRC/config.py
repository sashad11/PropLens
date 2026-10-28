# PROPLENS - PIPELINE CONFIGURATION
# Purpose: Keep our monitoring station and pollutant choices
# in one place, rather than repeating them across scripts.


# PROPLENS - MONITORING TARGETS
# Purpose: Tell our pipeline which station and pollutant
# combinations to collect data for.
#
# These combinations returned usable numerical measurements
# in our initial one-day tests.

monitoring_targets = [
    {"site_code": "CE3", "species_code": "NO2"},   # Central
    {"site_code": "TH4", "species_code": "NO2"},   # East
    {"site_code": "CR9", "species_code": "NO2"},   # South
    {"site_code": "EN5", "species_code": "NO2"},   # North
    {"site_code": "GT1", "species_code": "NO2"},   # West
    {"site_code": "BT4", "species_code": "NO2"},   # Northwest
    {"site_code": "RI2", "species_code": "PM25"},  # Southwest

    # Original stations used while developing our pipeline.
    {"site_code": "BX1", "species_code": "NO2"},
    {"site_code": "BX2", "species_code": "NO2"},
    {"site_code": "BQ9", "species_code": "PM25"}
]


# Start collecting historical measurements from 1 August 2026.
historical_start_date = "2026-08-01"

# Allow up to 30 new daily downloads per target per run.
# The collector will continue skipping dates already cached.
max_days_per_target = 50