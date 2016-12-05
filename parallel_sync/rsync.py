"""
This module copies files in parallel up or down stream
from or to a remote host
"""
from parallel_sync import executor
import os
from bunch import Bunch
from multiprocessing import Pool
from functools import partial
import signal
import compression

def upload(src, dst, creds,\
    tries=3, include=None, parallelism=10, extract=False):
    transfer(src, dst, creds, upstream=True,\
        tries=tries, include=include, parallelism=parallelism, extract=extract)


def download(src, dst, creds,\
    tries=3, include=None, parallelism=10, extract=False):
    transfer(src, dst, creds, upstream=False,\
        tries=tries, include=include, parallelism=parallelism, extract=extract)


def transfer(src, dst, creds, upstream=True,\
    tries=3, include=None, parallelism=10, extract=False):
    """
    @extract: boolean - whether to extract tar or zip files after transfer
    @parallelism(default=10): number of parallel processes to use
    """
    if isinstance(creds, dict):
        creds = Bunch(creds)
        if 'key' in creds:
            creds.key = os.path.expanduser(creds.key)
        if 'key_filename' in creds:
            creds.key = os.path.expanduser(creds.key_filename[0])

    if upstream:
        srcs = executor.find_files(src, None, include=include)
    else:
        srcs = executor.find_files(src, creds, include=include)

    if len(srcs) < 1:
        print('No source files found to transfer.')
        return

    src_dirs = set([os.path.dirname(path) for path in srcs])
    dst_dirs = [path.replace(src, dst) for path in src_dirs]
    dst_dirs = [path for path in dst_dirs if path not in ['', '/']]

    if upstream:
        executor.make_dirs(dst_dirs, creds=creds)
    else:
        executor.make_dirs(dst_dirs)

    dests = []
    for path in srcs:
        if path[:len(src)].endswith('/'):
            path = os.path.join(dst, path[len(src):])
        else:
            path = os.path.join(dst, path[len(src) + 1:])
        dests.append(path)


    rsync = "rsync -raz -e 'ssh"\
            " -o StrictHostKeyChecking=no"\
            " -o ServerAliveInterval=100"\
            " -i {}'".format(creds.key)

    cmds = []
    for ind, path in enumerate(srcs):
        cmd = "{} {}@{}:{} {}".format(rsync, creds.user, creds.host, path, dests[ind])
        if upstream:
            cmd = "{} {} {}@{}:{}".format(rsync, path, creds.user, creds.host, dests[ind])
        cmds.append(cmd)
    pool = Pool(parallelism, init_worker)
    func = partial(executor._local, None, tries)
    pool.map(func, cmds)
    pool.close()
    pool.join()
    if extract:
        compression.extract(dst, creds=creds)

def init_worker():
    """ use this initializer for process Pools to allow keyboard interrupts """
    signal.signal(signal.SIGINT, signal.SIG_IGN)

