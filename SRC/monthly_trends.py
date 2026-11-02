# PROPLENS MONTHLY NITROGEN DIOXIDE REPORT
#
# PURPOSE
# Aggregate hourly NO2 readings into monthly averages for each building's
# selected station. The building-to-station matches come from the AUTOMATIC
# match report, rather than the older manual matching file.
#
# HOW THE QUERY WORKS
# The JOIN pairs each building with measurements from its chosen station.
# The date filters use the shared reporting window; the upper bound is
# exclusive. AVG ignores NULL readings and COUNT(value) counts valid ones.
# A station matched to several buildings can therefore appear several times
# in this building-oriented report. Those rows are NOT independent monitors.
# The dashboard removes repeated station-month combinations for its chart.

# PROPLENS MONTHLY NO2 TRENDS
# Use automatic station matches and the same reporting period as other reports.

from pathlib import Path
import duckdb
from reporting_window import read_window

project = Path(__file__).resolve().parents[1]
window = read_window()
con = duckdb.connect(str(project / "Data/proplens.duckdb"))
output = project / "Outputs/monthly_trends.csv"
matches = project / "Outputs/station_matches.csv"

con.execute("""
    COPY (
        SELECT
            p.property_name,
            p.building_type,
            p.station_code,
            STRFTIME(m.measured_at, '%Y-%m') AS month,
            ROUND(AVG(m.value), 2) AS average_no2,
            COUNT(m.value) AS valid_readings,
            COUNT(*) AS total_readings
        FROM read_csv_auto(?) AS p
        JOIN measurements AS m
          ON p.station_code = m.site_code
         AND m.species_code = 'NO2'
        WHERE p.pollutant = 'NO2'
          AND m.measured_at >= ?
          AND m.measured_at < ?
        GROUP BY p.property_name, p.building_type, p.station_code, month
        ORDER BY p.property_name, month
    ) TO ? (HEADER, DELIMITER ',')
""", [str(matches), window['start_date'], window['end_exclusive'], str(output)])
con.close()
print(f"Monthly NO2 trends saved: {output}")
