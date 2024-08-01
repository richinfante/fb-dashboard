from ..util import eval_expr
from io import BytesIO
from PIL import Image
from .base import WidgetBase
from io import BytesIO
from datetime import datetime as dt, timedelta

class YFCandlestickWidget(WidgetBase):
    def __init__(self, x, y, width, height, config):
        super().__init__(x, y, width, height, config)

        # parse configuration
        self.symbol = config["symbol"]
        # mpf style, see https://github.com/matplotlib/mplfinance/blob/master/examples/styles.ipynb
        self.plot_style = config.get("plot_style", "nightclouds")
        self.up_color = config.get("up_color", "#00FF00")
        self.down_color = config.get("down_color", "#FF0000")
        # ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
        self.time_period = config.get("time_period", '1mo')
        # [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
        self.interval = config.get("interval", "1d")
        self.show_volume = eval_expr(config.get("show_volume", "True"), {})

        self.bytes = None

    def refresh(self):
        """
        refresh the image and data
        """
        self.render_data()
        super().refresh()

    def render_data(self):
        import matplotlib
        import yfinance as yf
        import mplfinance as mpf

        # use agg backend, so we can run in a headless environment
        matplotlib.use("agg")

        # get yf data
        data = yf.download(tickers=self.symbol, period=self.time_period, interval=self.interval)

        # make style
        mc = mpf.make_marketcolors(up=self.up_color, down=self.down_color, inherit=True)

        # https://github.com/matplotlib/mplfinance/blob/master/examples/styles.ipynb
        # Create a new style based on `nightclouds` but with my own `marketcolors`:
        s = mpf.make_mpf_style(base_mpf_style=self.plot_style, marketcolors=mc)

        buf = BytesIO()
        mpf.plot(
            data,
            type="candle",
            style=s,
            savefig=buf,
            tight_layout=True,
            title=self.symbol,
            volume=self.show_volume,
        )

        buf.seek(0)

        self.image = Image.open(buf)
        self.image = self.image.resize((self.width, self.height))

        # ensure the image has an alpha channel
        if not self.image.has_transparency_data:
            # https://stackoverflow.com/a/46366964
            a_channel = Image.new("L", self.image.size, 255)
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
