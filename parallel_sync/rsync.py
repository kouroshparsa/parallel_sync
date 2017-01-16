"""
This module copies files in parallel up or down stream
from or to a remote host
"""
from parallel_sync import executor
import os
from bunch import Bunch
from multiprocessing.pool import ThreadPool
from functools import partial
import compression
import logging
logging.basicConfig(level='INFO')

def upload(src, dst, creds,\
    tries=3, include=[], exclude=[], parallelism=10, extract=False,\
    validate=False, additional_params='-c'):
    """
    @src, @dst: source and destination directories
    @creds: dict of credentials
    @validate: bool - if True, it will perform a checksum comparison after the operation
    @additional_params: str - additional parameters to pass on to rsync
    """
    transfer(src, dst, creds, upstream=True,\
        tries=tries, include=include, exclude=exclude, parallelism=parallelism,\
        extract=extract, validate=validate, additional_params=additional_params)


def download(src, dst, creds,\
    tries=3, include=[], exclude=[], parallelism=10, extract=False,\
    validate=False, additional_params='-c'):
    """
    @src, @dst: source and destination directories
    @creds: dict of credentials
    @validate: bool - if True, it will perform a checksum comparison after the operation
    @additional_params: str - additional parameters to pass on to rsync
    """
    transfer(src, dst, creds, upstream=False,\
        tries=tries, include=include, exclude=exclude, parallelism=parallelism, extract=extract,\
        validate=validate, additional_params=additional_params)


def transfer(src, dst, creds, upstream=True,\
    tries=3, include=[], exclude=[], parallelism=10, extract=False,\
    validate=False, additional_params='-c'):
    """
    @src, @dst: source and destination directories
    @creds: dict of credentials
    @extract: boolean - whether to extract tar or zip files after transfer
    @parallelism(default=10): number of parallel processes to use
    @additional_params: str - additional parameters to pass on to rsync
    """
    if isinstance(creds, dict):
        creds = Bunch(creds)
        if 'key' in creds:
            creds.key = os.path.expanduser(creds.key)
        if 'key_filename' in creds:
            creds.key = os.path.expanduser(creds.key_filename[0])

    if upstream:
        srcs = executor.find_files(src, None, include=include, exclude=exclude)
    else:
        srcs = executor.find_files(src, creds, include=include, exclude=exclude)

    if len(srcs) < 1:
        logging.warn('No source files found to transfer.')
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


    rsync = "rsync {} -e 'ssh"\
            " -o StrictHostKeyChecking=no"\
            " -o ServerAliveInterval=100"\
            " -i {}'".format(additional_params, creds.key)

    cmds = []
    for ind, path in enumerate(srcs):
        cmd = "{} {}@{}:{} {}".format(rsync, creds.user, creds.host, path, dests[ind])
        if upstream:
            cmd = "{} {} {}@{}:{}".format(rsync, path, creds.user, creds.host, dests[ind])
        cmds.append(cmd)

    pool = ThreadPool(processes=parallelism)
    func = partial(executor._local, None, tries)
    pool.map(func, cmds)
    pool.close()
    pool.join()

    if extract:
        logging.info('File extraction...')
        if upstream:
            cmds = []
            for path in dests:
                if path.endswith('.gz'):
                    cmds.append('gunzip "{}"'.format(path))
            if len(cmds) > 0:
                executor.remote_batch(cmds)
        else:
            cmds = []
            for path in srcs:
                if path.endswith('.gz'):
                    cmds.append('gunzip "{}"'.format(path))
            if len(cmds) > 0:
                executor.local_batch(cmds)

    if validate and len(srcs) > 0:
        logging.info('Checksum validation...')
        func = partial(checksum_validator, creds)
        paths = []
        if upstream:
            paths = [(path, dests[ind]) for ind, path in enumerate(srcs)]
        else:
            paths = [(dests[ind], path) for ind, path in enumerate(srcs)]

        pool.map(func, paths)
        pool.close()
        pool.join()


def checksum_validator(creds, paths):
    local_path, remote_path = paths
    checksum1 = executor.local('md5sum "{}"'.format(local_path)).split(' ')[0]
    checksum2 = executor.remote('md5sum "{}"'.format(remote_path), creds=creds).split(' ')[0]
    if checksum1 != checksum2:
        raise Exception('checksum mismatch for %s' % paths)


