import toml
import time
import argparse
import sys
from datetime import datetime as dt
from .util import eval_expr
from .framebuffer import FrameBufferBase, LinuxFrameBuffer
from .widgets.image import ImageWidget
from .widgets.text import TextWidget
from .widgets.cloudwatch_metric import CloudWatchImageWidget
from .widgets.clock import ClockWidget
from .widgets.stock_candlestick import YFCandlestickWidget
from .widgets.satellite import SatelliteWidget
from .widgets.big_metric import BigMetricWidget

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--config", help="Path to the config file", default="config.toml")
    args.add_argument("--fb", help="Name of the framebuffer device", default="fb0")
    args.add_argument(
        "--export-filename",
        help="Export the framebuffer to a PNG file",
        default="framebuffer.png",
    )
    args.add_argument(
        "--no-framebuffer",
        help="Run without a framebuffer, writing to png specified by --export-filename",
        action="store_true",
    )
    args.add_argument(
        "--exit", help="Exit after writing the framebuffer", action="store_true"
    )
    args = args.parse_args()
    config = toml.load(args.config)

    plugins = {
        "Image": ImageWidget,
        "Text": TextWidget,
        "Clock": ClockWidget,
        'Metric': BigMetricWidget,
        "StockMarketCandlestick": YFCandlestickWidget,
        "CloudWatchMetricImage": CloudWatchImageWidget,
        "SatelliteMap": SatelliteWidget,
    }

    if args.no_framebuffer:
        fb = FrameBufferBase(1080, 720, export_filename=args.export_filename)
    else:
        fb = LinuxFrameBuffer(args.fb)  # create the framebuffer

    widgets = []

    # initialize widgets
    for widget_name, config in (config.get("widgets") or {}).items():
        # section_name = str(section)
        kind = config["type"]
        x = int(eval_expr(config["x"], {"w": fb.fb_width, "h": fb.fb_height}))
        y = int(eval_expr(config["y"], {"w": fb.fb_width, "h": fb.fb_height}))
        width = int(eval_expr(config["w"], {"w": fb.fb_width, "h": fb.fb_height}))
        height = int(eval_expr(config["h"], {"w": fb.fb_width, "h": fb.fb_height}))

        print(
            f"Creating widget of type {kind} at ({x}, {y}) with size ({width}, {height})"
        )

        if kind in plugins:
            widget = plugins[kind](x, y, width, height, config)
            widgets.append(widget)
        else:
            print(f"Unknown widget type: {kind}")
            exit(1)

    while True:
        # trigger a widget refresh
        # print('%s: refreshing widgets' % (str(dt.now())))
        now = dt.now()
        for widget in widgets:
            widget.refresh_in_bg_if_needed()
        # print('%s: done refreshing widgets (elapsed %s)' % (str(dt.now()), round((dt.now() - now).total_seconds(), 2)))

        # write widgets into framebuffer
        # print('%s: writing widgets into framebuffer' % (str(dt.now())))
        now = dt.now()
        for widget in widgets:
            widget.write_into_fb(fb)
        # print('%s: done writing widgets into framebuffer (elapsed %s)' % (str(dt.now()), round((dt.now() - now).total_seconds(), 2)))

        # copy our virtual buffer with the real one
        fb.swap_buffers()
        fb.make_buffer()

        # for testing, exit after all widgets have refreshed for the first time
        # --exit flag must be set to use this
        if args.exit:
            all_rendered = True
            for widget in widgets:
                if not widget.has_refreshed:
                    all_rendered = False
                    break

            if all_rendered:
                sys.exit(0)

        # wait for a bit
        time.sleep(0.25)
