#!/usr/bin/python3

import os


def takePhoto():
    os.system("fswebcam -r 640x480 --jpeg 85 -D 1 shot.jpg > photo.log 2>&1")

    return 'shot.jpg'

def shootVideo():
    os.system("ffmpeg -t 10 -f v4l2 -framerate 25 -video_size 640x80 -i /dev/video0 video.mkv > video.log 2>&1")

    return 'video.mkv'