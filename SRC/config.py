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


# The earliest date for our initial historical collection.
# We'll expand this after testing the multi-station pipeline.
historical_start_date = "2026-10-19"


# Define how much historical data we eventually want.
# We start with a short period while testing each station.
# Once the extraction is reliable, we'll expand the date range.
historical_start_date = "2026-10-19"


# Maximum number of new days to download for each station
# during one pipeline run.
# We start with 3 days to test historical collection safely.
max_days_per_target = 3