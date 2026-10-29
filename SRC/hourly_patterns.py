
# PROPLENS - HOURLY POLLUTION PATTERNS
#
# Compare average pollution levels by hour of day
# and between weekdays and weekends.
#
# Use monitoring stations only once, even when
# multiple buildings are matched to the same station.

from pathlib import Path
import duckdb

# STEP 1: SET UP FILE PATHS

project_folder = Path(__file__).resolve().parents[1]

database_path = project_folder / "Data/proplens.duckdb"
quality_path = project_folder / "Outputs/station_quality.csv"
output_path = project_folder / "Outputs/hourly_patterns.csv"

output_path.parent.mkdir(exist_ok=True)

# STEP 2: CONNECT TO THE DATABASE

connection = duckdb.connect(str(database_path))

# STEP 3: ANALYSE HOURLY MEASUREMENTS

# Read our station-quality report, then include
# only station-pollutant combinations that passed
# our historical-data screening.
#
# GROUP BY hour and day_type allows us to see
# whether pollution changes during the day.

connection.execute("""
    COPY (
        WITH eligible_stations AS (
            SELECT
                site_code,
                species_code
            FROM read_csv_auto(?)
            WHERE coverage_status = 'SUITABLE'
        )

        SELECT
            m.site_code,
            m.species_code,

            CASE
                WHEN EXTRACT(DOW FROM m.measured_at) IN (0, 6)
                THEN 'Weekend'
                ELSE 'Weekday'
            END AS day_type,

            EXTRACT(HOUR FROM m.measured_at) AS hour_of_day,

            COUNT(*) AS recorded_hours,
            COUNT(m.value) AS valid_readings,

            ROUND(AVG(m.value), 2) AS average_concentration

        FROM measurements m

        INNER JOIN eligible_stations s
            ON m.site_code = s.site_code
            AND m.species_code = s.species_code

        WHERE m.measured_at >= '2026-08-01'
          AND m.measured_at < '2026-10-29'

        GROUP BY
            m.site_code,
            m.species_code,
            day_type,
            hour_of_day

        ORDER BY
            m.species_code,
            m.site_code,
            day_type,
            hour_of_day
    )
    TO ?
    (HEADER, DELIMITER ',')
""", [str(quality_path), str(output_path)])

connection.close()

print("Hourly pollution analysis completed!")
print("Saved to Outputs/hourly_patterns.csv")
