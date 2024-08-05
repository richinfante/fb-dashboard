from PIL import Image, ImageDraw, ImageFont
from .base import WidgetBase
from ..util import eval_expr, parse_color
from datetime import datetime as dt
import requests

def get_keypath(obj, keypath):
    keys = keypath.split(".")
    for key in keys:
        obj = obj[key]
    return obj

class BigMetricWidget(WidgetBase):
    def __init__(self, x, y, width, height, config):
        super().__init__(x, y, width, height, config)
        self.url = config['url']
        self.bg_color = parse_color(config.get("bg_color", "#000000"))
        self.fg_color = parse_color(config.get("fg_color", "#16a34a"))
        self.label = config.get("label", "")
        self.mode = config.get("mode", "json")
        self.json_path = config['json_path']
        self.refresh_interval = 60 * 5

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
        data = requests.get(self.url)
        if self.mode == "json":
            data = data.json()
        else:
            raise ValueError("Unknown mode: %s" % self.mode)

        self.data = str(get_keypath(data, self.json_path))

    def refresh(self):
        """
        Write the text into the framebuffer
        """
        image = Image.new("RGBA", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(image)

        self.fetch_data()
        print(self.data)

        self.size = self.find_font_size(self.data, self.height, self.width)
        font = ImageFont.load_default(self.size)
        date_font = ImageFont.load_default(0.25 * self.size)

        font_top = self.height - self.size - 0.25 * self.size - 0.25 * self.size

        # print(x, y, self.size)
        draw.text(
            (self.width // 2, font_top),
            self.data,
            fill=self.fg_color,
            font=font,
            anchor="mt",
        )
        draw.text(
            (self.width // 2, font_top + self.size),
            self.label,
            fill=self.fg_color,
            font=date_font,
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
