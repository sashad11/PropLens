
# PROPLENS - PM2.5 BUILDING COMPARISON
#
# Purpose:
# Compare historical PM2.5 measurements near London buildings.
# Use confirmed stations with usable historical data.
#
# Important:
# These are station measurements, not direct measurements
# of people's exposure at individual buildings.


# IMPORTS

import csv
from pathlib import Path

import duckdb


# STEP 1: DEFINE OUR PM2.5 STATION MATCHES

# These matches are based on our station exploration
# and the historical PM2.5 coverage checks.
pm25_stations = {
    "P001": "GT1",  # Fox Primary School
    "P002": "CE3",  # St Thomas' Hospital
    "P003": "BT8",  # Magnolia Court Care Home
    "P004": "CE3",  # UCL North-West Wing
    "P005": "CE3"   # 80 Strand
}

# Barbican Estate (P006) is intentionally excluded.
# We have not confirmed a sufficiently suitable PM2.5 station.


# STEP 2: LOAD OUR BUILDING DATA

properties = []

with open("Data/properties.csv", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for property_row in reader:
        properties.append(property_row)


# STEP 3: LOAD OUR STATION COORDINATES

# Use LAQN metadata to calculate the distance between
# each building and its chosen PM2.5 monitoring station.
import json
from math import radians, sin, cos, sqrt, atan2

with open("Data/raw/london_stations.json", encoding="utf-8") as file:
    station_data = json.load(file)

stations = {
    station["@SiteCode"]: station
    for station in station_data["Sites"]["Site"]
}


# STEP 4: DEFINE THE DISTANCE FUNCTION

def distance_km(lat1, lon1, lat2, lon2):
    """Calculate straight-line distance using the Haversine formula."""

    radius = 6371

    lat1, lon1 = radians(lat1), radians(lon1)
    lat2, lon2 = radians(lat2), radians(lon2)

    difference_lat = lat2 - lat1
    difference_lon = lon2 - lon1

    a = (
        sin(difference_lat / 2) ** 2
        + cos(lat1) * cos(lat2)
        * sin(difference_lon / 2) ** 2
    )

    return radius * 2 * atan2(sqrt(a), sqrt(1 - a))


# STEP 5: CONNECT TO DUCKDB

connection = duckdb.connect("Data/proplens.duckdb")


# STEP 6: COMPARE PM2.5 MEASUREMENTS

report_rows = []

print("\nPROPLENS - PM2.5 BUILDING COMPARISON")
print("-----------------------------------")

for property_row in properties:

    property_id = property_row["property_id"]

    # Do not invent a match for buildings without coverage.
    if property_id not in pm25_stations:
        print(
            f"\n{property_row['property_name']}: "
            "No suitable PM2.5 station confirmed."
        )
        continue

    station_code = pm25_stations[property_id]
    station = stations[station_code]

    # Calculate the straight-line building-to-station distance.
    distance = distance_km(
        float(property_row["latitude"]),
        float(property_row["longitude"]),
        float(station["@Latitude"]),
        float(station["@Longitude"])
    )

    # Calculate average PM2.5 and measurement completeness.
    result = connection.execute("""
        SELECT
            ROUND(AVG(value), 2),
            COUNT(*),
            COUNT(value),
            ROUND(100.0 * COUNT(value) / COUNT(*), 1)
        FROM measurements
        WHERE site_code = ?
          AND species_code = 'PM25'
    """, [station_code]).fetchone()

    average, recorded, valid, completeness = result

    # Label the station's data completeness.
    if completeness >= 95:
        quality = "GOOD"
    elif completeness >= 80:
        quality = "CAUTION"
    else:
        quality = "POOR"

    # Flag distant monitoring stations.
    if distance <= 2:
        distance_status = "NEARBY"
    elif distance <= 3:
        distance_status = "CAUTION"
    else:
        distance_status = "DISTANT"

    # Show the result in the terminal.
    print(f"\nBuilding: {property_row['property_name']}")
    print(f"Building type: {property_row['building_type']}")
    print(f"Station: {station_code}")
    print(f"Distance: {distance:.2f} km ({distance_status})")
    print(f"Average PM2.5: {average} ug/m3")
    print(f"Completeness: {completeness}% ({valid}/{recorded})")
    print(f"Data quality: {quality}")

    if distance_status == "DISTANT":
        print("Warning: Station may not represent local conditions.")

    # Prepare the result for our CSV output.
    report_rows.append({
        "property_name": property_row["property_name"],
        "building_type": property_row["building_type"],
        "station_code": station_code,
        "distance_km": round(distance, 2),
        "distance_status": distance_status,
        "average_pm25_ug_m3": average,
        "recorded_hours": recorded,
        "valid_hours": valid,
        "completeness_percent": completeness,
        "data_quality": quality
    })


# STEP 7: SAVE THE REPORT

Path("Outputs").mkdir(exist_ok=True)

columns = [
    "property_name",
    "building_type",
    "station_code",
    "distance_km",
    "distance_status",
    "average_pm25_ug_m3",
    "recorded_hours",
    "valid_hours",
    "completeness_percent",
    "data_quality"
]

with open(
    "Outputs/pm25_comparison.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(file, fieldnames=columns)
    writer.writeheader()
    writer.writerows(report_rows)


# STEP 8: CLOSE THE DATABASE

connection.close()

print("\nPM2.5 report saved to Outputs/pm25_comparison.csv")
