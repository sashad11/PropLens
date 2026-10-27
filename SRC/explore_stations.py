# PROPLENS - MONITORING STATION DISCOVERY
# Purpose: Find potentially active London stations that monitor
# NO2 or PM2.5, using saved LAQN station information.


# Import the tools we need.
import json                 # Reads and saves JSON files.
import requests             # Communicates with the LAQN API.
from pathlib import Path    # Helps us work with file locations.


# STEP 1: Save or reuse the station information.

# Choose where to store the original station metadata.
file_path = Path("Data/raw/london_stations.json")

# Check whether we've already downloaded this information.
if file_path.exists():

    # Reuse our saved JSON instead of contacting the API.
    print("Loading saved station information.")

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

else:

    # The file doesn't exist, so retrieve station information.
    print("Downloading London station information.")

    url = (
        "https://api.erg.ic.ac.uk/AirQuality/Information/"
        "MonitoringSiteSpecies/GroupName=London/Json"
    )

    response = requests.get(url, timeout=30)

    # Stop if the API request failed.
    response.raise_for_status()

    # Convert the API response into Python data.
    data = response.json()

    # Save the original response for future use.
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


# STEP 2: Find all monitoring stations.

# Access the list of stations inside the JSON response.
stations = data["Sites"]["Site"]

# This list will hold stations matching our conditions.
suitable_stations = []


# STEP 3: Check each station.

for station in stations:

    # Read the station's closure date.
    # An empty string means no closure date is recorded.
    date_closed = station.get("@DateClosed", "")

    # Skip stations that have a recorded closure date.
    if date_closed not in ("", None):
        continue

    # Retrieve the station's pollutant information.
    species = station.get("Species", [])

    # Convert a single pollutant dictionary into a list.
    if isinstance(species, dict):
        species = [species]

    # If pollutant information is missing, use an empty list.
    if species is None:
        species = []

    # Create a list of pollutant codes for this station.
    pollutant_codes = []

    for pollutant in species:

        # Only use pollutants without a recorded finish date.
        # This does not guarantee that recent readings exist.
        date_finished = pollutant.get("@DateMeasurementFinished", "")

        if date_finished in ("", None):
            pollutant_codes.append(pollutant["@SpeciesCode"])

    # Check whether the station lists either target pollutant.
    if "NO2" in pollutant_codes or "PM25" in pollutant_codes:

        # Store useful information about the station.
        suitable_stations.append({
            "code": station["@SiteCode"],
            "name": station["@SiteName"],
            "borough": station["@LocalAuthorityName"],
            "latitude": float(station["@Latitude"]),
            "longitude": float(station["@Longitude"]),
            "pollutants": pollutant_codes
        })


# STEP 4: Display our results.

print(f"Potentially suitable stations found: {len(suitable_stations)}")

# Show the first 10 matching stations.
# [:10] selects up to 10 items from our list.
for station in suitable_stations[:10]:

    print("------------------------------")
    print(f"Code: {station['code']}")
    print(f"Name: {station['name']}")
    print(f"Borough: {station['borough']}")
    print(f"Pollutants: {station['pollutants']}")

    # PROPLENS - EXPLORE GEOGRAPHICAL COVERAGE
# Purpose: Find which London boroughs contain potentially
# suitable monitoring stations.


# Create an empty set to hold borough names.
# A set stores unique values, so each borough appears only once.
boroughs = set()


# Go through every suitable monitoring station.
for station in suitable_stations:

    # Add the station's borough to our set.
    # If the borough is already there, it won't be added twice.
    boroughs.add(station["borough"])


# Display how many different boroughs we found.
print(f"\nBoroughs represented: {len(boroughs)}")


# Display the boroughs in alphabetical order.
# sorted() arranges the names alphabetically.
for borough in sorted(boroughs):
    print(borough)

# PROPLENS - FIND STATIONS FOR INVESTMENT AREAS
# Purpose: Explore monitoring stations in our three chosen boroughs.


# PROPLENS - PROVISIONAL PROPERTY INVESTMENT AREAS
# We are exploring six boroughs across different parts of London.
# These are candidate locations, not our final property selections.
investment_areas = [
    "Westminster",       # Central London
    "Tower Hamlets",     # East London
    "Croydon",           # South London
    "Haringey",          # North London
    "Hillingdon",        # West London
    "Brent"              # Northwest London
]


# Go through each borough, one at a time.
for area in investment_areas:

    # Print the borough name so our results are easy to read.
    print(f"\n--- {area} ---")

    # Go through the stations we identified earlier.
    for station in suitable_stations:

        # Check whether the station belongs to this borough.
        if station["borough"] == area:

            # Show the station code, name and pollutants.
            print(f"Code: {station['code']}")
            print(f"Name: {station['name']}")
            print(f"Pollutants: {station['pollutants']}")
            print("------------------------------")