from PIL import Image, ImageDraw, ImageFont, ImageOps
from .base import WidgetBase
from ..util import eval_expr, parse_color
from datetime import datetime as dt
import requests
from io import BytesIO
from ..sfxbox import SimpleFlexBox

def get_keypath(obj, keypath):
    keys = keypath.split(".")
    for key in keys:
        obj = obj[key]
    return obj

class WeatherWidget(WidgetBase):
    def __init__(self, x, y, width, height, config):
        super().__init__(x, y, width, height, config)
        # self.url = config['url']
        self.bg_color = parse_color(config.get("bg_color", "#000000"))
        self.fg_color = parse_color(config.get("fg_color", "#ffffff"))
        # self.label = config.get("label", "")
        # self.mode = config.get("mode", "json")
        # self.json_path = config['json_path']
        # self.theme = config.get("theme", "light")
        self.latitude = config['latitude']
        self.longitude = config['longitude']
        self.refresh_interval = 60 * 10

    def find_font_size(self, test_text, height, width):
        font_size = 1

        for i in range(height):
            font = ImageFont.load_default(font_size)
            length = font.getlength(test_text)
            if length > 0.9 * width or font_size > 0.9 * height:
                break
            font_size += 1

        if font_size > 0.5 * height:
            font_size = 0.5 * height

        return font_size

    def fetch_data(self):
        url = f"https://api.weather.gov/points/{self.latitude},{self.longitude}"
        data = requests.get(url)
        data = data.json()
        forecast_url = data['properties']['forecast']
        forecast = requests.get(forecast_url)
        self.data = forecast.json()

    def refresh(self):
        """
        Write the text into the framebuffer
        """

        weather_layout = SimpleFlexBox(
            identifier="weather_layout",
            flex_direction="column",
            padding='2vw',
            children=[
                SimpleFlexBox(
                    identifier="top_row",
                    flex_direction="row",
                    weight=2,
                    children=[
                        SimpleFlexBox(
                            identifier="icon_box",
                            padding='5vw'
                        ),
                        SimpleFlexBox(
                            identifier="text_box",
                            padding='5vw',
                            gap='5%',
                            flex_direction='column',
                            children=[
                                SimpleFlexBox(
                                    identifier="period_name",
                                ),
                                SimpleFlexBox(
                                    identifier="temperature",
                                    weight=4
                                ),
                                SimpleFlexBox(
                                    identifier="short_forecast",
                                )
                            ]
                        )
                    ]
                ),
                SimpleFlexBox(
                    identifier="bottom_row",
                    flex_direction="row",
                    children=[
                        SimpleFlexBox(
                            identifier="detailed_forecast",
                            padding=('2vw', '5vw', '2vw', '5vw'),
                            gap='5vw',
                            children=[
                                SimpleFlexBox(
                                    identifier='wind_speed'
                                ),
                                SimpleFlexBox(
                                    identifier='wind_direction'
                                ),
                            ]
                        )
                    ]
                )
            ]
        )
        layout = weather_layout.compute_sizes(0, 0, self.width, self.height)


        image = Image.new("RGBA", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(image)

        self.fetch_data()
        print(self.data)

        # self.size = self.find_font_size(self.data, self.height, self.width)
        sub_font = ImageFont.load_default(self.height // 16)
        md_font = ImageFont.load_default(self.height // 8)
        font = ImageFont.load_default(self.height // 4)
        # date_font = ImageFont.load_default(0.25 * self.size)

        # font_top = self.height - self.size - 0.25 * self.size - 0.25 * self.size

        # print(x, y, self.size)
        temperature = self.data['properties']['periods'][0]['temperature']
        temp_unit = self.data['properties']['periods'][0]['temperatureUnit']
        period_name = self.data['properties']['periods'][0]['name']
        short_forecast = self.data['properties']['periods'][0]['shortForecast']
        icon = self.data['properties']['periods'][0]['icon']
        icon_data = requests.get(icon).content
        icon_image = Image.open(BytesIO(icon_data))
        icon_image = icon_image.convert("RGBA")
        icon_image = icon_image.resize((self.height // 2, self.height // 2), Image.Resampling.LANCZOS)
        rounded_mask = Image.new("L", icon_image.size, 255)
        maskdraw = ImageDraw.Draw(rounded_mask)
        # rounded rect with 25% radius
        maskdraw.rounded_rectangle(
            (0, 0, icon_image.size[0], icon_image.size[1]),
            round(icon_image.size[0] * 0.25),
            fill=0,
        )
        # maskdraw.ellipse((0, 0, icon_image.size[0], icon_image.size[1]), fill=0)

        # invert mask
        rounded_mask = ImageOps.invert(rounded_mask)

        icon_draw = ImageDraw.Draw(icon_image)

        # draw ellipse
        # icon_draw.ellipse((0, 0, icon_image.size[0], icon_image.size[1]), outline=(255, 255, 255, 255), width=4)
        icon_draw.rounded_rectangle(
            (0, 0, icon_image.size[0], icon_image.size[1]),
            round(icon_image.size[0] * 0.25),
            outline=(255, 255, 255, 255),
            width=4,
        )


        image.paste(icon_image, (
            (self.width // 2 - icon_image.size[0]) // 2,
            (self.height // 2 - icon_image.size[1]) // 2
        ), mask=rounded_mask)

        draw.text(
            (self.width // 2, 5),
            period_name,
            fill=self.fg_color,
            font=sub_font,
            anchor="lt",
        )
        draw.text(
            (self.width // 2, sub_font.size + 20),
            f"{temperature}°{temp_unit}",
            fill=self.fg_color,
            font=font,
            anchor="lt",
        )
        draw.text(
            (self.width // 2, sub_font.size + 15 + font.size + 5),
            short_forecast,
            fill=self.fg_color,
            font=sub_font,
            anchor="lt",
        )

        wind_speed = self.data['properties']['periods'][0]['windSpeed']
        wind_direction = self.data['properties']['periods'][0]['windDirection']

        draw.text(
            (self.width // 4, self.height * 0.75),
            f"{wind_speed} {wind_direction}",
            fill=self.fg_color,
            font=md_font,
            anchor="mm",
        )
        draw.text(
            (self.width // 4, self.height * 0.75 + md_font.size + 5),
            "WIND SPEED",
            fill=self.fg_color,
            font=sub_font,
            anchor="mm",
        )

        # draw compass around the wind speed
        # tick marks
        for i in [0, 90, 180, 270]:
            draw.line(
                (
                    self.width // 4 + 0.5 * md_font.size * (1 + 0.5 * i // 90),
                    self.height * 0.75 + 0.5 * md_font.size * (1 + 0.5 * i // 90),
                    self.width // 4 + 0.5 * md_font.size * (1 + 0.5 * i // 90) + 0.25 * md_font.size * (1 + 0.5 * i // 90),
                    self.height * 0.75 + 0.5 * md_font.size * (1 + 0.5 * i // 90) + 0.25 * md_font.size * (1 + 0.5 * i // 90),
                ),
                fill=self.fg_color,
                width=2,
            )

        rain = self.data['properties']['periods'][0]['probabilityOfPrecipitation']['value'] or 0
        draw.text(
            (3 * self.width // 4, self.height * 0.75),
            f"{rain}%",
            fill='#2196f3',
            font=md_font,
            anchor="mm",
        )

        draw.text(
            (3 * self.width // 4, self.height * 0.75 + md_font.size + 5),
            "CHANCE OF RAIN",
            fill='#2196f3',
            font=sub_font,
            anchor="mm",
        )



        img_resized = image.resize((self.width, self.height), Image.Resampling.LANCZOS)
        self.bytes = img_resized.tobytes("raw", "BGRA")
        self.bytes_per_pixel = 4
        super().refresh()

    def refresh222(self):
        """
        Write the text into the framebuffer
        """
        image = Image.new("RGBA", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(image)

        self.fetch_data()
        print(self.data)

        # self.size = self.find_font_size(self.data, self.height, self.width)
        sub_font = ImageFont.load_default(self.height // 16)
        md_font = ImageFont.load_default(self.height // 8)
        font = ImageFont.load_default(self.height // 4)
        # date_font = ImageFont.load_default(0.25 * self.size)

        # font_top = self.height - self.size - 0.25 * self.size - 0.25 * self.size

        # print(x, y, self.size)
        temperature = self.data['properties']['periods'][0]['temperature']
        temp_unit = self.data['properties']['periods'][0]['temperatureUnit']
        period_name = self.data['properties']['periods'][0]['name']
        short_forecast = self.data['properties']['periods'][0]['shortForecast']
        icon = self.data['properties']['periods'][0]['icon']
        icon_data = requests.get(icon).content
        icon_image = Image.open(BytesIO(icon_data))
        icon_image = icon_image.convert("RGBA")
        icon_image = icon_image.resize((self.height // 2, self.height // 2), Image.Resampling.LANCZOS)
        rounded_mask = Image.new("L", icon_image.size, 255)
        maskdraw = ImageDraw.Draw(rounded_mask)
        # rounded rect with 25% radius
        maskdraw.rounded_rectangle(
            (0, 0, icon_image.size[0], icon_image.size[1]),
            round(icon_image.size[0] * 0.25),
            fill=0,
        )
        # maskdraw.ellipse((0, 0, icon_image.size[0], icon_image.size[1]), fill=0)

        # invert mask
        rounded_mask = ImageOps.invert(rounded_mask)

        icon_draw = ImageDraw.Draw(icon_image)

        # draw ellipse
        # icon_draw.ellipse((0, 0, icon_image.size[0], icon_image.size[1]), outline=(255, 255, 255, 255), width=4)
        icon_draw.rounded_rectangle(
            (0, 0, icon_image.size[0], icon_image.size[1]),
            round(icon_image.size[0] * 0.25),
            outline=(255, 255, 255, 255),
            width=4,
        )


        image.paste(icon_image, (
            (self.width // 2 - icon_image.size[0]) // 2,
            (self.height // 2 - icon_image.size[1]) // 2
        ), mask=rounded_mask)

        draw.text(
            (self.width // 2, 5),
            period_name,
            fill=self.fg_color,
            font=sub_font,
            anchor="lt",
        )
        draw.text(
            (self.width // 2, sub_font.size + 20),
            f"{temperature}°{temp_unit}",
            fill=self.fg_color,
            font=font,
            anchor="lt",
        )
        draw.text(
            (self.width // 2, sub_font.size + 15 + font.size + 5),
            short_forecast,
            fill=self.fg_color,
            font=sub_font,
            anchor="lt",
        )

        wind_speed = self.data['properties']['periods'][0]['windSpeed']
        wind_direction = self.data['properties']['periods'][0]['windDirection']

        draw.text(
            (self.width // 4, self.height * 0.75),
            f"{wind_speed} {wind_direction}",
            fill=self.fg_color,
            font=md_font,
            anchor="mm",
        )
        draw.text(
            (self.width // 4, self.height * 0.75 + md_font.size + 5),
            "WIND SPEED",
            fill=self.fg_color,
            font=sub_font,
            anchor="mm",
        )

        # draw compass around the wind speed
        # tick marks
        for i in [0, 90, 180, 270]:
            draw.line(
                (
                    self.width // 4 + 0.5 * md_font.size * (1 + 0.5 * i // 90),
                    self.height * 0.75 + 0.5 * md_font.size * (1 + 0.5 * i // 90),
                    self.width // 4 + 0.5 * md_font.size * (1 + 0.5 * i // 90) + 0.25 * md_font.size * (1 + 0.5 * i // 90),
                    self.height * 0.75 + 0.5 * md_font.size * (1 + 0.5 * i // 90) + 0.25 * md_font.size * (1 + 0.5 * i // 90),
                ),
                fill=self.fg_color,
                width=2,
            )

        rain = self.data['properties']['periods'][0]['probabilityOfPrecipitation']['value'] or 0
        draw.text(
            (3 * self.width // 4, self.height * 0.75),
            f"{rain}%",
            fill='#2196f3',
            font=md_font,
            anchor="mm",
        )

        draw.text(
            (3 * self.width // 4, self.height * 0.75 + md_font.size + 5),
            "CHANCE OF RAIN",
            fill='#2196f3',
            font=sub_font,
            anchor="mm",
        )



        img_resized = image.resize((self.width, self.height), Image.Resampling.LANCZOS)
        self.bytes = img_resized.tobytes("raw", "BGRA")
        self.bytes_per_pixel = 4
        super().refresh()

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
