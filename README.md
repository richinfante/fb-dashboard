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

## Basic config with Cloudwatch Dashboards
Config file, may need
```
[widget]
x = 0
y = 0
w = w
h = h
type = CloudWatchMetricImage
widget = {"metrics": [[ "AWS/CloudFront", "Requests", "Region", "Global", "DistributionId", "YOUR_DISTRIBUTION_ID_HERE" ]],"view": "timeSeries","stacked": false,"stat": "Sum","period": 900, "width": w*2, "height": h*2,"start": "-PT72H", "end": "P0D", "timezone": "-0400"}
```

## Run at boot

On raspberry pi, `/etc/rc.local` is a pretty easy place to run scripts at boot. Add this line before `exit 0`:

You will likely need to change the username, path to the cloned repo, and any virtual env you might be using. This will run the graphics mode script as root, then run the main script as the normal user.

```bash
python3 /home/rich/aws-dash/gfxmode.py /dev/tty1 1

# if using a virtualenv
sudo -u rich bash -c 'cd /home/rich/aws-dash && source env/bin/activate && python3 dash.py'
```

If not using a virtual environment you replace the last line above with this:
```bash
# if not using a virtualenv
sudo -u rich python3 /home/rich/aws-dash/dash.py
```

## Debugging on non-linux system
```
# writes to `framebuffer.png` in current dir
python3 dash.py --no-framebuffer
```
