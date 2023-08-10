# TODO calculate miles and time properly (doesn't seem to be in GPX file information)

import argparse
import gpxpy
import gpxpy.gpx
from pprint import pprint

parser = argparse.ArgumentParser()
parser.add_argument("input", help="input filename")
parser.add_argument("-m", "--markdown", action="store_true",
                    help="output markdown table")
args = parser.parse_args()

def shapingpoint(point):
    for extension in point.extensions:
        if 'ShapingPoint' in extension.tag:
            return True
    return False

gpx_file = open(args.input, 'r')
gpx = gpxpy.parse(gpx_file)

outfmt = '{:02d} {:8.4f},{:8.4f}\t{:30.30}\t{}\t{}\t{}'
if args.markdown:
    outhdr = '| Stop |      Lat,Lon       | Description                    | Miles | Gas  | Time  | Notes'
    outsep = '| ---: | :----------------: | :----------------------------- | ----: | :--: | ----: | :----'
    outfmt = '|   {:02d} | {:-8.4f},{:8.4f} | {:30.30} |       | {:4} | {:5} | {}'

for route in gpx.routes:
    print('{}\n{}'.format(outhdr, outsep))
    stop = 0
    for point in route.points:
        if not shapingpoint(point):
            gas = 'G' if 'Gas Station' in point.symbol or stop == 0 else ''
            print(outfmt.format(
                stop,
                point.latitude, point.longitude,
                point.name,
                gas,
                point.time.strftime('%H:%M'),
                point.symbol))
            stop = stop + 1
