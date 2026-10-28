
# PROPLENS - PROPERTY AND STATION MATCHING
# Purpose: Match hypothetical property locations to nearby
# LAQN monitoring stations using geographical coordinates.

# Read our property CSV and saved station information.
import csv
import json

# Mathematical tools for calculating geographical distances.
from math import radians, sin, cos, sqrt, atan2


# STEP 1: DEFINE OUR DISTANCE FUNCTION

def distance_km(lat1, lon1, lat2, lon2):
    """Calculate straight-line distance between two locations in km."""

    # Earth's approximate radius in kilometres.
    earth_radius = 6371

    # Convert latitude and longitude from degrees to radians.
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # Find the difference between the two locations.
    latitude_difference = lat2 - lat1
    longitude_difference = lon2 - lon1

    # Use the Haversine formula to calculate geographical distance.
    a = (
        sin(latitude_difference / 2) ** 2
        + cos(lat1) * cos(lat2)
        * sin(longitude_difference / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Return the distance in kilometres.
    return earth_radius * c


# STEP 2: LOAD OUR TEST PROPERTY DATA

properties = []

# Read the six fictional property locations from our CSV.
with open("Data/properties.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for property_row in reader:
        properties.append(property_row)


# STEP 3: LOAD REAL LAQN STATION COORDINATES

# Read station metadata previously downloaded from LAQN.
with open("Data/raw/london_stations.json", "r", encoding="utf-8") as file:
    station_data = json.load(file)

# Extract the monitoring stations from the API response.
stations = station_data["Sites"]["Site"]


# STEP 4: SELECT STATIONS WITH COLLECTED HISTORICAL DATA

# These are the seven regional stations chosen for PropLens.
selected_stations = [
    "CE3", "TH4", "CR9", "EN5",
    "GT1", "BT4", "RI2"
]

# Keep only metadata for our seven selected stations.
available_stations = [
    station for station in stations
    if station["@SiteCode"] in selected_stations
]

# Stop if none of the selected stations were found.
if not available_stations:
    raise ValueError("No selected monitoring stations were found.")


# STEP 5: MATCH EACH PROPERTY TO ITS NEAREST SELECTED STATION
# DEBUG: Check whether our data loaded correctly.
print("Matching section reached")
print(f"Properties loaded: {len(properties)}")
print(f"Stations available: {len(available_stations)}")

# Store property-to-station matches so we can save them later.
property_matches = []
# Check each property in our CSV.
for property_row in properties:

    # Convert the property's coordinates into numbers.
    property_lat = float(property_row["latitude"])
    property_lon = float(property_row["longitude"])

    # Start without a match.
    nearest_station = None
    nearest_distance = float("inf")

    # Compare the property against every selected station.
    for station in available_stations:

        # Read the real station coordinates from LAQN.
        station_lat = float(station["@Latitude"])
        station_lon = float(station["@Longitude"])

        # Calculate the straight-line distance in kilometres.
        distance = distance_km(
            property_lat,
            property_lon,
            station_lat,
            station_lon
        )

        # Remember the station if it is the closest so far.
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_station = station

    # Display the result for this property.
    # These lines are INSIDE the outer loop.
    print(f"\nProperty: {property_row['property_name']}")
    print(f"Nearest station: {nearest_station['@SiteName']}")
    print(f"Station code: {nearest_station['@SiteCode']}")
    print(f"Distance: {nearest_distance:.2f} km")

        # Store the property and its closest station as one record.
    property_matches.append({
        "property_id": property_row["property_id"],
        "property_name": property_row["property_name"],
        "station_code": nearest_station["@SiteCode"],
        "station_name": nearest_station["@SiteName"],
        "distance_km": round(nearest_distance, 2)
    })

# STEP 6: SAVE THE MATCHES TO A CSV FILE

# Define the columns in our output file.
columns = [
    "property_id",
    "property_name",
    "station_code",
    "station_name",
    "distance_km"
]

# Save the matching results for our next analysis script.
with open("Data/property_matches.csv", "w", newline="", encoding="utf-8") as file:

    # Create a CSV writer using our column names.
    writer = csv.DictWriter(file, fieldnames=columns)

    # Write the column headings.
    writer.writeheader()

    # Write each property-to-station match.
    writer.writerows(property_matches)

print("\nProperty matches saved to Data/property_matches.csv")
