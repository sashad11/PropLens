# Check whether API data matches our request.
import time
import requests

MAX_ATTEMPTS = 3

def validate_response(data, site_code, species_code):

    if not isinstance(data, dict):
        raise ValueError("Response is not a JSON object.")

    raw_data = data.get("RawAQData")

    if not isinstance(raw_data, dict):
        raise ValueError("Missing or invalid RawAQData.")

    if (
        raw_data.get("@SiteCode") != site_code
        or raw_data.get("@SpeciesCode") != species_code
    ):
        raise ValueError("Unexpected station or pollutant.")

    measurements = raw_data.get("Data")

    if not isinstance(measurements, list):
        raise ValueError("Missing or invalid measurement list.")

    if not all(isinstance(item, dict) for item in measurements):
        raise ValueError("Malformed measurement record.")

    return measurements

def download_data(url):
    """
    Retry temporary network/server problems up to three times.
    Return the downloaded JSON if successful.
    """

    for attempt in range(1, MAX_ATTEMPTS + 1):

        try:
            response = requests.get(url, timeout=30)

            # Most 4xx errors indicate a request problem.
            # 429 means rate-limited, so we can retry it.
            if (
                400 <= response.status_code < 500
                and response.status_code != 429
            ):
                response.raise_for_status()

            response.raise_for_status()

            # A successful HTTP response might still contain
            # invalid JSON. The caller will report that failure.
            return response.json()

        except requests.RequestException as error:

            # Do not retry ordinary client errors such as 404.
            status = getattr(
                getattr(error, "response", None),
                "status_code",
                None
            )

            if status is not None and 400 <= status < 500 and status != 429:
                raise

            print(
                f"Attempt {attempt}/{MAX_ATTEMPTS} failed: {error}"
            )

            if attempt == MAX_ATTEMPTS:
                raise

            # Gradually increase the wait between attempts.
            time.sleep(2 * attempt)