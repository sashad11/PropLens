# PROPLENS - PIPELINE CONFIGURATION
# Purpose: Keep our monitoring station and pollutant choices
# in one place, rather than repeating them across scripts.


# PROPLENS - MONITORING TARGETS
# Purpose: Tell our pipeline which station and pollutant
# combinations to collect data for.
#
# These combinations returned usable numerical measurements
# in our initial one-day tests.


# PROPLENS - MONITORING TARGETS
# Each target tells the pipeline which station and pollutant to collect.

monitoring_targets = [
    # Existing NO2 monitoring stations.
    {"site_code": "CE3", "species_code": "NO2"},
    {"site_code": "TH4", "species_code": "NO2"},
    {"site_code": "CR9", "species_code": "NO2"},
    {"site_code": "EN5", "species_code": "NO2"},
    {"site_code": "GT1", "species_code": "NO2"},
    {"site_code": "BT4", "species_code": "NO2"},

    # Existing PM2.5 monitoring station.
    {"site_code": "RI2", "species_code": "PM25"},

    # Original stations used during development.
    {"site_code": "BX1", "species_code": "NO2"},
    {"site_code": "BX2", "species_code": "NO2"},
    {"site_code": "BQ9", "species_code": "PM25"},

    # New PM2.5 stations for our building analysis.
    {"site_code": "GT1", "species_code": "PM25"},
    {"site_code": "CE3", "species_code": "PM25"},
    {"site_code": "BT8", "species_code": "PM25"}
]


# Start collecting historical measurements from 1 August 2026.
historical_start_date = "2026-08-01"

# Allow up to 30 new daily downloads per target per run.
# The collector will continue skipping dates already cached.
max_days_per_target = 100

# Number of recent completed days to download again.
# LAQN may revise measurements after first publishing them.
refresh_days = 7