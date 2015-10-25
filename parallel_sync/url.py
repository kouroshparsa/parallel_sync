"""
This module manages file operations such as parallel download
"""
import os
import sys
from multiprocessing import Pool
from functools import partial
import logging
BASE_DIR = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.realpath("{}/..".format(BASE_DIR)))
from os.path import expanduser
import re
import zipper
from parallel_sync import executor
TIMEOUT = 40

def __remove_zip_ext(path):
    """ given a @path, returns the path without the .tar.gz or .gz extension
    """
    if path.endswith('.tar.gz'):
        return path[:-7]
    if path.endswith('.gz'):
        return path[:-3]
    if path.endswith('.zip'):
        return path[:-4]
    return path


def url_to_filename(url):
    filename = os.path.basename(url).strip()
    if filename.endswith('?'):
        filename = filename[:-1]
    return filename


def download(target_dir, urls, extract=False,\
    parallelism=10, overwrite=True, creds=None, tries=3):
    """ downloads large files either locally or on a remote machine
    @target_dir: where to download to
    @urls: a list of urls
    @extract: boolean - whether to gunzip after download
    @parallelism(default=10): number of parallel processes to use
    @overwrite: boolean - whether to overwrite the file if it exists
    @creds: dictionary with credentials
        if None, it will download locally
        if not None, then wget command will be run on a remote host
    """
    if isinstance(urls, str):
        urls = [urls]

    if not isinstance(urls, list):
        raise Exception('Expected a list of urls. Received %s' % urls)

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    if creds is None:
        local_download(target_dir, urls, extract=extract,\
            parallelism=parallelism, overwrite=overwrite, tries=tries)
    else:
        remote_download(target_dir, urls, creds, extract=extract,\
            parallelism=parallelism, overwrite=overwrite, tries=tries)
 

def remote_download(target_dir, urls, creds, extract=False,\
    parallelism=10, overwrite=True, tries=3):
    if isinstance(urls, str):
        urls = [urls]

    cmds = []
    for _url in urls:
        filename = url_to_filename(_url)
        file_path = os.path.join(target_dir, filename)
        cmds.append('wget -O "{}" -t {} -T {} -q "{}"'.format(file_path, tries, TIMEOUT, _url))
    executor.remote_batch(cmds, creds, parallelism=parallelism, curr_dir=target_dir)


def local_download(target_dir, urls, extract=False,\
    parallelism=10, overwrite=True, tries=3):
    if isinstance(urls, str):
        urls = [urls]

    cmds = []
    for _url in urls:
        filename = url_to_filename(_url)
        file_path = os.path.join(target_dir, filename)
        cmds.append('wget -O "{}" -t {} -T {} -q "{}"'.format(file_path, tries, TIMEOUT, _url))
    executor.local_batch(cmds, parallelism=parallelism, curr_dir=target_dir)





