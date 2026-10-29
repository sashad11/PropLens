
# PROPLENS - MISSING HOURLY MEASUREMENT CHECK
#
# Purpose:
# Check whether hourly timestamps are completely missing,
# rather than only checking for NULL measurement values.

import duckdb


# STEP 1: CONNECT TO OUR DATABASE

connection = duckdb.connect("Data/proplens.duckdb")


# STEP 2: IDENTIFY EXPECTED AND ACTUAL MEASUREMENTS

# Generate each expected hourly timestamp between
# 1 August and 29 October (exclusive).
#
# This covers 89 complete calendar days:
# 1 August to 28 October 2026.

results = connection.execute("""
    WITH expected_hours AS (
        SELECT timestamp
        FROM generate_series(
            TIMESTAMP '2026-08-01 00:00:00',
            TIMESTAMP '2026-10-28 23:00:00',
            INTERVAL '1 hour'
        ) AS t(timestamp)
    ),

    -- Select station-pollutant combinations with
    -- historical data across our analysis period.
    station_targets AS (
        SELECT DISTINCT site_code, species_code
        FROM measurements
        WHERE measured_at >= '2026-08-01'
          AND measured_at < '2026-10-29'
        GROUP BY site_code, species_code
        HAVING COUNT(DISTINCT CAST(measured_at AS DATE)) >= 80
    ),

    -- Create every expected station-pollutant-hour combination.
    expected_measurements AS (
        SELECT
            s.site_code,
            s.species_code,
            h.timestamp
        FROM station_targets s
        CROSS JOIN expected_hours h
    )

    SELECT
        e.site_code,
        e.species_code,

        COUNT(*) AS expected_hours,

        -- Count timestamps actually present in DuckDB.
        COUNT(m.measured_at) AS recorded_hours,

        -- Count timestamps with numerical measurements.
        COUNT(m.value) AS valid_hours,

        -- Expected hours without any corresponding record.
        COUNT(*) - COUNT(m.measured_at) AS missing_timestamps,

        -- Recorded hours where the value is NULL.
        COUNT(m.measured_at) - COUNT(m.value) AS null_readings,

        -- Percentage of expected hours with a valid value.
        ROUND(
            100.0 * COUNT(m.value) / COUNT(*),
            1
        ) AS overall_completeness

    FROM expected_measurements e

    LEFT JOIN measurements m
        ON e.site_code = m.site_code
        AND e.species_code = m.species_code
        AND e.timestamp = m.measured_at

    GROUP BY e.site_code, e.species_code

    ORDER BY e.site_code, e.species_code
""").fetchall()


# STEP 3: DISPLAY DATA-QUALITY RESULTS

print("\nPROPLENS - MISSING HOURLY DATA REPORT")
print("-------------------------------------")

for row in results:

    (
        station,
        pollutant,
        expected,
        recorded,
        valid,
        missing,
        nulls,
        completeness
    ) = row

    print(
        f"{station} | {pollutant} | "
        f"Expected: {expected} | "
        f"Recorded: {recorded} | "
        f"Valid: {valid} | "
        f"Missing timestamps: {missing} | "
        f"NULL values: {nulls} | "
        f"Complete: {completeness}%"
    )


# STEP 4: CLOSE THE DATABASE

connection.close()

print("\nMissing-hour validation completed.")
