#!/usr/bin/env python

from __future__ import print_function
import cgi
import json
import math
import sqlite3 as sql


class LatLon:
    """Hold a GPS coordinate, in decimal degrees."""
    lat = None
    lon = None
    
    def __init__(self, lat, lon):
        """Instantiated from lat/lon in decimal degrees."""
        self.lat = float(lat)
        self.lon = float(lon)

    def distance_to(self, coord, conversion_units=3443.89849):
        """Calculate the distance from this gps coordinate to another gps coordinate
        using the haversine formula returning the passed in type of conversion units,
        nautical miles by default.
        """
        lon1, lat1, lon2, lat2 = map(math.radians, [self.lon, self.lat, coord.lon, coord.lat])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        nmi = 2 * conversion_units * math.asin(math.sqrt(a))
        return nmi


class Vor:
    """Model for a VOR that is populated from the database."""
    state = None
    call = None
    type_ = None
    frequency = None
    elevation = None
    latitude = None
    longitude = None

    def __init__(self, state, call, type_, frequency, elevation, lat, lon):
        self.state = state
        self.call = call
        self.type_ = type_
        self.frequency = frequency
        self.elevation = elevation
        self.latitude = lat
        self.longitude = lon

    def __str__(self):
        return json.JSONEncoder().encode(self.__dict__)


def get_vors(filters=None):
    """Get a list of all VORs from the database that meet the filters, if present."""
    conn = sql.connect("vors.sqlite3")
    cur = conn.cursor()
    filter_statement = ""
    if filters['state'] is not None:
        filter_statement += " WHERE State=" + filters['state'].upper()
    vors = []
    query = "SELECT State,Call,Type,Frequency,Elevation,Latitude,Longitude from Vors"
    if filter_statement != "":
        query += filter_statement
    with conn:
        cur.execute(query)
        for row in cur.fetchall():
            vors.append(Vor(*row))
    return vors


def rank_vors(base_coord, vorlist):
    """Rank all VORS against the base coordinate returning an ordered list
    based on distance.
    """
    for vor in vorlist:
        vor.distance = base_coord.distance_to(LatLon(vor.lat, vor.lon))
    return sorted(vorlist, key=lambda k: k.distance)


def main():
    fs = cgi.FieldStorage()
    filters = {
        "state" : fs.getfirst('state', None)
    }
    vor_count = fs.getfirst('count', -1)
    lat = fs.getfirst('latitude', None)
    lon = fs.getfirst('longitude', None)
    
    print("Content-Type: application/json\n")
    if lat is None or lon is None:
        print(json.JSONEncoder().encode({"success" : False, "result" : "missing/invalid parameter(s)"}))
        return
    
    base_coord = LatLon(lat, lon)
    vors = rank_vors(base_coord, get_vors(filters))[:vor_count]
    print(json.JSONEncoder().encode({"success" : True, "result" : [str(v) for v in vors]}))


if __name__ == '__main__':
    main()
