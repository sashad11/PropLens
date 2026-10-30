
# PROPLENS API TESTS

import unittest
import sys
import requests

from pathlib import Path
from unittest.mock import patch, Mock

# Allow Python to find our SRC folder.
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "SRC"))

from api_utils import validate_response, download_data


class TestAPIValidation(unittest.TestCase):

    def test_correct_data(self):
        # Correct API data should be accepted.
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
        # Data from the wrong station should be rejected.
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
        # A response without measurements should be rejected.
        data = {
            "RawAQData": {
                "@SiteCode": "GT1",
                "@SpeciesCode": "NO2"
            }
        }

        with self.assertRaises(ValueError):
            validate_response(data, "GT1", "NO2")

    def test_retry_after_temporary_failure(self):
        # Pretend the API succeeds on the third attempt.
        successful_response = Mock()
        successful_response.status_code = 200
        successful_response.json.return_value = {
            "status": "success"
        }

        # Simulate two timeouts followed by success.
        with patch(
            "api_utils.requests.get",
            side_effect=[
                requests.exceptions.Timeout("Temporary timeout"),
                requests.exceptions.Timeout("Temporary timeout"),
                successful_response
            ]
        ) as mock_get:

            # Skip the waiting time during the test.
            with patch("api_utils.time.sleep"):
                result = download_data("https://example.com/test")

        # Confirm the response was returned.
        self.assertEqual(result, {"status": "success"})

        # Confirm Python tried exactly three times.
        self.assertEqual(mock_get.call_count, 3)


if __name__ == "__main__":
    unittest.main()
