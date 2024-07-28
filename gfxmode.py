import os, fcntl, sys

KDSETMODE = 0x4B3A

if __name__ == '__main__':
  tty = sys.argv[1] if len(sys.argv) > 1 else '/dev/tty1'
  mode = int(sys.argv[2]) if len(sys.argv) > 2 else 0x01

  try:
    #https://github.com/OpenRoberta/robertalab-ev3dev/blob/develop/roberta/lab.py
    # KDSETMODE = 0x4B3A, GRAPHICS = 0x01
    tty_fd = os.open(tty, os.O_RDWR)
    fcntl.ioctl(tty_fd, KDSETMODE, mode)
    os.close(tty_fd)
  except Exception as e:
    print(e)