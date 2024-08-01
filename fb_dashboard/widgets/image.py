import requests
from io import BytesIO
from PIL import Image
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from .base import WidgetBase


class ImageWidget(WidgetBase):
    def __init__(self, x, y, width, height, config):
        super().__init__(x, y, width, height, config)
        self.path = config["path"]
        self.bytes = None

        # allow for basic auth or digest auth to be used for password protected images
        if config.get("username") and config.get("password"):
            if config.get("auth_type") == "basic" or not config.get("auth_type"):
                self.auth = HTTPBasicAuth(config["username"], config["password"])
            elif config.get("auth_type") == "digest":
                self.auth = HTTPDigestAuth(config["username"], config["password"])
            else:
                print(f'Unknown auth type: {config.get("auth_type")}')
                exit(1)

        else:
            self.auth = None

    def refresh(self):
        self.load_image()
        super().refresh()

    def load_image(self):
        """
        Load the static image from the path, or download it from the internet
        """
        if self.path.startswith("http") or self.path.startswith("https"):
            req = requests.get(self.path, auth=self.auth, timeout=10)

            if not req.ok:
                print(
                    f"Failed to download image from {self.path}: {req.status_code} ({req.reason})"
                )
                self.raw_image = Image.new("RGBA", (self.width, self.height))
            else:
                self.raw_image = Image.open(BytesIO(req.content))
        else:
            self.raw_image = Image.open(self.path)

        self.image = self.raw_image.resize((self.width, self.height))

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
        if not self.has_refreshed:
            return

        for y in range(self.height):
            y_off = y * self.width * self.bytes_per_pixel
            fb.write_line(
                self.x,
                self.y + y,
                self.bytes[y_off : y_off + self.width * self.bytes_per_pixel],
            )
