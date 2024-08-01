import os
from io import BytesIO
import mmap
from PIL import Image


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
        num_pixels = self.fb_width * self.fb_height

        if self.fb_bits_per_pixel // 8 == 4:
            # 32-bit color, 8 bits per channel
            buf.write(b"\x00\x00\x00\xff" * num_pixels)
        elif self.fb_bits_per_pixel // 8 == 3:
            # 24-bit color, 8 bits per channel
            buf.write(b"\x00\x00\x00" * num_pixels)
        else:
            raise ValueError("Unsupported bits per pixel")

        buf.seek(0)

        self.virtual_buffer = buf

    def set_pixel(self, x, y, r, g, b, a):
        """
        set a single pixel in the virtual buffer
        """
        if x < 0 or x >= self.fb_width or y < 0 or y >= self.fb_height:
            return

        self.virtual_buffer.seek((y * self.fb_width + x) * self.fb_bits_per_pixel // 8)
        self.virtual_buffer.write(b.to_bytes(1, byteorder="little"))
        self.virtual_buffer.write(g.to_bytes(1, byteorder="little"))
        self.virtual_buffer.write(r.to_bytes(1, byteorder="little"))
        self.virtual_buffer.write(a.to_bytes(1, byteorder="little"))

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
        img = Image.frombytes(
            "RGBA",
            (self.fb_width, self.fb_height),
            self.virtual_buffer.getvalue(),
            "raw",
            "BGRA",
        )
        img.save(path, "PNG")

    def swap_buffers(self):
        """
        'swap' the virtual buffer with the actual framebuffer

        bulk write the virtual buffer to the framebuffer, so that the screen updates in one go
        """
        self.export_png("framebuffer.png")


class LinuxFrameBuffer(FrameBufferBase):
    def __init__(self, fb_name):
        self.fb_name = fb_name

        # get fb resolution
        [fb_w, fb_h] = (
            open("/sys/class/graphics/fb0/virtual_size", "r").read().strip().split(",")
        )
        self.fb_width = int(fb_w)
        self.fb_height = int(fb_h)

        # get bits per pixel
        self.fb_bits_per_pixel = int(
            open("/sys/class/graphics/fb0/bits_per_pixel", "r").read()
        )

        # save the screen resolution
        self.fbpath = "/dev/" + self.fb_name
        self.fbdev = os.open(self.fbpath, os.O_RDWR)

        # use mmap to map the framebuffer to memory
        num_bits = self.fb_width * self.fb_height * self.fb_bits_per_pixel
        self.fb = mmap.mmap(
            self.fbdev,
            num_bits // 8,
            mmap.MAP_SHARED,
            mmap.PROT_WRITE | mmap.PROT_READ,
            offset=0,
        )

        # setup a buffer to draw to
        self.make_buffer()

    def swap_buffers(self):
        """
        'swap' the virtual buffer with the actual framebuffer

        bulk write the virtual buffer to the framebuffer, so that the screen updates in one go
        """
        self.fb.seek(0)
        self.fb.write(self.virtual_buffer.getvalue())
