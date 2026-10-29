
# PROPLENS - AUTOMATED DISTANCE TESTS
#
# Tests the real Haversine function used by PropLens.

import unittest
import sys
from pathlib import Path

# Make the SRC folder available to this test.
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "SRC"))

# Import the SAME function that match_properties.py uses.
from geo_utils import distance_km


class TestDistanceCalculation(unittest.TestCase):

    def test_same_location(self):
        # A point is zero kilometres from itself.
        result = distance_km(51.5, -0.1, 51.5, -0.1)
        self.assertAlmostEqual(result, 0, places=5)

    def test_distance_is_symmetric(self):
        # A -> B should be the same distance as B -> A.
        forward = distance_km(51.5, -0.1, 51.6, -0.2)
        backward = distance_km(51.6, -0.2, 51.5, -0.1)

        self.assertAlmostEqual(forward, backward, places=5)

    def test_distance_is_positive(self):
        # Two different locations should have a positive distance.
        result = distance_km(51.5, -0.1, 51.6, -0.2)
        self.assertGreater(result, 0)


if __name__ == "__main__":
    unittest.main()
