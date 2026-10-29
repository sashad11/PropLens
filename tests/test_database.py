
# PROPLENS - DATABASE TESTS
#
# Test that the same hourly measurement cannot be
# inserted twice into our measurements table.

import unittest
import duckdb


class TestDatabase(unittest.TestCase):

    def test_duplicate_measurement_is_not_inserted(self):

        # Use a temporary database held in memory.
        # It disappears when the test finishes.
        connection = duckdb.connect(":memory:")

        # Create a simplified copy of our measurements table.
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

        # Insert one example NO2 measurement.
        insert_sql = """
            INSERT INTO measurements
            VALUES ('GT1', 'NO2', '2026-08-01 12:00:00', 24.5)
            ON CONFLICT DO NOTHING
        """

        connection.execute(insert_sql)

        # Attempt to insert exactly the same measurement again.
        connection.execute(insert_sql)

        # Count how many records exist.
        result = connection.execute("""
            SELECT COUNT(*) FROM measurements
        """).fetchone()[0]

        # We expect only one record, not two.
        self.assertEqual(result, 1)

        connection.close()


if __name__ == "__main__":
    unittest.main()
