#!/usr/bin/python
import time
import picamera2
import socket
import json
import subprocess
import os
import tarfile
import shutil
import numpy as np

from fractions import Fraction
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


# Make the medata for the current Raspberry Pi Camera.
def make_metadata(experiment, ip, position, tempusb, tempprobe):
    metadata = {}
    metadata['experiment'] = {
        "experiment": experiment
        }
    metadata['fixed_camera_data'] = {
        "ip_address": ip,
        "position": position
    }

    metadata['temperature'] = {
        "temp_usb": tempusb,
        "temp_probe": tempprobe
    }

    return metadata


# Here begins the proper process of taking the pictures
with picamera2.Picamera2() as camera:
    # Getting the image directory for all of the rPIs. Should become a 
    # passable parameter.
    image_dir = os.path.join("/home", "pi", "images")
    prev_dir = os.getcwd()
    # Switching into the directory where the folders and tarballs exist.
    with cd(image_dir):
        # Getting the current timestamp
        now = datetime.now()
        now_utc = datetime.utcnow()
        date = now.strftime("%Y-%m-%d")
        hour = now.strftime("%Y-%m-%d-%H")
        minute = now.strftime("%Y-%m-%d-%H-%M")
        # Full path directories.
        date_directory = os.path.join(image_dir, now.strftime("%Y-%m-%d"))
        hour_directory = os.path.join(date_directory, now.strftime("%Y-%m-%d-%H"))
        # Creating directories if they do not exist.
        if not os.path.exists(date_directory):
            os.makedirs(date_directory)
            # Hour directory will not exist for time point IF the date
            # directory does not exist.
            os.makedirs(hour_directory)
        elif not os.path.exists(hour_directory):
            os.makedirs(hour_directory)

        # For multi-platform ip getting
        ip = get_ip()
        position = get_position(ip)
        tempusb, tempprobe = get_temp()
        # Making the filename for the capture of the image.

        ext = "jpg"
        now = now.strftime("%Y-%m-%d-%H-%M")
        filename = str(ip)+"_pos-"+position+"_"+minute+".jpg"
        print(filename)
        filename = os.path.join(hour_directory, filename)
        camera_config = camera.create_still_configuration(main={"size": (3280, 2464)})
        camera.configure(camera_config)
        camera.start()
        camera.set_controls({"ExposureTime": 3000, "AnalogueGain": 0.6})
        camera.set_controls({"AeEnable": False})
        camera.set_controls({"AwbEnable": False})
        camera.set_controls({"ColourGains": (1.5, 1.5)})
        camera.capture_file(filename)
        controls = camera.capture_metadata()
        camera.stop()
        print("Captured %s" % filename)

        # Getting all the metadata that will be going into the json file.
        metadata_name = filename[:-4]
        experiment = "EXPERIMENTNAME"
        metadata = make_metadata(experiment, ip, position, tempusb,
                                 tempprobe)
        metadata.update({'camera_metadata': controls})
        json_filename = metadata_name + ".json"
        json_filename = os.path.join(hour_directory, json_filename)
        with open(json_filename, "w") as fp:
            json.dump(metadata, fp, sort_keys=True, indent=4)

        # Creating directory structure tar
        dir_join = str(ip)+"_"+hour
        with tarfile.open(dir_join+".tar", "w") as tar:
            tar.add(date_directory, arcname=date)
        shutil.rmtree(date_directory)
