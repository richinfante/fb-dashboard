from PIL import Image, ImageDraw, ImageFont
from .base import WidgetBase
from ..util import eval_expr, parse_color

class TextWidget(WidgetBase):
  def __init__(self, x, y, width, height, config):
    super().__init__(x, y, width, height, config)
    self.text = config['text']
    self.size = int(eval_expr(config['size'], {'w': width, 'h': height}))
    self.bg_color = parse_color(config.get('bg_color', '#000000'))
    self.fg_color = parse_color(config.get('fg_color', '#FFFFFF'))

  def refresh(self):
    """
      Write the text into the framebuffer
    """
    image = Image.new("RGBA", (self.width * 2, self.height * 2), self.bg_color)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(self.size)
    draw.text((0, 0), self.text, fill=self.fg_color, font=font)
    img_resized = image.resize((self.width,self.height), Image.Resampling.LANCZOS)
    self.bytes = img_resized.tobytes('raw', 'BGRA')
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
      fb.write_line(self.x, self.y + y, self.bytes[y_off:y_off + self.width * self.bytes_per_pixel])

