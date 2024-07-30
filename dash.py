import configparser
import boto3
import requests
import mmap
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import time
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import argparse
import json

def eval_expr(expr, variables):
  return eval(expr, {**variables, 'false': False, 'true': True})

def parse_color(color: str) -> tuple:
  """
    Parse a color string into an RGB tuple
  """
  if color.startswith('#'):
    if len(color) == 4:
      r = int(color[1:2], 16) * 17
      g = int(color[2:3], 16) * 17
      b = int(color[3:4], 16) * 17
    else:
      r = int(color[1:3], 16)
      g = int(color[3:5], 16)
      b = int(color[5:7], 16)

    return (r, g, b)

  elif color.startswith('rgb'):
    return tuple(map(int, color[4:-1].split(',')))


class FrameBufferBase:
  def __init__(self, width, height, bits_per_pixel=32):
    self.fb_width = width
    self.fb_height = height
    self.fb_bits_per_pixel = bits_per_pixel

    # setup a buffer to draw to
    self.make_buffer()

  def make_buffer(self):
    """
      Create a virtual buffer to store the image data.
      We write to this buffer and then swap it with the actual framebuffer, to avoid flickering and tearing while drawing, since drawing pixels directly to the framebuffer is slow.
    """
    buf = BytesIO()
    num_bytes = self.fb_width * self.fb_height * (self.fb_bits_per_pixel // 8)
    buf.write(b'\x00' * num_bytes)
    buf.seek(0)

    self.virtual_buffer = buf

  def set_pixel(self, x, y, r, g, b, a):
    """
      set a single pixel in the virtual buffer
    """
    if x < 0 or x >= self.fb_width or y < 0 or y >= self.fb_height:
      return

    self.virtual_buffer.seek((y * self.fb_width + x) * self.fb_bits_per_pixel // 8)
    self.virtual_buffer.write(b.to_bytes(1, byteorder='little'))
    self.virtual_buffer.write(g.to_bytes(1, byteorder='little'))
    self.virtual_buffer.write(r.to_bytes(1, byteorder='little'))
    self.virtual_buffer.write(a.to_bytes(1, byteorder='little'))

  def write_line(self, x, y, bytes):
    """
      write a line of pixels to the virtual buffer
    """
    self.virtual_buffer.seek((y * self.fb_width + x) * self.fb_bits_per_pixel // 8)
    self.virtual_buffer.write(bytes)

  def export_png(self, path):
    """
      Export the virtual buffer as a PNG file
      Mainly for debugging purposes, running without a framebuffer on a non-linux system or in a container
    """
    img = Image.frombytes('RGBA', (self.fb_width, self.fb_height), self.virtual_buffer.getvalue(), 'raw', 'BGRA')
    img.save(path, 'PNG')

  def swap_buffers(self):
    """
      'swap' the virtual buffer with the actual framebuffer

      bulk write the virtual buffer to the framebuffer, so that the screen updates in one go
    """
    self.export_png('framebuffer.png')

class LinuxFrameBuffer(FrameBufferBase):
  def __init__(self, fb_name):
    self.fb_name = fb_name

    # get fb resolution
    [fb_w, fb_h] = open("/sys/class/graphics/fb0/virtual_size", "r").read().strip().split(",")
    self.fb_width = int(fb_w)
    self.fb_height = int(fb_h)

    # get bits per pixel
    self.fb_bits_per_pixel = int(open("/sys/class/graphics/fb0/bits_per_pixel", "r").read())

    # save the screen resolution
    self.fbpath = '/dev/' + self.fb_name
    self.fbdev = os.open(self.fbpath, os.O_RDWR)

    # use mmap to map the framebuffer to memory
    num_bits = self.fb_width*self.fb_height*self.fb_bits_per_pixel
    self.fb = mmap.mmap(self.fbdev, num_bits//8, mmap.MAP_SHARED, mmap.PROT_WRITE|mmap.PROT_READ, offset=0)

    # setup a buffer to draw to
    self.make_buffer()

  def swap_buffers(self):
    """
      'swap' the virtual buffer with the actual framebuffer

      bulk write the virtual buffer to the framebuffer, so that the screen updates in one go
    """
    self.fb.seek(0)
    self.fb.write(self.virtual_buffer.getvalue())

class Widget:
  def __init__(self, x, y, width, height):
    self.x = x
    self.y = y
    self.width = width
    self.height = height

class CloudWatchImageWidget(Widget):
  def __init__(self, x, y, width, height, config):
    super().__init__(x, y, width, height)
    self.widget = eval_expr(config['widget'], {'w': self.width, 'h': self.height})
    if isinstance(self.widget, dict):
      self.widget = json.dumps(self.widget)

    self.aws_profile = config.get('aws_profile', None)
    self.aws_region = config.get('aws_region', None)
    self.load_image()

  def refresh(self):
    """
      Refresh the image from cloudwatch
    """
    self.load_image()

  def load_image(self):
    """
      Load the image from cloudwatch
    """
    if self.aws_profile or self.aws_region:
      print(f'Using profile {self.aws_profile}')
      boto3_session = boto3.session.Session(profile_name=self.aws_profile, region_name=self.aws_region)
      cloudwatch = boto3_session.client('cloudwatch')
    else:
      cloudwatch = boto3.client('cloudwatch')

    response = cloudwatch.get_metric_widget_image(
      MetricWidget=self.widget,
      OutputFormat='png'
    )

    self.bytes = response['MetricWidgetImage']
    self.raw_image = Image.open(BytesIO(self.bytes))
    self.image = self.raw_image.resize((width, height))

    # ensure the image has an alpha channel
    if not self.image.has_transparency_data:
      # https://stackoverflow.com/a/46366964
      a_channel = Image.new('L', self.image.size, 255)   # 'L' 8-bit pixels, black and white
      self.image.putalpha(a_channel)

    # convert to BGRA format
    self.bytes = self.image.tobytes('raw', 'BGRA')
    self.bytes_per_pixel = 4

  def write_into_fb(self, fb):
    """
      Write the image into the framebuffer
    """
    for y in range(self.height):
      y_off = y * self.width * self.bytes_per_pixel
      fb.write_line(self.x, self.y + y, self.bytes[y_off:y_off + self.width * self.bytes_per_pixel])

class TextWidget(Widget):
  def __init__(self, x, y, width, height, config):
    super().__init__(x, y, width, height)
    self.text = config['text']
    self.size = int(eval_expr(config['size'], {'w': width, 'h': height}))
    self.bg_color = parse_color(config.get('bg_color', '#000000'))
    self.fg_color = parse_color(config.get('fg_color', '#FFFFFF'))
    self.refresh()

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

  def write_into_fb(self, fb):
    """
      Write the image into the framebuffer
    """
    for y in range(self.height):
      y_off = y * self.width * self.bytes_per_pixel
      fb.write_line(self.x, self.y + y, self.bytes[y_off:y_off + self.width * self.bytes_per_pixel])


class ImageWidget(Widget):
  def __init__(self, x, y, width, height, config):
    super().__init__(x, y, width, height)
    self.path = config['path']

    # allow for basic auth or digest auth to be used for password protected images
    if config.get('username') and config.get('password'):
      if config.get('auth_type') == 'basic' or not config.get('auth_type'):
        self.auth = HTTPBasicAuth(config['username'], config['password'])
      elif config.get('auth_type') == 'digest':
        self.auth = HTTPDigestAuth(config['username'], config['password'])
      else:
        print(f'Unknown auth type: {config.get("auth_type")}')
        exit(1)

    else:
      self.auth = None

    self.load_image()

  def refresh(self):
    self.load_image()

  def load_image(self):
    """
      Load the static image from the path, or download it from the internet
    """
    if self.path.startswith('http') or self.path.startswith('https'):
      req = requests.get(self.path, auth=self.auth)

      if not req.ok:
        print(f'Failed to download image from {self.path}: {req.status_code} ({req.reason})')
        self.raw_image = Image.new('RGBA', (self.width, self.height))
      else:
        self.bytes = req.content
        self.raw_image = Image.open(BytesIO(self.bytes))
    else:
      self.raw_image = Image.open(self.path)

    self.image = self.raw_image.resize((width, height))

    # ensure the image has an alpha channel
    if not self.image.has_transparency_data:
      # https://stackoverflow.com/a/46366964
      a_channel = Image.new('L', self.image.size, 255)   # 'L' 8-bit pixels, black and white
      self.image.putalpha(a_channel)

    # convert to BGRA format
    self.bytes = self.image.tobytes('raw', 'BGRA')
    self.bytes_per_pixel = 4

  def write_into_fb(self, fb):
    """
      Write the image into the framebuffer
    """
    for y in range(self.height):
      y_off = y * self.width * self.bytes_per_pixel
      fb.write_line(self.x, self.y + y, self.bytes[y_off:y_off + self.width * self.bytes_per_pixel])

if __name__ == '__main__':
  args = argparse.ArgumentParser()
  args.add_argument('--config', help='Path to the config file', default='config.ini')
  args.add_argument('--fb', help='Name of the framebuffer device', default='fb0')
  args.add_argument('--no-framebuffer', help='Run without a framebuffer, writing to png', action='store_true')
  args = args.parse_args()

  config = configparser.RawConfigParser()
  config.read(args.config)  # load the config file

  plugins = {
    'Image': ImageWidget,
    'Text': TextWidget,
    'CloudWatchMetricImage': CloudWatchImageWidget
  }

  if args.no_framebuffer:
    fb = FrameBufferBase(1080, 720)
  else:
    fb = LinuxFrameBuffer(args.fb)  # create the framebuffer

  widgets = []
  refresh_interval = 60

  # initialize widgets
  for section in config.sections():
    section_name = str(section)
    if section_name.startswith('widget'):
      kind = config[section]['type']
      x = int(eval_expr(config[section]['x'], {'w': fb.fb_width, 'h': fb.fb_height}))
      y = int(eval_expr(config[section]['y'], {'w': fb.fb_width, 'h': fb.fb_height}))
      width = int(eval_expr(config[section]['w'], {'w': fb.fb_width, 'h': fb.fb_height}))
      height = int(eval_expr(config[section]['h'], {'w': fb.fb_width, 'h': fb.fb_height}))

      raw_config = {k: v for (k,v) in config[section].items()}

      print(f'Creating widget of type {kind} at ({x}, {y}) with size ({width}, {height})')

      if kind in plugins:
        widget = plugins[kind](x, y, width, height, raw_config)
        widgets.append(widget)
      else:
        print(f'Unknown widget type: {kind}')
        exit(1)

  while True:
    # write widgets into framebuffer
    for widget in widgets:
      widget.write_into_fb(fb)

    # copy our virtual buffer with the real one
    fb.swap_buffers()

    # wait for a bit
    time.sleep(refresh_interval)

    # trigger a widget refresh
    for widget in widgets:
      widget.refresh()