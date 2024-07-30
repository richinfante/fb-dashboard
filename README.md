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
## Basic use with AWS
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

## Debugging on non-linux system
```
# writes to `framebuffer.png` in current dir
python3 dash.py --no-framebuffer
```
