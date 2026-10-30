
# PROPLENS DATABASE TESTS
#
# Check that DuckDB prevents duplicate measurements
# and updates existing readings when LAQN corrects them.

import unittest
import duckdb


class TestDatabase(unittest.TestCase):

    def test_duplicate_measurement_is_not_inserted(self):
        # Create a temporary database.
        connection = duckdb.connect(":memory:")

        # Create our test measurements table.
        connection.execute("""
            CREATE TABLE measurements (
                site_code VARCHAR,
                species_code VARCHAR,
                measured_at TIMESTAMP,
                value DOUBLE,
                PRIMARY KEY (
                    site_code,
                    species_code,
                    measured_at
                )
            )
        """)

        # Insert the same measurement twice.
        insert_sql = """
            INSERT INTO measurements
            VALUES ('GT1', 'NO2', '2026-08-01 12:00:00', 24.5)
            ON CONFLICT DO NOTHING
        """

        connection.execute(insert_sql)
        connection.execute(insert_sql)

        # Only one measurement should exist.
        row_count = connection.execute(
            "SELECT COUNT(*) FROM measurements"
        ).fetchone()[0]

        self.assertEqual(row_count, 1)

        connection.close()

    def test_corrected_measurement_updates(self):
        # Create a separate temporary database.
        connection = duckdb.connect(":memory:")

        # Create our test measurements table.
        connection.execute("""
            CREATE TABLE measurements (
                site_code VARCHAR,
                species_code VARCHAR,
                measured_at TIMESTAMP,
                value DOUBLE,
                PRIMARY KEY (
                    site_code,
                    species_code,
                    measured_at
                )
            )
        """)

        # Save the original measurement.
        connection.execute("""
            INSERT INTO measurements
            VALUES ('GT1', 'NO2', '2026-10-27 12:00:00', 24.5)
        """)

        # Simulate LAQN correcting the reading.
        connection.execute("""
            INSERT INTO measurements
            VALUES ('GT1', 'NO2', '2026-10-27 12:00:00', 23.8)

            ON CONFLICT (
                site_code,
                species_code,
                measured_at
            )

            DO UPDATE SET
                value = EXCLUDED.value

            WHERE measurements.value
                  IS DISTINCT FROM EXCLUDED.value
        """)

        # Check that the corrected value was stored.
        result = connection.execute(
            "SELECT value FROM measurements"
        ).fetchone()[0]

        self.assertAlmostEqual(result, 23.8)

        # Check that no duplicate measurement was created.
        row_count = connection.execute(
            "SELECT COUNT(*) FROM measurements"
        ).fetchone()[0]

        self.assertEqual(row_count, 1)

        connection.close()


if __name__ == "__main__":
    unittest.main()
