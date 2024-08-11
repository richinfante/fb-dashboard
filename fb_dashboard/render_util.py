from PIL import Image, ImageDraw, ImageFont, ImageOps

def autosize_text_into_size (text, font, max_width, max_height):
    """
    Resizes the font size to fit the text into the given bounds
    """
    # Start with a large font size
    font_size = max_height
    font = ImageFont.load_default(font_size)
    text_width = font.getlength(text)
    text_height = font.size

    # Reduce the font size until it fits
    while text_width > max_width or text_height > max_height:
        font_size -= 1
        font = ImageFont.load_default(font_size)
        text_width = font.getlength(text)
        text_height = font.size

    return font

def autodraw_text(draw, text, box, max_font_size=None, **kwargs):
    (x, y, width, height) = box

    """
    Automatically draw text into a box, resizing the font as necessary
    """
    font = autosize_text_into_size(text, ImageFont.load_default(1), width, height)

    if max_font_size and font.size > max_font_size:
        font = ImageFont.load_default(max_font_size)

    if kwargs.get('anchor'):
        anchor = kwargs.get('anchor')
        if anchor == 'mm':
            origin = (x + width // 2, y + height // 2)
        elif anchor == 'lt':
            origin = (x, y)
        elif anchor == 'mt':
            origin = (x + width // 2, y)
        elif anchor == 'rt':
            origin = (x + width, y)
        elif anchor == 'lm':
            origin = (x, y + height // 2)
        elif anchor == 'rm':
            origin = (x + width, y + height // 2)
        elif anchor == 'lb':
            origin = (x, y + height)
        elif anchor == 'mb':
            origin = (x + width // 2, y + height)
        elif anchor == 'rb':
            origin = (x + width, y + height)
        else:
            raise ValueError(f"Unknown anchor: {anchor}")
    else:
        origin = (x, y)

    draw.text(origin, text, font=font, **kwargs)
    return font.size


def draw_layout_boxes (draw, layout, width, height, box_color="black", content_box_color="red", text_color="black"):
  texts = {}
  for (box_id, box_sizes) in layout.items():
      draw.rectangle((box_sizes['box'][0], box_sizes['box'][1], box_sizes['box'][0] + box_sizes['box'][2], box_sizes['box'][1] + box_sizes['box'][3]), outline=box_color)
      draw.rectangle((box_sizes['content_box'][0], box_sizes['content_box'][1], box_sizes['content_box'][0] + box_sizes['content_box'][2], box_sizes['content_box'][1] + box_sizes['content_box'][3]), outline=content_box_color)

      content_coord = (box_sizes["content_box"][0], box_sizes["content_box"][1])
      if content_coord in texts:
          texts[content_coord] += ', ' + box_id
      else:
          texts[content_coord] = box_id

      # root_coord = (box_sizes["box"][0], box_sizes["box"][1])
      # if root_coord in texts:
      #     texts[root_coord] += ', ' + box_id + '#box'
      # else:
      #     texts[root_coord] = box_id + '#box'

  font = ImageFont.load_default(height / 48)
  for (coord, txt) in texts.items():
      draw.text(coord, txt, fill=text_color, font=font)


def paste_image_into_bounds(main_image, image, box):
    (x, y, width, height) = box

    image_resized = image.resize((width, height), Image.Resampling.LANCZOS)
    main_image.paste(image_resized, (x, y))

def rounded_image(image, radius, border_color=None, border_width=0):
    """
    Create a rounded image with an optional border
    """
    width, height = image.size

    rounded_image = image.copy()

    # Create a mask
    mask = Image.new("L", (width, height), 0)
    maskdraw = ImageDraw.Draw(mask)
    maskdraw.rounded_rectangle(
      (0, 0, width, height),
      radius=radius,
      fill=0,
    )

    mask = ImageOps.invert(mask)

    # Apply the mask
    rounded_image.paste(image, (0, 0), mask=mask)

    # Create a new image with the desired size
    draw = ImageDraw.Draw(rounded_image)
    if border_color:
        draw.rounded_rectangle(
          (0, 0, width, height),
          radius=radius,
          outline=border_color,
          width=border_width,
        )

    return rounded_image


def draw_image_into_bounds(draw, image, box):
    (x, y, width, height) = box

    if not image.has_alpha():
        image.putalpha(255)

    image_resized = image.resize((width, height), Image.Resampling.LANCZOS)
    draw.bitmap((x, y), image_resized.tobytes("raw", "BGRA"), width, height)