
# PROPLENS - MONTHLY PM2.5 TRENDS
#
# Purpose:
# Calculate average PM2.5 concentrations by month.
# Only include monitoring stations used in our building analysis.
#
# Note:
# These are station measurements, not personal exposure estimates.


# STEP 1: IMPORT LIBRARIES

import csv
from pathlib import Path
import duckdb


# STEP 2: CONNECT TO OUR DUCKDB DATABASE

connection = duckdb.connect("Data/proplens.duckdb")


# STEP 3: CALCULATE MONTHLY PM2.5 AVERAGES

# Group measurements by station and calendar month.
# This avoids treating multiple buildings sharing CE3
# as separate air quality measurements.

results = connection.execute("""
    SELECT
        site_code,
        STRFTIME(measured_at, '%Y-%m') AS month,

        -- Average of numerical PM2.5 readings.
        ROUND(AVG(value), 2) AS average_pm25,

        -- Number of hourly records with numerical values.
        COUNT(value) AS valid_hours,

        -- Total number of stored hourly records.
        COUNT(*) AS recorded_hours

    FROM measurements

    WHERE species_code = 'PM25'
      AND site_code IN ('GT1', 'CE3', 'BT8')

    GROUP BY
        site_code,
        STRFTIME(measured_at, '%Y-%m')

    ORDER BY
        site_code,
        month
""").fetchall()


# STEP 4: SAVE THE MONTHLY TRENDS

# Ensure the folder exists before creating the CSV.
Path("Outputs").mkdir(exist_ok=True)

output_file = "Outputs/monthly_pm25.csv"

columns = [
    "station_code",
    "month",
    "average_pm25_ug_m3",
    "valid_hours",
    "recorded_hours"
]

with open(output_file, "w", newline="", encoding="utf-8") as file:

    writer = csv.writer(file)
    writer.writerow(columns)
    writer.writerows(results)


# STEP 5: DISPLAY A PREVIEW

print("\nPROPLENS - MONTHLY PM2.5 TRENDS")
print("--------------------------------")

for row in results:
    station, month, average, valid, recorded = row

    print(
        f"{station} | {month} | "
        f"{average} ug/m3 | "
        f"{valid}/{recorded} valid hours"
    )


# STEP 6: CLOSE DATABASE CONNECTION

connection.close()

print(f"\nMonthly PM2.5 trends saved to {output_file}")
