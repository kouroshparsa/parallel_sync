"""
This module copies files in parallel up or down stream
from or to a remote host
"""
from . import executor
import os
from bunch import Bunch
from multiprocessing.pool import ThreadPool
from functools import partial
from . import compression
import logging
logging.basicConfig(level='INFO')
import hashlib
import shutil
import re

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
            path = creds.key_filename
            if isinstance(path, list):
                path = path[0]
            creds.key = os.path.expanduser(path)

    if upstream:
        srcs = executor.find_files(src, None, include=include, exclude=exclude)
    else:
        srcs = executor.find_files(src, creds, include=include, exclude=exclude)

    if len(srcs) < 1:
        logging.warn('No source files found to transfer.')
        return

    paths = []
    for path in srcs:
        dst_path = path[len(src):]
        if dst_path.startswith('/'):
            dst_path = dst_path[1:]

        if dst.endswith('/'):
            dst = dst[:-1]
        dst_path = os.path.join(dst, dst_path)
        paths.append((path, dst_path))

    transfer_paths(paths, creds, upstream,\
        tries=tries, parallelism=parallelism, extract=extract,\
        validate=validate, additional_params=additional_params)


def __make_dirs(paths, creds, upstream):
    dirs = [os.path.dirname(path[1]) for path in paths]
    if upstream:
        executor.make_dirs(dirs, creds=creds)
    else:
        executor.make_dirs(dirs)


def transfer_paths(paths, creds, upstream=True, tries=3,\
    parallelism=10, extract=False,\
    validate=False, additional_params='-c'):
    """
    @paths: list of tuples of (source_path, dest_path)
    """
    if isinstance(creds, dict):
        creds = Bunch(creds)
        if 'key' in creds:
            creds.key = os.path.expanduser(creds.key)
        if 'key_filename' in creds:
            path = creds.key_filename
            if isinstance(path, list):
                path = path[0]
            creds.key = os.path.expanduser(path)

    __make_dirs(paths, creds, upstream)
    rsync = "rsync {} -e 'ssh"\
            " -o StrictHostKeyChecking=no"\
            " -o ServerAliveInterval=100"\
            " -i {}'".format(additional_params, creds.key)

    cmds = []
    for src, dst in paths:
        cmd = '{} {}@{}:"{}" "{}"'.format(rsync, creds.user, creds.host, src, dst)
        if upstream:
            cmd = '{} "{}" {}@{}:"{}"'.format(rsync, src, creds.user, creds.host, dst)
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
            for _, path in paths:
                if path.endswith('.gz'):
                    cmds.append('gunzip "{}"'.format(path))
            if len(cmds) > 0:
                executor.remote_batch(cmds, creds)
        else:
            cmds = []
            for _, path in paths:
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



def path_match(path, include=[], exclude=[]):
    if include is None:
        include = []
    if exclude is None:
        exclude = []
    for patt in include:
        if not re.match(patt.replace('*', '.*'), path):
            return False

    for patt in exclude:
        if re.match(patt.replace('*', '.*'), path):
            return False

    return True


def copy(src_dir, dst_dir, include=[], exclude=[], parallelism=10,\
    extract=False, validate=False):
    paths = []
    if os.path.isfile(src_dir):
        paths = [(src_dir,)]
    else:
        for root, subdirs, files in os.walk(src_dir):
            for filename in files:
                path = os.path.join(root, filename)
                if path_match(path, include, exclude):
                    x = path[len(src_dir):]
                    if x.startswith('/'):
                        x = x[1:]
                    dst = os.path.join(dst_dir, x)
                    paths.append((path, dst))

    local_copy(paths, parallelism=parallelism,\
        extract=extract, validate=validate)


def _copyfile(src_dst):
    shutil.copyfile(src_dst[0], src_dst[1])

def local_copy(paths, parallelism=10, extract=False, validate=False):
    """
    @paths: list of tuples of (source_path, dest_path)
    """
    for src, dst in paths:
        dst_dir = os.path.dirname(os.path.expanduser(dst))
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

    if len(paths) < 1:
        return

    pool = ThreadPool(processes=parallelism)
    pool.map(_copyfile, paths)
    pool.close()
    pool.join()

    if extract:
        logging.info('File extraction...')
        for _, path in paths:
            if path.endswith('.gz'):
                executor.local_batch('gunzip "{}"'.format(path))

    if validate and len(srcs) > 0:
        logging.info('Checksum validation...')
        func = partial(local_checksum_validator)
        pool.map(func, paths)
        pool.close()
        pool.join()


def local_checksum_validator(paths):
    """
    @paths: list of tuples of (source_path, dest_path)
    """
    for src, dst in paths:
        checksum1 = hashlib.md5(open(src, 'rb').read()).hexdigest()
        checksum2 = hashlib.md5(open(dst, 'rb').read()).hexdigest()
        if checksum1 != checksum2:
            raise Exception('checksum mismatch for\n{}\n{}'.format(src, dst))

