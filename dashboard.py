
# PROPLENS DASHBOARD
#
# Purpose:
# Create an interactive dashboard to explore air quality
# measurements near different types of London buildings.

from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px


# STEP 1: CONFIGURE THE DASHBOARD

st.set_page_config(
    page_title="PropLens",
    page_icon="🏙️",
    layout="wide"
)


# STEP 2: FIND OUR PROJECT FILES

project_folder = Path(__file__).resolve().parent
outputs_folder = project_folder / "Outputs"


# STEP 3: LOAD OUR ANALYSIS REPORTS

# These CSV files were created by our Python and SQL scripts.
no2_data = pd.read_csv(
    outputs_folder / "property_comparison.csv"
)

pm25_data = pd.read_csv(
    outputs_folder / "pm25_comparison.csv"
)


# STEP 4: DISPLAY THE DASHBOARD TITLE

st.title("PropLens")

st.write(
    "Exploring historical air quality measurements "
    "near different types of buildings in London."
)

st.caption(
    "Historical analysis: 1 August to 28 October 2026. "
    "Measurements come from nearby monitoring stations, "
    "not directly from the buildings."
)


# STEP 5: SHOW OUR DATA SUMMARY

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Buildings", len(no2_data))

with col2:
    st.metric("Pollutants", 2)

with col3:
    st.metric("Historical days", 89)


# STEP 6: DISPLAY THE COMPARISON TABLES

st.subheader("Building comparisons")

pollutant = st.selectbox(
    "Choose a pollutant",
    ["NO₂", "PM₂.₅"]
)

if pollutant == "NO₂":
    selected_data = no2_data
else:
    selected_data = pm25_data

    
# STEP 7: CREATE AN INTERACTIVE COMPARISON CHART

# Choose the correct concentration column.
if pollutant == "NO₂":
    value_column = "average_no2_ug_m3"
else:
    value_column = "average_pm25_ug_m3"

# Several buildings share the same monitoring station.
# Keep each station only once to avoid repeating its data.
chart_data = selected_data.drop_duplicates(
    subset=["station_code"]
).copy()

# Sort stations by their average pollution concentration.
chart_data = chart_data.sort_values(
    by=value_column,
    ascending=True
)

# Create an interactive bar chart using Plotly.
fig = px.bar(
    chart_data,
    x="station_code",
    y=value_column,
    color="station_type",
    hover_data=[
        "station_name",
        "station_type"
    ],
    labels={
        "station_code": "Monitoring station",
        value_column: "Average concentration (µg/m³)",
        "station_type": "Station type"
    },
    title=f"Average {pollutant} by monitoring station"
)

# Improve the chart's appearance.
fig.update_layout(
    height=420,
    xaxis_title="Monitoring station",
    yaxis_title="Average concentration (µg/m³)"
)

# Show the chart in our Streamlit dashboard.
st.plotly_chart(fig, use_container_width=True)

# Explain why there are fewer bars than buildings.
st.caption(
    "Each monitoring station appears once, even when "
    "multiple buildings share its measurements."
)

# STEP 8: DISPLAY A SIMPLER BUILDING COMPARISON TABLE

# Choose the columns that matter most to someone
# exploring the dashboard.
table_data = selected_data[
    [
        "property_name",
        "building_type",
        "station_code",
        "station_type",
        value_column,
        "distance_km",
        "distance_status",
        "completeness_percent"
    ]
].copy()

# Rename the columns so they are easier to understand.
table_data.columns = [
    "Building",
    "Building type",
    "Station",
    "Station type",
    "Average (µg/m³)",
    "Distance (km)",
    "Distance warning",
    "Data completeness (%)"
]

# Display the simplified table.
st.dataframe(
    table_data,
    hide_index=True,
    use_container_width=True
)


# STEP 9: DISPLAY MONTHLY POLLUTION TRENDS
#
# Purpose:
# Show how average pollution levels changed across
# August, September and October 2026.

st.subheader("Monthly pollution trends")

st.write(
    "Explore how average pollution concentrations changed "
    "at each monitoring station over the three months."
)


# STEP 10: LOAD THE CORRECT MONTHLY REPORT

# NO2 and PM2.5 currently have separate CSV reports.
if pollutant == "NO₂":

    monthly_data = pd.read_csv(
        outputs_folder / "monthly_trends.csv"
    )

    monthly_value = "average_no2"

else:

    monthly_data = pd.read_csv(
        outputs_folder / "monthly_pm25.csv"
    )

    monthly_value = "average_pm25_ug_m3"


# STEP 11: PREPARE THE DATA

# Only show stations used in our current comparison.
selected_stations = selected_data["station_code"].unique()

monthly_data = monthly_data[
    monthly_data["station_code"].isin(selected_stations)
].copy()

# Some buildings share monitoring stations.
# Keep each station only once per month.
monthly_data = monthly_data.drop_duplicates(
    subset=["station_code", "month"]
)

# Convert the month column into dates so Plotly
# displays August, September and October in order.
monthly_data["month"] = pd.to_datetime(
    monthly_data["month"]
)

monthly_data = monthly_data.sort_values("month")


# STEP 12: CREATE OUR MONTHLY LINE CHART

monthly_fig = px.line(
    monthly_data,
    x="month",
    y=monthly_value,
    color="station_code",
    markers=True,
    labels={
        "month": "Month",
        monthly_value: "Average concentration (µg/m³)",
        "station_code": "Monitoring station"
    },
    title=f"Monthly average {pollutant} by monitoring station"
)

# Make the chart easier to read.
monthly_fig.update_layout(
    height=450,
    xaxis_title="Month",
    yaxis_title="Average concentration (µg/m³)"
)

monthly_fig.update_xaxes(
    tickformat="%b %Y",
    dtick="M1"
)

# Display the interactive chart.
st.plotly_chart(
    monthly_fig,
    width="stretch"
)

st.caption(
    "Each line represents one monitoring station. "
    "Shared stations are counted once. "
    "October includes measurements only up to 28 October."
)


# STEP 13: EXPLORE HOURLY POLLUTION PATTERNS
#
# Compare pollution concentrations at different hours
# of the day on weekdays and weekends.

st.subheader("Hourly pollution patterns")

st.write(
    "See how pollution levels change throughout the day "
    "and compare weekday and weekend measurements."
)


# STEP 14: LOAD HOURLY DATA

hourly_data = pd.read_csv(
    outputs_folder / "hourly_patterns.csv"
)

# Match the pollutant selected earlier.
pollutant_code = "NO2" if pollutant == "NO₂" else "PM25"

hourly_data = hourly_data[
    hourly_data["species_code"] == pollutant_code
].copy()


# STEP 15: LET THE USER CHOOSE A STATION

# Only offer stations included in our current
# building comparisons.
available_stations = sorted(
    set(hourly_data["site_code"])
    & set(selected_data["station_code"])
)

selected_station = st.selectbox(
    "Choose a monitoring station",
    available_stations
)

# Keep only the selected station's measurements.
station_hourly = hourly_data[
    hourly_data["site_code"] == selected_station
].copy()


# STEP 16: CREATE THE HOURLY LINE CHART

hourly_fig = px.line(
    station_hourly,
    x="hour_of_day",
    y="average_concentration",
    color="day_type",
    markers=True,
    category_orders={
        "day_type": ["Weekday", "Weekend"]
    },
    labels={
        "hour_of_day": "Hour of day (GMT)",
        "average_concentration": "Average concentration (µg/m³)",
        "day_type": "Day type"
    },
    title=f"Hourly {pollutant} patterns at {selected_station}"
)

hourly_fig.update_layout(
    height=450,
    xaxis_title="Hour of day (GMT)",
    yaxis_title="Average concentration (µg/m³)"
)

hourly_fig.update_xaxes(
    tickmode="linear",
    dtick=2
)

st.plotly_chart(
    hourly_fig,
    width="stretch"
)

st.caption(
    "Hours are shown in GMT. During British Summer Time, "
    "local London time is one hour ahead. "
    "Patterns show averages at the monitoring station "
    "and do not establish what caused the changes."
)


# STEP 17: MAP BUILDINGS AND MONITORING STATIONS
#
# Show where the six buildings are located
# and where their matched monitoring stations are.

import json

st.subheader("Building and monitoring station locations")

st.write(
    "Explore the geographical locations of our six "
    "buildings and their associated monitoring stations."
)

# STEP 18: LOAD THE BUILDING LOCATIONS

buildings = pd.read_csv(
    project_folder / "Data/properties.csv"
)

# Keep the coordinates and give each location a label.
building_locations = buildings[
    ["property_name", "latitude", "longitude"]
].copy()

building_locations = building_locations.rename(
    columns={"property_name": "name"}
)

building_locations["location_type"] = "Building"


# STEP 19: LOAD THE STATION LOCATIONS

# Station coordinates come from the LAQN metadata.
with open(
    project_folder / "Data/Raw/london_stations.json",
    encoding="utf-8"
) as file:
    station_metadata = json.load(file)

stations = station_metadata["Sites"]["Site"]

# Find station codes used by either pollutant.
used_station_codes = set(no2_data["station_code"]) | set(
    pm25_data["station_code"]
)

station_locations = []

for station in stations:

    if station["@SiteCode"] not in used_station_codes:
        continue

    station_locations.append({
        "name": station["@SiteName"],
        "latitude": float(station["@Latitude"]),
        "longitude": float(station["@Longitude"]),
        "location_type": "Monitoring station"
    })


# STEP 20: COMBINE BOTH TYPES OF LOCATIONS

station_locations = pd.DataFrame(station_locations)

map_data = pd.concat(
    [building_locations, station_locations],
    ignore_index=True
)

# Assign different colours to buildings and stations.
map_data["color"] = map_data["location_type"].map({
    "Building": "#38BDF8",
    "Monitoring station": "#F97316"
})


# STEP 21: DISPLAY THE MAP
# MAP LEGEND
# Explain what each marker colour represents.

col1, col2 = st.columns(2)

with col1:
    st.markdown("🔵 **Blue = Building**")

with col2:
    st.markdown("🟠 **Orange = Monitoring station**")
    
st.map(
    map_data,
    latitude="latitude",
    longitude="longitude",
    color="color",
    size=100,
    zoom=10
)

st.caption(
    "Blue markers represent buildings. Orange markers "
    "represent monitoring stations. The map shows locations, "
    "not pollution exposure or measurement coverage."
)

# STEP 6: INTRODUCE OUR COMPARISON CHART

st.subheader("Air quality comparisons")

st.write(
    "Compare historical pollutant levels at monitoring stations "
    "associated with our six London buildings."
)

# STEP 7: EXPLAIN OUR DATA LIMITATIONS

st.info(
    "Monitoring stations measure pollution at their own "
    "locations. Some buildings share a station, and some "
    "stations are several kilometres away. These results "
    "should not be treated as measurements of individual "
    "building exposure."
)

