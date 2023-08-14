"""
create a markdown template from a Garmin GPX file for route information
"""

import argparse
import math
from datetime import datetime
from typing import Optional

import astral
import astral.sun
import gpxpy
import gpxpy.gpx


NAMESPACE = {
    'trp': 'http://www.garmin.com/xmlschemas/TripExtensions/v1'
}

OUT_HDR = '| Stop |      Lat,Lon       | Description                    | Miles | Gas  | Time  | Layover | Notes'
OUT_SEP = '| ---: | :----------------: | :----------------------------- | ----: | :--: | ----: | ------: | :----'
OUT_FMT = '|   {:02d} | {:-8.4f},{:8.4f} | {:30.30} |       | {:>4} | {:>5} | {:>7} | {}'

KM_TO_MILES = 0.621371
M_TO_FEET = 3.28084


def format_time(time_s: float, seconds: bool) -> str:
    if not time_s:
        return 'n/a'
    if seconds:
        return str(int(time_s))
    minutes = math.floor(time_s / 60.)
    hours = math.floor(minutes / 60.)
    return f'{int(hours):02d}:{int(minutes % 60):02d}:{int(time_s % 60):02d}'

def format_long_length(length: float, miles: bool) -> str:
    if miles:
        return f'{length / 1000. * KM_TO_MILES:.2f}miles'
    return f'{length/ 1000.:.2f}km'

def format_short_length(length: float, miles: bool) -> str:
    if miles:
        return f'{length * M_TO_FEET:.2f}ft'
    return f'{length:.2f}m'

def format_speed(speed: float, miles: bool) -> str:
    if not speed:
        speed = 0
    if miles:
        return f'{speed * KM_TO_MILES * 3600. / 1000.:.2f}mph'
    return f'{speed:.2f}m/s = {speed * 3600. / 1000.:.2f}km/h'

def shaping_point(point) -> bool:
    """ is a garmin route entry just a shaping point? """
    if not point.name:
        return True
    if point.name.startswith('Via '):
        return True
    for extension in point.extensions:
        if 'ShapingPoint' in extension.tag:
            return True
    return False

def layover(point) -> str:
    """ layover time """
    for extension in point.extensions:
        for duration in extension.findall('trp:StopDuration', NAMESPACE):
            return(duration.text.replace('PT', '+').lower())
    return ''

def departure_time(point) -> Optional[datetime]:
    """ returns native datetime object for route points with departure times or None """
    for extension in point.extensions:
        for departure in extension.findall('trp:DepartureTime', NAMESPACE):
            return(datetime.fromisoformat(departure.text.replace('Z', '+00:00')))

def start_point(route) -> tuple[float, float, Optional[datetime]]:
    """ what is the start location of the route, and what's the departure time """
    for point in route.points:
        return(point.latitude, point.longitude, departure_time(point))
    return (0.0, 0.0, None)

def sun_rise_set(route) -> str:
    """ return sunrise/sunset info based upon the route start point """
    lat, lon, start_date = start_point(route)
    start = astral.LocationInfo("Start Point", "", "", lat, lon)
    sun = astral.sun.sun(start.observer, date=start_date)
    return (f'Sunrise: {sun["sunrise"].astimezone():%H:%M}, '
            f'Sunset: {sun["sunset"].astimezone():%H:%M}')

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="input filename")
    args = parser.parse_args()

    with open(args.input, 'r', encoding='UTF-8') as file:
        gpx = gpxpy.parse(file)

    for route in gpx.routes:
        if route.name:
            print(f'# {route.name}')
        if route.description:
            print(f'## {route.description}')
        print(f'- {sun_rise_set(route)}')
        print(f'\n{OUT_HDR}\n{OUT_SEP}')
        stop = 0
        for point in route.points:
            if not shaping_point(point):
                stop += 1
                departure = departure_time(point)
                print(OUT_FMT.format(
                    stop,
                    point.latitude, point.longitude,
                    point.name,
                    'G' if point.symbol and 'Gas Station' in point.symbol or stop == 1 else '',
                    departure.astimezone().strftime('%H:%M') if departure else '',
                    layover(point) or '',
                    point.symbol or ''))

    print()
    move_data = gpx.get_moving_data()
    if move_data and move_data.moving_time:
        print(f'- Total time: {format_time(move_data.moving_time, False)}')
    print(f'- Total length: {format_long_length(gpx.length_2d(), True)}')

main()
