import configparser
import boto3
import requests
import mmap
import os
from io import BytesIO
from PIL import Image
import random
import time
import fcntl
from requests.auth import HTTPDigestAuth, HTTPBasicAuth

class FrameBuffer:
  def __init__(self, fb_name):
    self.fb_name = fb_name

    print('init fb')

    # get fb resolution
    [fb_w, fb_h] = open("/sys/class/graphics/fb0/virtual_size", "r").read().strip().split(",")
    self.fb_width = int(fb_w)
    self.fb_height = int(fb_h)

    # get bits per pixel
    self.fb_bits_per_pixel = int(open("/sys/class/graphics/fb0/bits_per_pixel", "r").read())

    # save the screen resolution
    self.fbpath = '/dev/' + self.fb_name
    self.fbdev = os.open(self.fbpath, os.O_RDWR)

    print('mmap fb')

    # use mmap to map the framebuffer to memory
    num_bits = self.fb_width*self.fb_height*self.fb_bits_per_pixel
    self.fb = mmap.mmap(self.fbdev, num_bits//8, mmap.MAP_SHARED, mmap.PROT_WRITE|mmap.PROT_READ, offset=0)

    print('make buffer')

    self.make_buffer()
    print('done')

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
    self.widget = config['widget']
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

config = configparser.RawConfigParser()
config.read('config.ini')

plugins = {
  'Image': ImageWidget,
  'CloudWatchMetricImage': CloudWatchImageWidget
}

fb = FrameBuffer('fb0')

widgets = []

for section in config.sections():
  section_name = str(section)
  if section_name.startswith('widget'):
    kind = config[section]['type']
    x = int(eval(config[section]['x'], {'w': fb.fb_width, 'h': fb.fb_height}))
    y = int(eval(config[section]['y'], {'w': fb.fb_width, 'h': fb.fb_height}))
    width = int(eval(config[section]['w'], {'w': fb.fb_width, 'h': fb.fb_height}))
    height = int(eval(config[section]['h'], {'w': fb.fb_width, 'h': fb.fb_height}))

    raw_config = {k: v for (k,v) in config[section].items()}

    print(f'Creating widget of type {kind} at ({x}, {y}) with size ({width}, {height})')

    if kind in plugins:
      widget = plugins[kind](x, y, width, height, raw_config)
      widgets.append(widget)
    else:
      print(f'Unknown widget type: {kind}')
      exit(1)


# for x in range(0, 255):
#   for y in range(0, 255):
#     fb.set_pixel(255 + x, y, random.randrange(0, 255), random.randrange(0, 255), random.randrange(0, 255), 255)

# img = ImageWidget(0, 0, 256, 256, 'image.jpg')
# img.write_into_fb(fb)

while True:
  for widget in widgets:
    widget.write_into_fb(fb)

  print('swap')
  fb.swap_buffers()
  time.sleep(60)
  print('refresh widgets')
  for widget in widgets:
    widget.refresh()