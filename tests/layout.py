from pprint import pprint
from fb_dashboard.sfxbox import SimpleFlexBox
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
                    weight=2,
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


from PIL import Image, ImageDraw, ImageFont

test_w = 1024
test_h = 768

layout = weather_layout.compute_sizes(0, 0, test_w, test_h)
pprint(layout)

image = Image.new("RGB", (test_w, test_h), (255, 255, 255))
draw = ImageDraw.Draw(image)
texts = {}
for (box_id, box_sizes) in layout.items():
    draw.rectangle((box_sizes['box'][0], box_sizes['box'][1], box_sizes['box'][0] + box_sizes['box'][2], box_sizes['box'][1] + box_sizes['box'][3]), outline="black")
    draw.rectangle((box_sizes['content_box'][0], box_sizes['content_box'][1], box_sizes['content_box'][0] + box_sizes['content_box'][2], box_sizes['content_box'][1] + box_sizes['content_box'][3]), outline="red")

    content_coord = (box_sizes["content_box"][0], box_sizes["content_box"][1])
    if content_coord in texts:
        texts[content_coord] += ', ' + box_id+'#content'
    else:
        texts[content_coord] = box_id + '#content'

    # root_coord = (box_sizes["box"][0], box_sizes["box"][1])
    # if root_coord in texts:
    #     texts[root_coord] += ', ' + box_id + '#box'
    # else:
    #     texts[root_coord] = box_id + '#box'

font = ImageFont.load_default(test_h / 48)
for (coord, txt) in texts.items():
    draw.text(coord, txt, fill="black", font=font)
image.save("layout.png")