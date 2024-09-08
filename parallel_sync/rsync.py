"""
This module copies files in parallel up or down stream
from or to a remote host
"""
import os
import re
import hashlib
import platform
import subprocess
from multiprocessing.pool import ThreadPool
from functools import partial
import logging
from . import Credential, executor
logging.basicConfig(level='INFO')


def upload(src: str, dst: str, creds: Credential,
    tries: int=1, include: list='*', exclude: list=None,
    parallelism: int=10, extract: bool=False,
    validate: bool=False, additional_params: str='-c'):
    """
    @src, @dst: source and destination directories
    @creds: ssh credentials
    @validate: bool - if True, it will perform a checksum comparison after the operation
    @additional_params: str - additional parameters to pass on to rsync
    """
    __transfer(src, dst, creds, upstream=True,\
        tries=tries, include=include, exclude=exclude, parallelism=parallelism,\
        extract=extract, validate=validate, additional_params=additional_params)


def download(src: str, dst: str, creds: Credential,
    tries: int=1, include: str='*', exclude: list=None,
    parallelism: int=10, extract: bool=False,
    validate: bool=False, additional_params: str='-c'):
    """
    @src, @dst: source and destination directories
    @creds: ssh credentials
    @validate: bool - if True, it will perform a checksum comparison after the operation
    @additional_params: str - additional parameters to pass on to rsync
    """
    __transfer(src, dst, creds, upstream=False,
        tries=tries, include=include, exclude=exclude, parallelism=parallelism, extract=extract,
        validate=validate, additional_params=additional_params)


def __transfer(src: str, dst: str, creds: Credential, upstream: bool=True,
    tries: int=1, include: str='*', exclude: list=None, parallelism: int=10, extract: bool=False,
    validate: bool=False, additional_params: str='-c'):
    """
    @src: str path of a file or folder for source
    @dst: path of a file or folder for destination
    @creds: ssh credentials
    @upstream: bool, whether it is upload or not (False means download)
    @tries: int, how many times to try
    @include: wild card pattern
    @exclude: list of wild card patterns
    @parallelism(default=10): number of parallel processes to use
    @extract: bool - whether to extract tar or zip files after transfer
    @validate: whether to do a checksum validation at the end
    @additional_params: str - additional parameters to pass on to rsync
    """
    if src is None:
        raise ValueError('src cannot be None')
        
    if dst is None:
        raise ValueError('dst cannot be None')
        
    srcs = []
    if upstream and os.path.isfile(src):
        srcs = [src]
    else:
        if upstream: # upload
            folder_srcs, srcs = executor.find_local(src, include=include, exclude=exclude)
        else: # download
            folder_srcs, srcs = executor.find_remote(src, creds, include=include, exclude=exclude)

    folder_dsts = set([__get_dst_path(src, s, dst) for s in folder_srcs if s!=src] + [dst])
    __make_dirs(folder_dsts, creds, upstream)

    if len(srcs) < 1:
        logging.warning('No source files found to transfer.')
        return

    paths = []
    for s_path in srcs:
        paths.append((s_path, __get_dst_path(src, s_path, dst)))

    __transfer_paths(paths, creds, upstream,
        tries=tries, parallelism=parallelism, extract=extract,
        validate=validate, additional_params=additional_params)

def __get_dst_path(src: str, src_path:str, dst_dir: str):
    """
    @src: str, the root of source directory to copy from
    @src_path: str, the full path of file or folder to copy
    @dst_dir: str, the destination folder
    returns the destination full file path
    Example: src=C:/temp/testdir
            src_path=C:/temp/testdir/emptydir
            dst_dir=/tmp/testdir
            returns /tmp/testdir/emptydir

    """
    postfix = src_path[len(src):]
    if len(postfix) < 1: # src must be a file
        postfix = src.replace('\\', '/').split('/')[-1]

    if postfix.startswith('/') or postfix.startswith('\\'):
        postfix = postfix[1:]

    if dst_dir.endswith('/'):
        dst_dir = dst_dir[:-1]
    return f'{dst_dir}/{postfix}'


def __make_dirs(folders: set, creds: Credential, upstream: bool):
    """
    @folders: set of folder paths
    @creds: ssh credentials
    @upstream: bool, whether to upload or downolad
    Creates directories on the remote machine
    """
    if upstream:
        executor.make_dirs_remote(folders, creds=creds)
    else:
        for folder in folders:
            os.makedirs(folder, exist_ok=True)


def __is_rsync_installed():
    """
    returns bool, whether rsync is installed on the local machine or now
    """
    if 'Windows' in platform.system():
        return False

    proc = subprocess.run("which rsync", shell=True, check=False)
    return proc.returncode == 0
    

def __get_transfer_commands(creds: Credential, upstream: bool,
                            paths: list, additional_params: str='-c') -> list:
    """
    @paths: list of tuples of (source_path, dest_path)
        note that source_path can be either local or remote
    @creds: ssh Credentials
    @upstream: bool whether it is upload or download
    @additional_params: str. You can pass additional rsync parameters. The default is just '-c'
    returns a list of commands to be run locally
    """
    rsync = f"rsync {additional_params} -e 'ssh -i {creds.key_filename}' "\
        "-o StrictHostKeyChecking=no -o ServerAliveInterval=100"

    cmds = []
    for src, dst in paths:
        cmd = None
        if upstream and os.path.isdir(src):
            cmd = f'ssh -p {creds.port} {creds.username}@{creds.hostname} -i "{creds.key_filename}" mkdir -p {dst}'

        elif __is_rsync_installed():
            if upstream:
                cmd = f'{rsync} "{src}" {creds.username}@{creds.hostname}:"{dst}" --port {creds.port}'
            else: # download:
                cmd = f'{rsync} {creds.username}@{creds.hostname}:"{src}" "{dst}"'

        else: # then use scp:
            if upstream:
                cmd = f'scp -P {creds.port} -i "{creds.key_filename}" "{src}" {creds.username}@{creds.hostname}:"{dst}"'
            else: # download:
                cmd = f'scp -P {creds.port} -i "{creds.key_filename}" {creds.username}@{creds.hostname}:"{src}" "{dst}"'

        cmds.append(cmd)
    return cmds



def __transfer_paths(paths: list, creds: Credential, upstream: bool=True, tries: int=1,
    parallelism: int=10, extract: bool=False, validate: bool=False, additional_params: str='-c'):
    """
    @paths: list of tuples of (source_path, dest_path)
        note that source_path can be either local or remote
    @creds: ssh Credentials
    @upstream: bool whether it is upload or download
    @tries: int. How many times to try to transfer the file.
        Default is 1. You can specify more then time to retry.
    @parallelism: int. How many processes to evoke to do the file transfer
    @extract: bool, whether after transfering the file it needs to be extracted
    @validate: bool, whether you want to do a checksum validation after the transfer
    @additional_params: str. You can pass additional rsync parameters. The default is just '-c'
    """
    if len(paths) < 1:
        raise ValueError('You did not specify any paths')


    if creds.hostname in ['', None]:
        raise Exception('The host is not specified.')

    # __make_dirs(paths, creds, upstream)
    cmds = __get_transfer_commands(creds, upstream, paths, additional_params)
    pool = ThreadPool(processes=parallelism)
    func = partial(executor.local, tries=tries)
    pool.map(func, cmds)
    pool.close()
    pool.join()

    if validate and len(paths) > 0:
        validate_checksums(creds, upstream, parallelism, paths)

    if extract:
        extract_files(creds, upstream, paths)


def extract_files(creds, upstream, paths):
    """
    :param creds: dictionary
    :param upstream: boolean
    :param paths: list of tuples of (source_path, dest_path)
    """
    logging.info('File extraction...')
    if upstream:  # local=source, remote=dest
        cmds = []
        for _, path in paths:
            if path.endswith('.gz'):
                cmds.append(f'gunzip "{path}"')
        if len(cmds) > 0:
            executor.remote_batch(cmds, creds)

    else:  # local=dest, remote=source
        cmds = []
        for _, path in paths:
            if path.endswith('.gz'):
                cmds.append(f'gunzip "{path}"')
        if len(cmds) > 0:
            executor.local_batch(cmds)


def validate_checksums(creds, upstream, parallelism, paths):
    """
    :param creds: a dictionary with the ssh credentials
    :param upstream: boolean
    :param paths: is a list of two paths: local path and remote path
    if fails, it raises an Exception
    """
    logging.info('Checksum validation...')
    func = partial(checksum_validator, creds)
    # transform paths to be a pair of local and remote paths:
    paths2 = []
    if upstream:  # local=source, remote=dest
        paths2 = [(src, dst) for src, dst in paths]

    else:  # local=dest, remote=source
        paths2 = [(dst, src) for src, dst in paths]

    pool = ThreadPool(processes=parallelism)
    pool.map(func, paths2)
    pool.close()
    pool.join()


def checksum_validator(creds, paths):
    """
    :param creds: a dictionary with the ssh credentials
    :param paths: is a list of two paths: local path and remote path
    if fails, it raises an Exception
    """
    local_path, remote_path = paths
    checksum1 = executor.local(f'md5sum "{local_path}"').split(' ')[0]
    checksum2 = executor.remote(f'md5sum "{remote_path}"', creds).split(' ')[0]
    if checksum1 != checksum2:
        raise Exception('checksum mismatch for %s' % paths)
    logging.info('Verified: filename=%s checksum=%s', os.path.basename(local_path), checksum1)

class CheckSumMismatch(Exception):
    pass

def local_checksum_validator(paths: list):
    """
    @paths: list of tuples of (source_path, dest_path)
    """
    for src, dst in paths:
        checksum1 = hashlib.md5(open(src, 'rb').read()).hexdigest()
        checksum2 = hashlib.md5(open(dst, 'rb').read()).hexdigest()
        if checksum1 != checksum2:
            raise CheckSumMismatch(f'checksum mismatch for\n{src}\n{dst}')
