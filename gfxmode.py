import os, fcntl, sys

KDSETMODE = 0x4B3A

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print('Usage: gfxmode.py /dev/ttyX text|graphics' % sys.argv[0])
    sys.exit(1)

  # tty to set graphics mode on
  tty = sys.argv[1]

  # mode to set tty to
  if sys.argv[2] == 'text':
    mode = 0
  elif sys.argv[2] == 'graphics':
    mode = 1
  else:
    mode = int(sys.argv[2])

  try:
    #https://github.com/OpenRoberta/robertalab-ev3dev/blob/develop/roberta/lab.py
    # KDSETMODE = 0x4B3A, GRAPHICS = 0x01
    tty_fd = os.open(tty, os.O_RDWR)
    fcntl.ioctl(tty_fd, KDSETMODE, mode)
    os.close(tty_fd)
  except Exception as e:
    print(e)