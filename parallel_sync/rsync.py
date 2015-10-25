import parallel_sync as psync
from parallel_sync import executor
import os
from bunch import Bunch
from multiprocessing import Pool
from functools import partial

def upload(src, dst, creds,\
    tries=3, include=['*'], parallelism=10):
    transfer(src, dst, creds, upstream=True,\
        tries=tries, include=include, parallelism=parallelism)


def download(src, dst, creds,\
    tries=3, include=['*'], parallelism=10):
    transfer(src, dst, creds, upstream=False,\
        tries=tries, include=include, parallelism=parallelism)


def transfer(src, dst, creds, upstream=True,\
    tries=3, include=['*'], parallelism=10):
    """
    @parallelism(default=10): number of parallel processes to use
    """
    if isinstance(creds, dict):
        creds = Bunch(creds)
        if 'key' in creds:
            creds.key = os.path.expanduser(creds.key)
        if 'key_filename' in creds:
            creds.key = os.path.expanduser(creds.key_filename[0])

    cmds = []
    for filter in include:
        cmds.append('find {} -name "{}"'.format(src, filter))

    cmd = ' && '.join(cmds)

    output = ''
    if upstream:
        executor.make_dirs(dst, creds)
        output = executor.local(cmd)
    else:
        executor.make_dirs(dst)
        output = executor.remote(cmd, creds)

    srcs = list(set(output.splitlines()))

    dests = []
    for path in srcs:
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
    pool = Pool(processes=parallelism)
    func = partial(executor._local, None, tries)
    pool.map(func, cmds)
    pool.close()
    pool.join()


def __remove_zip_ext(path):
    """ given a @path, returns the path without the .tar.gz or .gz extension
    """
    if path.endswith('.tar.gz'):
        return path[:-7]
    if path.endswith('.gz'):
        return path[:-3]
    return path

