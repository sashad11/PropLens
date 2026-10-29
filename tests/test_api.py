# PROPLENS - API VALIDATION TESTS

import unittest
import sys
from pathlib import Path

# Allow Python to find our SRC folder.
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "SRC"))

from api_utils import validate_response


class TestAPIValidation(unittest.TestCase):

    def test_correct_data(self):
        # Correct station and pollutant should be accepted.
        data = {
            "RawAQData": {
                "@SiteCode": "GT1",
                "@SpeciesCode": "NO2",
                "Data": [{"@Value": "24.5"}]
            }
        }

        result = validate_response(data, "GT1", "NO2")
        self.assertEqual(len(result), 1)

    def test_wrong_station(self):
        # Wrong station should cause an error.
        data = {
            "RawAQData": {
                "@SiteCode": "CE3",
                "@SpeciesCode": "NO2",
                "Data": []
            }
        }

        with self.assertRaises(ValueError):
            validate_response(data, "GT1", "NO2")

    def test_missing_measurements(self):
        # Missing measurement list should cause an error.
        data = {
            "RawAQData": {
                "@SiteCode": "GT1",
                "@SpeciesCode": "NO2"
            }
        }

        with self.assertRaises(ValueError):
            validate_response(data, "GT1", "NO2")


if __name__ == "__main__":
    unittest.main()