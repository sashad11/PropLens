
# PROPLENS - GEOGRAPHICAL UTILITIES
#
# Shared calculations used by our property-matching scripts.

from math import radians, sin, cos, sqrt, atan2


def distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate the approximate straight-line distance between
    two locations using latitude and longitude.

    Returns the distance in kilometres.
    """

    # Approximate radius of Earth in kilometres.
    earth_radius = 6371

    # Convert degrees to radians.
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # Find the difference between the coordinates.
    latitude_difference = lat2 - lat1
    longitude_difference = lon2 - lon1

    # Apply the Haversine formula.
    a = (
        sin(latitude_difference / 2) ** 2
        + cos(lat1) * cos(lat2)
        * sin(longitude_difference / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c
