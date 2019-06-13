# Copyright (c) 2017 Adafruit Industries
# Author: Tony DiCola & James DeVito
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import time, os, signal, sys

import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from jetbot.utils.utils import *
import jetbot.utils.teensyadc as teensyadc

import subprocess

# 128x32 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_32(rst=None, i2c_bus=1, gpio=1) # setting gpio to 1 is hack to avoid platform detection

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Load default font.
try:
    font = ImageFont.load('/home/jetbot/jetbot/jetbot/fonts/slkscr.pil')
    lineheight = 8
    padding = 0
except:
    font = ImageFont.load_default()
    lineheight = 8
    padding = -2

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

disploop = 0

def draw_blank(Code, Frame):
    global draw
    global disp
    global image
    global width
    global height
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    disp.image(image)
    disp.display()
    quit()

signal.signal(signal.SIGTERM, draw_blank)

while True:

    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)

    # Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
    cmd = "top -bn1 | grep load | awk '{printf \"%.0f\", $(NF-2)}'"
    CPU = subprocess.check_output(cmd, shell = True )
    CPU = str(CPU.decode('utf-8'))

    cmd = "free -m | awk 'NR==2{printf \"%.0f\", $3*100/$2 }'"
    MemUsage = subprocess.check_output(cmd, shell = True )
    MemUsage = str(MemUsage.decode('utf-8'))

    cmd = "df -h | awk '$NF==\"/\"{printf \"%s\", $5}'"
    Disk = subprocess.check_output(cmd, shell = True )
    Disk = str(Disk.decode('utf-8')).rstrip('%')

    cmd = "cat /sys/devices/virtual/thermal/thermal_zone*/temp | head -n4 | awk -v max=0 '{if ($1 > max){ max = $1; }} END {printf \"%.0f\", max/1000}'"
    Temperature = subprocess.check_output(cmd, shell = True )
    Temperature = str(Temperature.decode('utf-8'))

    Battery = "%.1f" % teensyadc.read_batt_volts()

    DualshockMac = get_dualshock4_mac()

    linecnt = 0

    ethIp = get_ip_address('eth0')
    wifiIp = get_ip_address('wlan0')
    wifiSsid = None
    if wifiIp != None:
        wifiSsid = get_wifi_ssid()

    # Draw text
    if ethIp != None:
        draw.text((x, top + (lineheight * linecnt)),   "ETH: " + str(ethIp),  font=font, fill=255)
        linecnt += 1
    if wifiIp != None:
        if (disploop % 4) < 2 and wifiSsid != None:
            draw.text((x, top + (lineheight * linecnt)),   "WIFI: " + str(wifiSsid), font=font, fill=255)
        else:
            draw.text((x, top + (lineheight * linecnt)),   "WIFI: " + str(wifiIp), font=font, fill=255)
        linecnt += 1

    quickstats = "C:" + CPU
    if (disploop % 4) < 2:
        quickstats += "  M:" + MemUsage
    else:
        quickstats += "  D:" + Disk
    quickstats += "  T:" + Temperature + "  B:" + Battery
    draw.text((x, top + (lineheight * linecnt)), quickstats, font=font, fill=255)
    linecnt += 1

    if DualshockMac != None:
        draw.text((x, top + (lineheight * linecnt)), "DS4: " + DualshockMac, font=font, fill=255)
        linecnt += 1

    # Display image.
    disp.image(image)
    disp.display()
    time.sleep(1)
    disploop += 1
