
# PROPLENS - MONTHLY AIR QUALITY TRENDS
#
# Purpose:
# Calculate the average NO2 concentration for each building
# in each month, using its matched monitoring station.

import csv
from pathlib import Path
import duckdb


# STEP 1: CONNECT TO OUR EXISTING DATABASE

connection = duckdb.connect("Data/proplens.duckdb")


# STEP 2: CALCULATE MONTHLY AVERAGES

# Match each building with its station's NO2 measurements.
# Group the readings by building and calendar month.
results = connection.execute("""
    SELECT
        p.property_name,
        p.building_type,
        p.station_code,
        STRFTIME(m.measured_at, '%Y-%m') AS month,

        ROUND(AVG(m.value), 2) AS average_no2,

        COUNT(m.value) AS valid_readings,
        COUNT(*) AS total_readings

    FROM read_csv_auto('Data/property_matches.csv') AS p

    JOIN measurements AS m
        ON p.station_code = m.site_code

    WHERE m.species_code = 'NO2'

    GROUP BY
        p.property_name,
        p.building_type,
        p.station_code,
        STRFTIME(m.measured_at, '%Y-%m')

    ORDER BY
        p.property_name,
        month
""").fetchall()


# STEP 3: CREATE THE OUTPUT FOLDER

# Make sure the folder exists before saving the report.
Path("Outputs").mkdir(exist_ok=True)


# STEP 4: SAVE THE MONTHLY RESULTS TO CSV

output_file = "Outputs/monthly_trends.csv"

columns = [
    "property_name",
    "building_type",
    "station_code",
    "month",
    "average_no2",
    "valid_readings",
    "total_readings"
]

with open(output_file, "w", newline="", encoding="utf-8") as file:

    writer = csv.writer(file)

    # Write column headings.
    writer.writerow(columns)

    # Write each monthly result.
    writer.writerows(results)


# STEP 5: DISPLAY A PREVIEW

print("\nPROPLENS - MONTHLY NO2 TRENDS")
print("-----------------------------")

for row in results:
    print(
        f"{row[0]} | {row[3]} | "
        f"{row[4]} µg/m³ | "
        f"{row[5]}/{row[6]} valid readings"
    )


# STEP 6: CLOSE THE DATABASE CONNECTION

connection.close()

print(f"\nMonthly trends saved to {output_file}")
