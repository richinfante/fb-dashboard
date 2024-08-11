from pprint import pprint
from fb_dashboard.sfxbox import SimpleFlexBox
from fb_dashboard.render_util import draw_layout_boxes
weather_layout = SimpleFlexBox(
    identifier="weather_layout",
    flex_direction="column",
    padding="2vw",
    children=[
        SimpleFlexBox(
            identifier="top_row",
            flex_direction="row",
            weight=2,
            children=[
                SimpleFlexBox(identifier="icon_box", padding="5vw"),
                SimpleFlexBox(
                    weight=2,
                    identifier="text_box",
                    padding="5vw",
                    gap="5%",
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
                        SimpleFlexBox(identifier="wind_speed"),
                        SimpleFlexBox(identifier="wind_direction"),
                    ],
                )
            ],
        ),
    ],
)


from PIL import Image, ImageDraw, ImageFont

test_w = 1024
test_h = 768

layout = weather_layout.compute_sizes(0, 0, test_w, test_h)
pprint(layout)

image = Image.new("RGB", (test_w, test_h), (255, 255, 255))
draw = ImageDraw.Draw(image)
draw_layout_boxes(draw, layout, test_w, test_h)
image.save("layout.png")
