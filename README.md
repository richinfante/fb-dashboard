# fb-dashboard

## Usage

Copy `config.example.ini` -> `config.ini` and edit to your desired configuration.

```bash
# install requirements
pip3 install -r requirements.txt

# set graphics mode for the current screen's tty (usually tty1)
sudo python3 gfxmode.py /dev/tty1 graphics

# run the dashboard
python3 dash.py
```

## Debugging on non-linux system
```
# writes to `framebuffer.png` in current dir
python3 dash.py --no-framebuffer
```