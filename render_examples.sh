#!/bin/bash

python3 -m fb_dashboard --no-framebuffer --exit --config examples/example1.toml --export-filename examples/example1.toml.png
python3 -m fb_dashboard --no-framebuffer --exit --config examples/example2.toml --export-filename examples/example2.toml.png