
# PROPLENS - STATION DATA QUALITY REPORT
#
# Summarise the quantity and completeness of
# measurements for each station and pollutant.

from pathlib import Path
import duckdb

# Make sure the output folder exists.
Path("Outputs").mkdir(exist_ok=True)

# Connect to our existing database.
connection = duckdb.connect("Data/proplens.duckdb")

# Create a report covering our 89-day analysis period.
connection.execute("""
    COPY (
        SELECT
            site_code,
            species_code,

            COUNT(*) AS recorded_hours,

            COUNT(value) AS valid_hours,

            COUNT(*) - COUNT(value) AS null_readings,

            ROUND(
                100.0 * COUNT(value) / 2136,
                1
            ) AS completeness_pct,

            CASE
                WHEN COUNT(*) >= 2000
                     AND COUNT(value) * 100.0 / 2136 >= 90
                THEN 'SUITABLE'

                ELSE 'REVIEW'
            END AS coverage_status

        FROM measurements

        WHERE measured_at >= '2026-08-01'
          AND measured_at < '2026-10-29'

        GROUP BY site_code, species_code
        ORDER BY species_code, site_code
    )
    TO 'Outputs/station_quality.csv'
    (HEADER, DELIMITER ',')
""")

connection.close()

print("Station quality report saved!")
print("File: Outputs/station_quality.csv")
