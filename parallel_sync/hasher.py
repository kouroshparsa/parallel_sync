"""
This module is used for hashing files and folders
"""
import md5
import os
from parallel_sync import executor
import subprocess

def get_md5(path, creds=None):
    """
    returns the md5sum of a file or directory
    if creds is not None, then it performs the operation
    on the remote host
    """

    cmd = "find %s -type f -exec md5sum {} \; | awk {'print $1'} | sort | md5sum" % path
    if creds is None:
        hash = executor.local(cmd)
    else:
        hash = executor.remote(cmd, creds)
    return hash[:hash.find(' ')]


