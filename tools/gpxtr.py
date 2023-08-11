"""
gpxtr - create a markdown template from a Garmin GPX file for
        route information
"""

import argparse
from datetime import datetime

import gpxpy
import gpxpy.gpx
from astral import LocationInfo
from astral.sun import sun

NAMESPACE = {
    'trp': 'http://www.garmin.com/xmlschemas/TripExtensions/v1'
}

OUTHDR = '| Stop |      Lat,Lon       | Description                    | Miles | Gas  | Time  | Layover | Notes'
OUTSEP = '| ---: | :----------------: | :----------------------------- | ----: | :--: | ----: | ------: | :----'
OUTFMT = '|   {:02d} | {:-8.4f},{:8.4f} | {:30.30} |       | {:>4} | {:>5} | {:>7} | {}'


def shaping_point(pt):
    """ is a garmin route entry just a shaping point? """
    for extension in pt.extensions:
        if 'ShapingPoint' in extension.tag:
            return True
    return False

def layover(pt):
    """ layover time """
    for extension in pt.extensions:
        for duration in extension.findall('trp:StopDuration', NAMESPACE):
            return(duration.text.replace('PT', '+').lower())

def departure_time(pt):
    """ returns native datetime object for route points with departure times or None """
    for extension in pt.extensions:
        for departure in extension.findall('trp:DepartureTime', NAMESPACE):
            return(datetime.fromisoformat(departure.text.replace('Z', '+00:00')))

def start_point(rte):
    """ what is the start location of the route, and what's the departure time """
    for pt in rte.points:
        return(pt.latitude, pt.longitude, departure_time(pt))

def sun_rise_set(rte):
    """ return sunrise/sunset info based upon the route startpoing """
    lat, lon, startdate = start_point(rte)
    start = LocationInfo("Start Point", "", "", lat, lon)
    s = sun(start.observer, date=startdate)
    return f'Sunrise: {s["sunrise"].astimezone():%H:%M}, Sunset: {s["sunset"].astimezone():%H:%M}'

parser = argparse.ArgumentParser()
parser.add_argument("input", help="input filename")
args = parser.parse_args()

with open(args.input, 'r', encoding='UTF-8') as file:
    gpxdata = gpxpy.parse(file)

for route in gpxdata.routes:
    print('{}\n{}'.format(OUTHDR, OUTSEP))
    stop = 0
    for point in route.points:
        if not shaping_point(point):
            stop += 1
            dt = departure_time(point)
            print(OUTFMT.format(
                stop,
                point.latitude, point.longitude,
                point.name,
                'G' if 'Gas Station' in point.symbol or stop == 1 else '',
                dt.astimezone().strftime('%H:%M') if dt else '',
                layover(point) or '',
                point.symbol))
    print("\n", sun_rise_set(route))
