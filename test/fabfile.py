"""
This script executes a download/upload tasks for demo purposes

Prereq:
    must have fabric installed
"""

from fabric.api import env
import os, sys
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.realpath('%s/..' % BASE_DIR))
import parallel_sync as psync

@task
def download_urls():
    """ downloads some files """
    urls = ['http://www.nationalgeographic.com/dc/exposure/homepage/photoconfiguration/image/70759_photo_nxqzsecnr7nwui2pbv33cboxp3vu2hmpyjyavf6lo6pvvsfavj3q_850x478.jpg',\
            'http://www.nationalgeographic.com/dc/exposure/homepage/photoconfiguration/image/70867_photo_g2j2wmgshw2nhigkyrhbstxkylvu2hmpyjyavf6lo6pvvsfavj3q_850x478.jpg']
    psync.download('/tmp/images', urls, env=env)



