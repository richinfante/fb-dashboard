from PIL import Image, ImageDraw, ImageFont
from .base import WidgetBase
from ..util import eval_expr, parse_color
from datetime import datetime as dt
import pytz


class ClockWidget(WidgetBase):
    def __init__(self, x, y, width, height, config):
        super().__init__(x, y, width, height, config)
        # self.size = int(eval_expr(config['size'], {'w': width, 'h': height}))
        self.bg_color = parse_color(config.get("bg_color", "#000000"))
        self.fg_color = parse_color(config.get("fg_color", "#FFFFFF"))
        self.clock_format = config.get("clock_format", "%H:%M:%S")
        self.date_format = config.get("date_format", "%Y-%m-%d")
        self.timezone = config.get("timezone")
        self.refresh_interval = 0.25

        font_size = 1

        test_text = dt.now().strftime(self.clock_format)
        for i in range(height):
            font = ImageFont.load_default(font_size)
            length = font.getlength(test_text)
            if length > 0.9 * width or font_size > 0.9 * height:
                break
            font_size += 1

        self.size = font_size

    def refresh(self):
        """
        Write the text into the framebuffer
        """
        image = Image.new("RGBA", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default(self.size)

        date_font = ImageFont.load_default(0.25 * self.size)

        if not self.timezone:
            text = dt.now().strftime(self.clock_format)
            date_text = dt.now().strftime(self.date_format)
        else:
            tz = pytz.timezone(self.timezone)
            text = dt.now(tz).strftime(self.clock_format)
            date_text = dt.now(tz).strftime(self.date_format)

        # print(x, y, self.size)
        draw.text(
            (self.width // 2, self.height // 2),
            text,
            fill=self.fg_color,
            font=font,
            anchor="mm",
        )
        draw.text(
            (self.width // 2, self.height // 2 + self.size / 2 + 0.25 * self.size),
            date_text,
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
