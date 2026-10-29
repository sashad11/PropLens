
# PROPLENS - AUTOMATIC STATION MATCHING
#
# Match each building separately for NO2 and PM25.
# Consider only stations with sufficient historical data.
# Keep distance and station-type warnings visible.

import csv
import json
from pathlib import Path

from geo_utils import distance_km


# STEP 1: FIND OUR PROJECT FILES

project_folder = Path(__file__).resolve().parents[1]

properties_file = project_folder / "Data/properties.csv"
stations_file = project_folder / "Data/Raw/london_stations.json"
quality_file = project_folder / "Outputs/station_quality.csv"
output_file = project_folder / "Outputs/station_matches.csv"

output_file.parent.mkdir(exist_ok=True)


# STEP 2: LOAD BUILDINGS

with open(properties_file, encoding="utf-8") as file:
    properties = list(csv.DictReader(file))


# STEP 3: LOAD STATION INFORMATION

with open(stations_file, encoding="utf-8") as file:
    station_data = json.load(file)

stations = station_data["Sites"]["Site"]

# Find station information quickly using its code.
station_lookup = {
    station["@SiteCode"]: station
    for station in stations
}


# STEP 4: FIND STATIONS WITH SUFFICIENT DATA

# These thresholds are our own project screening rules,
# not official LAQN suitability standards.
minimum_completeness = 90.0
minimum_recorded_hours = 2000

eligible_stations = []

with open(quality_file, encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:

        completeness = float(row["completeness_pct"])
        recorded = int(row["recorded_hours"])

        if (
            completeness >= minimum_completeness
            and recorded >= minimum_recorded_hours
            and row["site_code"] in station_lookup
        ):
            eligible_stations.append(row)


# STEP 5: MATCH EACH BUILDING FOR EACH POLLUTANT

results = []

for property_row in properties:

    property_lat = float(property_row["latitude"])
    property_lon = float(property_row["longitude"])

    for pollutant in ["NO2", "PM25"]:

        candidates = []

        # Examine only stations with historical data
        # for the pollutant currently being matched.
        for quality_row in eligible_stations:

            if quality_row["species_code"] != pollutant:
                continue

            station = station_lookup[quality_row["site_code"]]

            station_lat = float(station["@Latitude"])
            station_lon = float(station["@Longitude"])

            distance = distance_km(
                property_lat,
                property_lon,
                station_lat,
                station_lon
            )

            candidates.append({
                "station": station,
                "distance": distance,
                "quality": quality_row
            })

        # Choose the nearest qualifying station.
        candidates.sort(key=lambda item: item["distance"])

        if not candidates:
            print(
                f"No eligible {pollutant} station for "
                f"{property_row['property_name']}"
            )
            continue

        best = candidates[0]

        distance = best["distance"]

        if distance <= 2:
            distance_status = "NEARBY"
        elif distance <= 3:
            distance_status = "CAUTION"
        else:
            distance_status = "DISTANT"

        station = best["station"]
        quality = best["quality"]

        results.append({
            "property_id": property_row["property_id"],
            "property_name": property_row["property_name"],
            "building_type": property_row["building_type"],
            "pollutant": pollutant,
            "station_code": station["@SiteCode"],
            "station_name": station["@SiteName"],
            "station_type": station.get("@SiteType", "Unknown"),
            "distance_km": round(distance, 2),
            "distance_status": distance_status,
            "completeness_pct": quality["completeness_pct"],
            "recorded_hours": quality["recorded_hours"],
            "valid_hours": quality["valid_hours"]
        })


# STEP 6: SAVE THE MATCHES

columns = [
    "property_id",
    "property_name",
    "building_type",
    "pollutant",
    "station_code",
    "station_name",
    "station_type",
    "distance_km",
    "distance_status",
    "completeness_pct",
    "recorded_hours",
    "valid_hours"
]

with open(
    output_file,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(file, fieldnames=columns)
    writer.writeheader()
    writer.writerows(results)


# STEP 7: SHOW THE RESULTS

print("\nPROPLENS - AUTOMATIC STATION MATCHING")
print("------------------------------------")

for result in results:
    print(
        f"{result['property_name']} | "
        f"{result['pollutant']} | "
        f"{result['station_code']} | "
        f"{result['distance_km']:.2f} km | "
        f"{result['distance_status']} | "
        f"{result['completeness_pct']}% valid"
    )

print(f"\nSaved {len(results)} matches to:")
print("Outputs/station_matches.csv")
