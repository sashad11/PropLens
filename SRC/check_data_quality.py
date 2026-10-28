# PROPLENS - DATA QUALITY REPORT
# Purpose: Check how many hourly pollution readings are available
# for each monitoring station and pollutant.

import duckdb

# Connect to our existing database.
connection = duckdb.connect("Data/proplens.duckdb")

# Use SQL to summarise the measurements.
results = connection.execute("""
    SELECT
        site_code,
        species_code,

        -- Count all stored hourly records.
        COUNT(*) AS total_hours,

        -- Count only records with numerical pollution values.
        COUNT(value) AS valid_hours,

        -- Calculate the percentage containing numerical values.
        ROUND(
            100.0 * COUNT(value) / COUNT(*),
            1
        ) AS completeness_percent

    FROM measurements

    -- Group the measurements by station and pollutant.
    GROUP BY site_code, species_code

    -- Show the least complete combinations first.
    ORDER BY completeness_percent ASC
""").fetchall()

# Display the results.
print("\nPROPLENS - DATA QUALITY REPORT")
print("------------------------------------------")

for row in results:
    # Go through the results for each station and pollutant.

    site_code, species_code, total, valid, completeness = row

    # Classify each combination using its completeness percentage.
    # These are our own project rules, not official LAQN ratings.
    if completeness >= 95:
        status = "GOOD"
    elif completeness >= 80:
        status = "CAUTION"
    else:
        status = "POOR"

    # Print both the completeness percentage and our warning.
    print(
        f"{site_code} | {species_code} | "
        f"{valid}/{total} valid | "
        f"{completeness}% | {status}"
    )