
# PROPLENS: PM2.5 BUILDING COMPARISON
#
# PURPOSE:
# Compare historical PM2.5 measurements near six London buildings.
#
# The monitoring stations are selected automatically using
# our station matching report.
#
# IMPORTANT:
# These readings describe pollution at monitoring stations.
# They do not measure exposure inside individual buildings.


# STEP 1: IMPORT THE TOOLS WE NEED

# Read and write CSV files.
import csv

# Find files and folders.
from pathlib import Path

# Query our database.
import duckdb


# STEP 2: FIND OUR PROJECT FILES

# Find the main PropLens folder.
project_folder = Path(__file__).resolve().parents[1]

# Find our DuckDB database.
database_path = project_folder / "Data/proplens.duckdb"

# Find the automatic station matches created earlier.
matches_path = project_folder / "Outputs/station_matches.csv"

# Decide where to save the PM2.5 comparison.
output_path = project_folder / "Outputs/pm25_comparison.csv"

# Make sure the output folder exists.
output_path.parent.mkdir(exist_ok=True)


# STEP 3: LOAD THE AUTOMATIC STATION MATCHES

# Open the CSV containing matches for both pollutants.
with open(matches_path, encoding="utf-8") as file:
    all_matches = list(csv.DictReader(file))

# Keep only PM2.5 matches.
pm25_matches = [
    row for row in all_matches
    if row["pollutant"] == "PM25"
]

# Stop if no PM2.5 matches were found.
if not pm25_matches:
    raise ValueError("No PM2.5 station matches were found.")


# STEP 4: COUNT SHARED MONITORING STATIONS

# More than one building may use the same monitoring station.
# We need to explain this rather than treating the
# measurements as independent building observations.

station_counts = {}

for match in pm25_matches:

    station_code = match["station_code"]

    station_counts[station_code] = (
        station_counts.get(station_code, 0) + 1
    )


# STEP 5: CONNECT TO DUCKDB

connection = duckdb.connect(str(database_path))


# STEP 6: COMPARE THE PM2.5 MEASUREMENTS

# Store the results before exporting them.
report_rows = []

print("\nPROPLENS: PM2.5 BUILDING COMPARISON")
print("----------------------------------")

# Sort buildings alphabetically.
for match in sorted(
    pm25_matches,
    key=lambda row: row["property_name"]
):

    # Read the building and station information.
    name = match["property_name"]
    building_type = match["building_type"]

    station_code = match["station_code"]
    station_name = match["station_name"]
    station_type = match["station_type"]

    distance = float(match["distance_km"])
    distance_status = match["distance_status"]


    # STEP 7: CALCULATE THE POLLUTION AVERAGE

    # Use the same 89-day period as our NO2 report.
    #
    # AVG ignores NULL values.
    # COUNT(value) only counts numerical readings.
    #
    # There are 2136 expected hourly measurements:
    # 89 days multiplied by 24 hours.

    result = connection.execute(
        """
        SELECT
            ROUND(AVG(value), 2) AS average_pm25,

            COUNT(*) AS recorded_hours,

            COUNT(value) AS valid_hours,

            ROUND(
                100.0 * COUNT(value) / 2136,
                1
            ) AS completeness_percent

        FROM measurements

        WHERE site_code = ?
          AND species_code = 'PM25'
          AND measured_at >= '2026-08-01'
          AND measured_at < '2026-10-29'
        """,
        [station_code]
    ).fetchone()

    average, recorded, valid, completeness = result


    # STEP 8: CLASSIFY DATA QUALITY

    # These thresholds are PropLens project rules,
    # not official LAQN quality classifications.

    if completeness >= 95:
        data_quality = "GOOD"

    elif completeness >= 80:
        data_quality = "CAUTION"

    else:
        data_quality = "POOR"


    # STEP 9: CHECK WHETHER THE STATION IS SHARED

    shared_count = station_counts[station_code]

    if shared_count > 1:
        shared_station = "YES"
    else:
        shared_station = "NO"


    # STEP 10: DISPLAY THE COMPARISON

    print(f"\nBuilding: {name}")
    print(f"Building type: {building_type}")
    print(f"Station: {station_name} ({station_code})")
    print(f"Station type: {station_type}")

    print(
        f"Distance: {distance:.2f} km "
        f"({distance_status})"
    )

    if average is not None:
        print(f"Average PM2.5: {average:.2f} ug/m3")
    else:
        print("Average PM2.5: No valid measurements")

    print(f"Completeness: {completeness}%")
    print(f"Valid readings: {valid}/{recorded}")
    print(f"Data quality: {data_quality}")

    # Explain when multiple buildings share data.
    if shared_station == "YES":
        print(
            f"Note: This station is shared by "
            f"{shared_count} buildings."
        )

    # Flag stations located relatively far away.
    if distance_status == "DISTANT":
        print(
            "Warning: Monitoring station is over 3 km away."
        )


    # STEP 11: PREPARE A ROW FOR THE CSV

    report_rows.append({
        "property_name": name,
        "building_type": building_type,
        "station_code": station_code,
        "station_name": station_name,
        "station_type": station_type,
        "distance_km": distance,
        "distance_status": distance_status,
        "average_pm25_ug_m3": average,
        "recorded_hours": recorded,
        "valid_hours": valid,
        "completeness_percent": completeness,
        "data_quality": data_quality,
        "shared_station": shared_station
    })


# STEP 12: SAVE THE COMPARISON REPORT

# Keep the same column structure as our NO2 report,
# apart from the pollutant concentration column.

columns = [
    "property_name",
    "building_type",
    "station_code",
    "station_name",
    "station_type",
    "distance_km",
    "distance_status",
    "average_pm25_ug_m3",
    "recorded_hours",
    "valid_hours",
    "completeness_percent",
    "data_quality",
    "shared_station"
]

with open(
    output_path,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(file, fieldnames=columns)

    writer.writeheader()
    writer.writerows(report_rows)


# STEP 13: CLOSE THE DATABASE

connection.close()

print("\nPM2.5 comparison completed successfully.")
print(f"Buildings compared: {len(report_rows)}")
print("Saved to Outputs/pm25_comparison.csv")
