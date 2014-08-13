import math


def distance_between(latlon1, latlon2, radius_units=3443.89849):
    '''Use the haversine formula to calculate the
    distance between two GPS points.
    @param: latlon1 - Latitude/Longitude for the
    first point, given in decimal degrees.
    @param: latlon2 - Latitude/Longitude for the
    first point, given in decimal degrees.
    @return: radius_units - Radius of earth in whatever
    unit type you want returned. Default uses nautical miles
    '''
    lat1, lon1 = map(math.radians, latlon1)
    lat2, lon2 = map(math.radians, latlon2)

    d_lon = lon2 - lon1
    d_lat = lat2 - lat1

    a = math.sin(d_lat / 2)**2 + math.cos(lat1) \
        * math.cos(lat2) * math.sin(d_lon / 2)**2

    return 2 * radius_units * math.asin(math.sqrt(a))


def bearing(latlon1, latlon2):
    pass
