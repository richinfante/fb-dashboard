import requests
from io import BytesIO
from PIL import Image, ImageOps
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from .base import WidgetBase
import boto3
import json
from ..util import eval_expr


class CloudWatchImageWidget(WidgetBase):
    def __init__(self, x, y, width, height, config):
        super().__init__(x, y, width, height, config)
        self.widget = eval_expr(config["widget"], {"w": self.width, "h": self.height})
        if isinstance(self.widget, dict):
            self.widget = json.dumps(self.widget)

        self.aws_profile = config.get("aws_profile", None)
        self.aws_region = config.get("aws_region", None)
        self.invert_image = eval_expr(config.get("invert", "False"), {})
        self.bytes = None

    def refresh(self):
        """
        Refresh the image from cloudwatch
        """
        self.load_image()
        super().refresh()

    def load_image(self):
        """
        Load the image from cloudwatch
        """
        if self.aws_profile or self.aws_region:
            boto3_session = boto3.session.Session(
                profile_name=self.aws_profile, region_name=self.aws_region
            )
            cloudwatch = boto3_session.client("cloudwatch")
        else:
            cloudwatch = boto3.client("cloudwatch")

        response = cloudwatch.get_metric_widget_image(
            MetricWidget=self.widget, OutputFormat="png"
        )

        raw_bytes = response["MetricWidgetImage"]
        self.raw_image = Image.open(BytesIO(raw_bytes))
        self.image = self.raw_image.resize((self.width, self.height))

        if self.invert_image:
            self.image = ImageOps.invert(self.image)

        # ensure the image has an alpha channel
        if not self.image.has_transparency_data:
            # https://stackoverflow.com/a/46366964
            a_channel = Image.new(
                "L", self.image.size, 255
            )  # 'L' 8-bit pixels, black and white
            self.image.putalpha(a_channel)

        # convert to BGRA format
        self.bytes = self.image.tobytes("raw", "BGRA")
        self.bytes_per_pixel = 4

    def write_into_fb(self, fb):
        """
        Write the image into the framebuffer
        """
        if not self.bytes:
            return

        for y in range(self.height):
            y_off = y * self.width * self.bytes_per_pixel
            fb.write_line(
                self.x,
                self.y + y,
                self.bytes[y_off : y_off + self.width * self.bytes_per_pixel],
            )
