# PROPLENS - PIPELINE CONFIGURATION
# Purpose: Keep our monitoring station and pollutant choices
# in one place, rather than repeating them across scripts.


# Create a list of station and pollutant combinations.
# Each dictionary represents one combination we want to collect.
# Later, this list can be selected automatically using station metadata.
monitoring_targets = [

    # Our original station, which we've already tested.
    {
        "site_code": "BX1",
        "species_code": "NO2"
    },

    # A second station measuring nitrogen dioxide.
    {
        "site_code": "BX2",
        "species_code": "NO2"
    },

    # A station associated with PM2.5 monitoring.
    {
        "site_code": "BQ9",
        "species_code": "PM25"
    }

]


# Define how much historical data we eventually want.
# We start with a short period while testing each station.
# Once the extraction is reliable, we'll expand the date range.
historical_start_date = "2026-10-19"
