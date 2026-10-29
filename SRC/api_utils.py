# Check whether API data matches our request.

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