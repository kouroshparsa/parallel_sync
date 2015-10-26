"""
This module is used for hashing files and folders
"""
from parallel_sync import executor

def get_md5(path, creds=None):
    """
    returns the md5sum of a file or directory
    if creds is not None, then it performs the operation
    on the remote host
    """

    cmd = "find %s -type f -exec md5sum {} \\; | awk {'print $1'} | sort | md5sum" % path
    hash_val = ''
    if creds is None:
        hash_val = executor.local(cmd)
    else:
        hash_val = executor.remote(cmd, creds)
    return hash_val[:hash_val.find(' ')]


