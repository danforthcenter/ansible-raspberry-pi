#!/usr/bin/python

import socket
import json
import subprocess
import os
import numpy as np

from datetime import datetime
from contextlib import contextmanager


# Function to switch directories so as to make tarballing a little easier.
@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


# Platform-independent method to get the ip of the current host.
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 0))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def get_position(ip):
    postable = np.loadtxt("/home/pi/pi-id.txt", dtype=np.dtype('str'))
    ip = str(ip)
    posrow = postable[postable[:, 1] == ip]
    position = posrow[0, 0]
    return position


def get_temp():
    tempdata = str(subprocess.getoutput('sudo /home/pi/temper/temper.py'))
    tempsplit = tempdata.split()
    tempusb = tempsplit[6]
    tempprobe = tempsplit[9]
    return tempusb, tempprobe


def get_time():
    now = datetime.now()
    date = now.strftime("%Y-%m-%d-%H-%M")
    return date


# Make the medata for the current Raspberry Pi Camera.
def make_metadata(ip, position, date, tempusb, tempprobe):
    metadata = {}

    metadata['ip'] = ip

    metadata['position'] = position

    metadata['datetime'] = date

    metadata['temperature-usb'] = tempusb

    metadata['temperature-probe'] = tempprobe

    return metadata


# Getting the image directory for all of the rPIs. Should become a passable parameter.
temp_dir = os.path.join("/home", "pi", "tempdata")
prev_dir = os.getcwd()
# Switching into the directory where the folders and tarballs exist.

# For multi-platform ip getting
ip = get_ip()
position = get_position(ip)
date = get_time()
tempusb, tempprobe = get_temp()
filename = str(temp_dir)+'/tempdata_'+str(date)+'_'+str(ip)+'_'+str(position)

metadata = make_metadata(ip, position, date, tempusb, tempprobe)
json_filename = filename + ".json"
with open(json_filename, "w") as fp:
    json.dump(metadata, fp, sort_keys=True, indent=4)
