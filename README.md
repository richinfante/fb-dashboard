# fb-dashboard

## Usage

Copy `config.example.ini` -> `config.ini` and edit to your desired configuration.

```bash
# install requirements
pip3 install -r requirements.txt

# set graphics mode for the current screen's tty (usually tty1)
sudo python3 gfxmode.py /dev/tty1 graphics

# run the dashboard
python3 -m fb_dashboard
```

## Basic config with Cloudwatch Dashboards
Config file, may need to customize the widget to the one you want to display. the `widget` is also eval()'ed like the x, y, w, and h variables, so you can dynamically specify the width and height of the image.

```
[widget]
x = 0
y = 0
w = w
h = h
type = CloudWatchMetricImage
widget = {"metrics": [[ "AWS/CloudFront", "Requests", "Region", "Global", "DistributionId", "YOUR_DISTRIBUTION_ID_HERE" ]],"view": "timeSeries","stacked": false,"stat": "Sum","period": 900, "width": w, "height": h,"start": "-PT72H", "end": "P0D", "timezone": "-0400"}
```

## Config Options By Type
- all:
  - `x` - x position on screen
  - `y` - y position on screen
  - `w` - width of the widget
  - `h` - height of the widget
- `CloudWatchMetricImage`
  - `widget` - a JSON string from CloudWatch's metric image export function
  - `aws_profile` - (optional) AWS profile name
  - `aws_region` - (optional) AWS region name
- `Image`
  - `path` - local path, http://, or https:// link to the image
  - `auth_type` - (optional) `basic` (default), or `digest`. Only used if username and password are set.
  - `username` - (optional) auth username
  - `password` - (optional) auth password
- `Clock`
  - `clock_format` - (optional) clock format string, e.g. `%H:%M:%S` or `%I:%M %p`
  - `date_format` - (optional) date format string, e.g. `%Y-%m-%d` or `%A, %B %d, %Y`
  - `timezone` - (optional) e.g. America/New_York
  - `bg_color` - bg color, in hex or `rgb()` format.
  - `fg_color` - bg color, in hex or `rgb()` format.
- `Text` (experimental)
  - `text` - text to display
  - `size` - font size
  - `bg_color` - bg color, in hex or `rgb()` format.
  - `fg_color` - bg color, in hex or `rgb()` format.



## Run at boot

On raspberry pi, `/etc/rc.local` is a pretty easy place to run scripts at boot. Add this line before `exit 0`:

You will likely need to change the username, path to the cloned repo, and any virtual env you might be using. This will run the graphics mode script as root, then run the main script as the normal user.

```bash
python3 /home/rich/aws-dash/gfxmode.py /dev/tty1 1

# if using a virtualenv
sudo -u rich bash -c 'cd /home/rich/fb-dashboard && source env/bin/activate && python3 -m fb_dashboard'
```

If not using a virtual environment you replace the last line above with this:
```bash
# if not using a virtualenv
sudo -u rich bash -c 'python3 cd /home/rich/fb-dashboard && python3 -m fb_dashboard'
```

## Debugging on non-linux system
```
# writes to `framebuffer.png` in current dir
python3 -m fb_dashboard --no-framebuffer
```

## Security
This isn't designed to be used with untrusted data. The config file eval()'s several sections to allow for dynamic configuration. This is by design, so I do not recommend running this as root with untrusted images. Ensure you have the latest versions of the dependencies so they have the latest security patches.