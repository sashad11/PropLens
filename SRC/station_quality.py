# PROPLENS HISTORICAL STATION QUALITY
#
# WHY WE CHECK QUALITY
# A row for 10:00 may exist even if its pollution value is NULL. Counting
# all rows would make that hour look like a successful measurement.
# This report therefore counts both stored records and valid numbers.
#
# EXPECTED HOURS
# The common reporting window tells us how many hourly timestamps SHOULD
# exist from its start through its last included day. Dividing valid readings
# by expected hours also penalises completely missing timestamps.
#
# SUITABILITY RULE
# A station/pollutant pair must have at least 90 percent timestamp coverage
# AND at least 90 percent valid readings for the chosen period. Otherwise it
# is marked REVIEW and is not eligible for automatic station matching.
# This 90 percent threshold is our project choice, not an LAQN rating.


# PROPLENS - STATION DATA QUALITY REPORT
#
# Summarise the quantity and completeness of
# measurements for each station and pollutant.

from pathlib import Path
import duckdb
from reporting_window import read_window

window = read_window()

# Make sure the output folder exists.
Path("Outputs").mkdir(exist_ok=True)

# Connect to our existing database.
connection = duckdb.connect("Data/proplens.duckdb")

# Create a report using the current shared reporting period.
connection.execute("""
    COPY (
        SELECT
            site_code,
            species_code,

            COUNT(*) AS recorded_hours,

            COUNT(value) AS valid_hours,

            COUNT(*) - COUNT(value) AS null_readings,

            ROUND(
                100.0 * COUNT(value) / ?,
                1
            ) AS completeness_pct,

            CASE
                WHEN COUNT(*) * 100.0 / ? >= 90
                     AND COUNT(value) * 100.0 / ? >= 90
                THEN 'SUITABLE'

                ELSE 'REVIEW'
            END AS coverage_status

        FROM measurements

        WHERE measured_at >= ?
          AND measured_at < ?

        GROUP BY site_code, species_code
        ORDER BY species_code, site_code
    )
    TO 'Outputs/station_quality.csv'
    (HEADER, DELIMITER ',')
""", [window["expected_hours"], window["expected_hours"], window["expected_hours"], window["start_date"], window["end_exclusive"]])

connection.close()

print("Station quality report saved!")
print("File: Outputs/station_quality.csv")
