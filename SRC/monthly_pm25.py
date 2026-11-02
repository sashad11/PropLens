# PROPLENS MONTHLY FINE PARTICLE REPORT
#
# PURPOSE
# Calculate the monthly PM2.5 average for each station used in the current
# building matching report. Unlike the NO2 building report, this output is
# station-oriented and includes each monitoring station only once per month.
#
# The query filters to stations matched for PM25, then groups hourly
# measurements by station and calendar month within the common date window.
# AVG ignores missing (NULL) values. COUNT(value) counts valid measurements,
# whereas COUNT(*) counts stored hourly records, including NULL readings.

# PROPLENS MONTHLY PM2.5 TRENDS
# Include only stations matched to buildings for PM2.5, once each.

from pathlib import Path
import duckdb
from reporting_window import read_window

project = Path(__file__).resolve().parents[1]
window = read_window()
con = duckdb.connect(str(project / "Data/proplens.duckdb"))
output = project / "Outputs/monthly_pm25.csv"
matches = project / "Outputs/station_matches.csv"
con.execute("""
    COPY (
        SELECT
            m.site_code,
            STRFTIME(m.measured_at, '%Y-%m') AS month,
            ROUND(AVG(m.value), 2) AS average_pm25_ug_m3,
            COUNT(m.value) AS valid_hours,
            COUNT(*) AS recorded_hours
        FROM measurements m
        WHERE m.species_code = 'PM25'
          AND m.site_code IN (
            SELECT DISTINCT station_code
            FROM read_csv_auto(?)
            WHERE pollutant = 'PM25'
          )
          AND m.measured_at >= ?
          AND m.measured_at < ?
        GROUP BY m.site_code, month
        ORDER BY m.site_code, month
    ) TO ? (HEADER, DELIMITER ',')
""", [str(matches), window['start_date'], window['end_exclusive'], str(output)])
con.close()
print(f"Monthly PM2.5 trends saved: {output}")
