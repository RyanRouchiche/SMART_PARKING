from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_M = 6371000
METERS_PER_DEGREE = 111320


def distance_m(lat1, lng1, lat2, lng2):
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    return round(2 * EARTH_RADIUS_M * asin(sqrt(a)))


def bounding_box(lat, lng, radius_m):
    d_lat = radius_m / METERS_PER_DEGREE
    d_lng = radius_m / (METERS_PER_DEGREE * max(cos(radians(lat)), 0.01))
    return lat - d_lat, lat + d_lat, lng - d_lng, lng + d_lng
