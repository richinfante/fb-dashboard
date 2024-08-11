from PIL import Image, ImageDraw, ImageFont, ImageOps
from .base import WidgetBase
from ..util import eval_expr, parse_color
from datetime import datetime as dt
import requests
from io import BytesIO
from ..sfxbox import SimpleFlexBox
from ..render_util import (
    autodraw_text,
    draw_layout_boxes,
    paste_image_into_bounds,
    rounded_image,
)


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
        self.label_color = parse_color(config.get("label_color", "#aaaaaa"))
        # self.label = config.get("label", "")
        # self.mode = config.get("mode", "json")
        # self.json_path = config['json_path']
        # self.theme = config.get("theme", "light")
        self.latitude = config["latitude"]
        self.longitude = config["longitude"]
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
        forecast_url = data["properties"]["forecast"]
        forecast = requests.get(forecast_url)
        self.data = forecast.json()

    def refresh(self):
        """
        Write the text into the framebuffer
        """

        weather_layout = SimpleFlexBox(
            identifier="weather_layout",
            flex_direction="column",
            padding="2vw",
            children=[
                SimpleFlexBox(
                    identifier="top_row",
                    flex_direction="row",
                    weight=2,
                    padding=("5vw", 0, "5vw", 0),
                    children=[
                        SimpleFlexBox(
                            identifier="icon_box",
                            padding=(0, "2vw", 0, "5vw"),
                        ),
                        SimpleFlexBox(
                            identifier="text_box",
                            padding=(0, "5vw", 0, "5vw"),
                            gap="5%",
                            weight=2,
                            flex_direction="column",
                            children=[
                                SimpleFlexBox(
                                    identifier="period_name",
                                ),
                                SimpleFlexBox(identifier="temperature", weight=4),
                                SimpleFlexBox(
                                    identifier="short_forecast",
                                ),
                            ],
                        ),
                    ],
                ),
                SimpleFlexBox(
                    identifier="bottom_row",
                    flex_direction="row",
                    children=[
                        SimpleFlexBox(
                            identifier="detailed_forecast",
                            padding=("2vw", "5vw", "2vw", "5vw"),
                            gap="5vw",
                            children=[
                                SimpleFlexBox(
                                    identifier="wind_speed",
                                    flex_direction="column",
                                    gap="5%",
                                    children=[
                                        SimpleFlexBox(
                                            identifier="wind_speed_value", weight=3
                                        ),
                                        SimpleFlexBox(identifier="wind_speed_label"),
                                    ],
                                ),
                                SimpleFlexBox(
                                    identifier="wind_direction",
                                    flex_direction="column",
                                    gap="5%",
                                    children=[
                                        SimpleFlexBox(
                                            identifier="wind_direction_value", weight=3
                                        ),
                                        SimpleFlexBox(
                                            identifier="wind_direction_label"
                                        ),
                                    ],
                                ),
                                SimpleFlexBox(
                                    identifier="rain",
                                    flex_direction="column",
                                    gap="5%",
                                    children=[
                                        SimpleFlexBox(
                                            identifier="rain_value", weight=3
                                        ),
                                        SimpleFlexBox(identifier="rain_label"),
                                    ],
                                ),
                            ],
                        )
                    ],
                ),
            ],
        )
        layout = weather_layout.compute_sizes(0, 0, self.width, self.height)

        image = Image.new("RGBA", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(image)

        self.fetch_data()

        # print(x, y, self.size)
        temperature = self.data["properties"]["periods"][0]["temperature"]
        temp_unit = self.data["properties"]["periods"][0]["temperatureUnit"]
        period_name = self.data["properties"]["periods"][0]["name"]
        short_forecast = self.data["properties"]["periods"][0]["shortForecast"]
        icon = self.data["properties"]["periods"][0]["icon"]

        if self.debug:
            draw_layout_boxes(
                draw,
                layout,
                self.width,
                self.height,
                box_color="gray",
                content_box_color="red",
                text_color="gray",
            )

        autodraw_text(
            draw, period_name, layout["period_name"]["content_box"], fill=self.fg_color
        )
        autodraw_text(
            draw,
            f"{temperature}°{temp_unit}",
            layout["temperature"]["content_box"],
            fill=self.fg_color,
            anchor="lm",
        )
        autodraw_text(
            draw,
            short_forecast,
            layout["short_forecast"]["content_box"],
            fill=self.fg_color,
        )

        font_size = autodraw_text(
            draw,
            "WIND BEARING",
            layout["wind_direction_label"]["content_box"],
            fill=self.label_color,
        )

        autodraw_text(
            draw,
            "WIND SPEED",
            layout["wind_speed_label"]["content_box"],
            fill=self.label_color,
            max_font_size=font_size,
        )
        autodraw_text(
            draw,
            "RAIN",
            layout["rain_label"]["content_box"],
            fill=self.label_color,
            max_font_size=font_size,
        )

        wind_speed = self.data["properties"]["periods"][0]["windSpeed"]
        wind_direction = self.data["properties"]["periods"][0]["windDirection"]
        rain = (
            self.data["properties"]["periods"][0]["probabilityOfPrecipitation"]["value"]
            or 0
        )

        autodraw_text(
            draw,
            wind_speed,
            layout["wind_speed_value"]["content_box"],
            fill=self.fg_color,
            anchor="lm",
        )
        autodraw_text(
            draw,
            wind_direction,
            layout["wind_direction_value"]["content_box"],
            fill=self.fg_color,
            anchor="lm",
        )
        autodraw_text(
            draw,
            f"{rain}%",
            layout["rain_value"]["content_box"],
            fill=self.fg_color,
            anchor="lm",
        )

        icon_data = requests.get(icon).content
        icon_image = Image.open(BytesIO(icon_data))
        icon_image = icon_image.convert("RGBA")

        # paste_image_into_bounds(image, icon_image_masked, layout['icon_box']['content_box'])
        icon_data = requests.get(icon.replace("size=medium", "size=large")).content
        icon_image = Image.open(BytesIO(icon_data))
        icon_image = icon_image.convert("RGBA")
        icon_image = ImageOps.contain(
            icon_image,
            (
                layout["icon_box"]["content_box"][2],
                layout["icon_box"]["content_box"][3],
            ),
            Image.LANCZOS,
        )

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

        image.paste(
            icon_image,
            (
                layout["icon_box"]["content_box"][0]
                + (layout["icon_box"]["content_box"][2] - icon_image.size[0]) // 2,
                layout["icon_box"]["content_box"][1]
                + (layout["icon_box"]["content_box"][3] - icon_image.size[1]) // 2,
            ),
            mask=rounded_mask,
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
