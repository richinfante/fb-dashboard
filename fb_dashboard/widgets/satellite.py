# https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle
import requests
from io import BytesIO
from PIL import Image, ImageOps, ImageDraw, ImageFont
from ..util import eval_expr, parse_color
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from .base import WidgetBase
import os
from datetime import datetime as dt, timedelta

from skyfield.api import load
from skyfield.iokit import parse_tle_file
from skyfield.api import wgs84
from hashlib import sha256
import json



class SatelliteWidget(WidgetBase):

    def latlon_to_xy(self, lat, lon):
        # print(lat, lon)
        return (
            int((lon + 180) * self.width / 360),
            int((90 - lat) * self.height / 180),
        )

    def __init__(self, x, y, width, height, config):
        super().__init__(x, y, width, height, config)
        self.tle_url = config["tle_url"]

        satellite_filter = config.get("satellite_filter", None)
        if satellite_filter:
            self.satellite_filter = satellite_filter.split(",")
        else:
            self.satellite_filter = []

        self.bg_color = parse_color(config.get('bg_color', '#000000'))
        self.map_color = parse_color(config.get('map_color', '#999999'))
        self.track_color = parse_color(config.get('track_color', '#00b400'))
        self.satellite_color = parse_color(config.get('satellite_color', '#00ff00'))
        self.pin_radius = eval_expr(config.get('pin_radius', '2'), {'w': width, 'h': height})

        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, "./data/world.geo.json")
        self.refresh_interval = 5
        self.last_tle_refresh = None

        geojson = open(filename, "r")
        geo_data = json.loads(geojson.read())
        geojson.close()

        self.geo_data = geo_data

        self.bg_image = Image.new("RGB", (width, height), color=self.bg_color)
        draw = ImageDraw.Draw(self.bg_image)

        # draw the geojson data
        for feature in geo_data["features"]:
            coords = feature["geometry"]["coordinates"]
            if feature["geometry"]["type"] == "Polygon":
                for feat in coords:
                    to_draw = []
                    for coord in feat:
                        to_draw.append(self.latlon_to_xy(coord[1], coord[0]))

                    draw.polygon(to_draw, outline=self.map_color)
            elif feature["geometry"]["type"] == "MultiPolygon":
                for feat in coords:
                    to_draw = []
                    for coord in feat:
                        for c in coord:
                            to_draw.append(self.latlon_to_xy(c[1], c[0]))

                    draw.polygon(to_draw, outline=self.map_color)

    def refresh(self):
        if not self.last_tle_refresh or dt.now() - self.last_tle_refresh > timedelta(
            hours=1
        ):
            print("refreshing TLE")
            self.refresh_tle()
            self.last_tle_refresh = dt.now()
        self.render()
        super().refresh()

    def refresh_tle(self):
        ts = load.timescale()
        url_hash = str(sha256(self.tle_url.encode()).hexdigest())

        dirname = os.path.dirname(__file__)
        pathname = os.path.join(dirname, "data", f"{url_hash}.tle")

        if not self.last_tle_refresh:
            print("loading TLE from", self.tle_url)
            print("caching in", url_hash)

        if not load.exists(pathname) or load.days_old(pathname) > 1:
            print("TLE is stale, downloading new data")
            load.download(self.tle_url, pathname)

        tle_file = open(pathname, "rb")
        self.satellites = list(parse_tle_file(tle_file, ts))

    def render(self):
        ts = load.timescale()

        new_image = self.bg_image.copy()
        draw = ImageDraw.Draw(new_image)

        print("Loaded", len(self.satellites), "satellites")

        for satellite in self.satellites:
            if self.satellite_filter and satellite.name not in self.satellite_filter:
                continue

            geocentric = satellite.at(ts.now())
            lat, lon = wgs84.latlon_of(geocentric)
            hr_track = []
            for i in range(0, 60):
                g_pos = satellite.at(
                    ts.now() - timedelta(minutes=30) + timedelta(minutes=i)
                )
                clat, clon = wgs84.latlon_of(g_pos)
                screen_coord = self.latlon_to_xy(clat.degrees, clon.degrees)
                hr_track.append(screen_coord)

            # find the differences between each point in the track
            dx_track = []
            dy_track = []
            for i in range(1, len(hr_track)):
                dx_track.append(abs(hr_track[i][0] - hr_track[i - 1][0]))
                dy_track.append(abs(hr_track[i][1] - hr_track[i - 1][1]))

            # find the median of the differences
            median_dx = sorted(dx_track)[len(dx_track) // 2]
            median_dy = sorted(dy_track)[len(dy_track) // 2]

            out_tracks = []
            cur_track = []
            for (i, coord) in enumerate(hr_track):
                cur_track.append(coord)

                if i == len(hr_track) - 1:
                    pass  # last coord is always added

                # if the difference between the current point and the previous point is > 4* the median, split the track
                elif dx_track[i] > median_dx * 4 or dy_track[i] > median_dy * 4:
                    out_tracks.append(cur_track)
                    cur_track = []

            out_tracks.append(cur_track)

            for track in out_tracks:
                if len(track) > 1:
                    draw.line(track, fill=self.track_color)

            x, y = self.latlon_to_xy(lat.degrees, lon.degrees)
            draw.ellipse((x - self.pin_radius, y - self.pin_radius, x + self.pin_radius, y + self.pin_radius), fill=self.satellite_color)
            # font = ImageFont.load_default(8)
            # draw.text((x, y), satellite.name, fill=(255, 255, 255), font=font)

        # ensure the image has an alpha channel
        if not new_image.has_transparency_data:
            # https://stackoverflow.com/a/46366964
            a_channel = Image.new(
                "L", new_image.size, 255
            )  # 'L' 8-bit pixels, black and white
            new_image.putalpha(a_channel)

        # convert to BGRA format
        self.bytes = new_image.tobytes("raw", "BGRA")
        self.bytes_per_pixel = 4

    def write_into_fb(self, fb):
        """
        Write the image into the framebuffer
        """
        if not self.has_refreshed:
            return

        for y in range(self.height):
            y_off = y * self.width * self.bytes_per_pixel
            fb.write_line(
                self.x,
                self.y + y,
                self.bytes[y_off : y_off + self.width * self.bytes_per_pixel],
            )
