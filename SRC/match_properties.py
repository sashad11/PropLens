
# PROPLENS - PROPERTY AND MONITORING STATION MATCHING
#
# Purpose:
# 1. Match our six real London buildings to nearby LAQN stations.
# 2. Calculate the straight-line distance to each station.
# 3. Save our existing matches to a CSV file.
# 4. Explore three nearby alternative stations for each building.


# IMPORTS
# Import the Python tools required by this script.

import csv                  # Reads and writes CSV files.
import json                 # Reads saved LAQN station information.

from math import (
    radians, sin, cos, sqrt, atan2
)                           # Mathematical functions for distance calculations.


# STEP 1: DEFINE THE DISTANCE CALCULATION

def distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate the approximate straight-line distance between
    two locations using latitude and longitude.

    Returns the distance in kilometres.
    """

    # Approximate radius of Earth in kilometres.
    earth_radius = 6371

    # Convert coordinates from degrees to radians.
    # Python's trigonometric functions use radians.
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # Calculate the differences between the locations.
    latitude_difference = lat2 - lat1
    longitude_difference = lon2 - lon1

    # Apply the Haversine formula to estimate distance.
    a = (
        sin(latitude_difference / 2) ** 2
        + cos(lat1) * cos(lat2)
        * sin(longitude_difference / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Return the calculated distance.
    return earth_radius * c


# STEP 2: LOAD OUR SIX BUILDING LOCATIONS

# Create a list to store our building records.
properties = []

# Read the buildings from our CSV file.
with open("Data/properties.csv", "r", encoding="utf-8") as file:

    # DictReader uses the CSV headings as dictionary keys.
    reader = csv.DictReader(file)

    # Add each building to our properties list.
    for property_row in reader:
        properties.append(property_row)

# Stop if the CSV does not contain any buildings.
if not properties:
    raise ValueError("No buildings were found in Data/properties.csv.")


# STEP 3: LOAD LAQN MONITORING STATION INFORMATION

# Read the station metadata we previously downloaded.
# This includes station names, types and geographical coordinates.
with open(
    "Data/raw/london_stations.json",
    "r",
    encoding="utf-8"
) as file:
    station_data = json.load(file)

# Extract the list of monitoring stations from the JSON.
stations = station_data["Sites"]["Site"]


# STEP 4: IDENTIFY OUR ORIGINAL SEVEN STATIONS

# These are the stations we originally selected for PropLens.
# They already have historical measurements in our database.
selected_stations = [
    "CE3", "TH4", "CR9", "EN5",
    "GT1", "BT4", "RI2"
]

# Keep station metadata only for the selected station codes.
available_stations = [
    station for station in stations
    if station["@SiteCode"] in selected_stations
]

# Stop if the selected stations cannot be found.
if not available_stations:
    raise ValueError("No selected monitoring stations were found.")


# STEP 5: MATCH EACH BUILDING TO AN EXISTING STATION

print("\nPROPLENS - CURRENT BUILDING MATCHES")
print("----------------------------------")

# This list will hold the results that we save to CSV.
property_matches = []

# Go through every building in our dataset.
for property_row in properties:

    # Convert the building's coordinates from text into numbers.
    property_lat = float(property_row["latitude"])
    property_lon = float(property_row["longitude"])

    # Start without a matching station.
    # Infinity ensures that the first distance will be smaller.
    nearest_station = None
    nearest_distance = float("inf")

    # Compare this building with each of our original stations.
    for station in available_stations:

        # Read the real station coordinates provided by LAQN.
        station_lat = float(station["@Latitude"])
        station_lon = float(station["@Longitude"])

        # Calculate the distance from the building to this station.
        distance = distance_km(
            property_lat,
            property_lon,
            station_lat,
            station_lon
        )

        # If this is the closest station so far, remember it.
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_station = station

    # Display the closest match for this building.
    print(f"\nBuilding: {property_row['property_name']}")
    print(f"Station: {nearest_station['@SiteName']}")
    print(f"Station code: {nearest_station['@SiteCode']}")
    print(f"Distance: {nearest_distance:.2f} km")

    # Save the result as a dictionary.
    property_matches.append({
        "property_id": property_row["property_id"],
        "property_name": property_row["property_name"],
        "building_type": property_row["building_type"],
        "station_code": nearest_station["@SiteCode"],
        "station_name": nearest_station["@SiteName"],
        "distance_km": round(nearest_distance, 2)
    })


# STEP 6: SAVE OUR CURRENT MATCHES TO A CSV

# Define the columns in the output file.
columns = [
    "property_id",
    "property_name",
    "building_type",
    "station_code",
    "station_name",
    "distance_km"
]

# Open the output file for writing.
# Running the script again updates the CSV with the latest matches.
with open(
    "Data/property_matches.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    # Create a writer that uses the column names above.
    writer = csv.DictWriter(file, fieldnames=columns)

    # Write the header row.
    writer.writeheader()

    # Write all six property-to-station matches.
    writer.writerows(property_matches)

print("\nCurrent matches saved to Data/property_matches.csv")


# STEP 7: EXPLORE THREE NEARBY ALTERNATIVE STATIONS

# Now that we have our working matches, we can explore
# other LAQN stations without changing our current report.
print("\nPROPLENS - NEARBY STATION CANDIDATES")
print("----------------------------------")

# Check each building separately.
for property_row in properties:

    # Convert this building's coordinates into numbers.
    property_lat = float(property_row["latitude"])
    property_lon = float(property_row["longitude"])

    # Store possible stations and their distances.
    candidates = []

    # Examine all stations in the saved LAQN metadata.
    for station in stations:

        # Exclude stations with a recorded closure date.
        if station.get("@DateClosed") not in ("", None):
            continue

        # Find the pollutants monitored at this station.
        species = station.get("Species", [])

        # LAQN may return one pollutant as a dictionary
        # instead of a list, so make the format consistent.
        if isinstance(species, dict):
            species = [species]

        # Handle stations without pollutant information.
        if species is None:
            species = []

        # Store pollutant codes with no recorded finish date.
        active_pollutants = []

        for pollutant in species:

            # No finish date suggests the pollutant
            # may still be monitored at this station.
            if pollutant.get("@DateMeasurementFinished") in ("", None):
                active_pollutants.append(
                    pollutant.get("@SpeciesCode")
                )

        # Only explore stations that list PM2.5 measurements.
        # This helps us find suitable candidates for our new analysis.
        if "PM25" not in active_pollutants:
            continue

        # Read the station's geographical coordinates.
        station_lat = float(station["@Latitude"])
        station_lon = float(station["@Longitude"])

        # Calculate its distance from the current building.
        distance = distance_km(
            property_lat,
            property_lon,
            station_lat,
            station_lon
        )

        # Store the information needed to assess this station.
        candidates.append({
            "code": station["@SiteCode"],
            "name": station["@SiteName"],
            "type": station.get("@SiteType", "Unknown"),
            "pollutants": active_pollutants,
            "distance": distance
        })

    # Sort the stations from nearest to furthest.
    candidates.sort(
        key=lambda candidate: candidate["distance"]
    )

    # Display the three closest candidates.
    print(f"\nBuilding: {property_row['property_name']}")

    for candidate in candidates[:3]:

        print(
            f"{candidate['code']} | "
            f"{candidate['distance']:.2f} km | "
            f"{candidate['type']} | "
            f"{candidate['pollutants']}"
        )


# STEP 8: FINISH

print("\nProperty matching and station exploration completed.")
