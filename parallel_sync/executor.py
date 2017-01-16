"""
This is the central module that does common operations
either locally or remotely.
It can do operations in parallel batches as well
"""
import os
import sys
from multiprocessing.pool import ThreadPool
from functools import partial
import logging
import subprocess
import traceback
logging.basicConfig(level='INFO')
BASE_DIR = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.realpath("{}/..".format(BASE_DIR)))
import paramiko
from bunch import Bunch
import Queue
import re
SSH_TIMEOUT = int(os.getenv('SSH_TIMEOUT', '10'))

def run(cmds, creds=None, curr_dir=None, parallelism=10):
    """ runs commands on the remote machine in parallel
    if there is only one command, then the output is returned
    @cmds: list of commands to run in parallel
    @curr_dir(optional): the currenct directory to run t he command from
    @parallelism: int - how many commands to run at the same time
    """
    if creds is None:
        if isinstance(cmds, list):
            local_batch(cmds,\
                         curr_dir=curr_dir,\
                         parallelism=parallelism)
        else:
            return _local(curr_dir, 1, cmds)
    else:
        if isinstance(cmds, list):
            remote_batch(cmds, creds,\
                         curr_dir=curr_dir,\
                         parallelism=parallelism)
        else:
            return remote(cmds, creds,\
                          curr_dir=curr_dir)


def remote_batch(cmds, creds, curr_dir=None, parallelism=10):
    """ runs commands on the remote machine in parallel
    @cmds: list of commands to run in parallel
    @curr_dir(optional): the currenct directory to run t he command from
    @parallelism: int - how many commands to run at the same time
    """
    cmd_q = Queue.Queue()
    for cmd in cmds:
        cmd_q.put(cmd)

    if isinstance(creds, dict):
        creds = Bunch(creds)

    client = paramiko.SSHClient()
    args = {'hostname':creds.host, 'username':creds.user}
    if 'key_filename' in creds:
        creds.key = os.path.expanduser(creds.key_filename[0])
    if 'key' in creds:
        key_path = os.path.expanduser(creds.key)
        key = paramiko.RSAKey.from_private_key_file(key_path)
        args['pkey'] = key
    if 'password' in creds:
        args['password'] = creds.password

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    args['timeout'] = SSH_TIMEOUT
    client.connect(**args)

    while not cmd_q.empty():
        cmd_list = []
        for _ in range(parallelism):
            if cmd_q.empty():
                break
            cmd_list.append(cmd_q.get())

        cmd = '(%s)' % ') & ('.join(cmd_list)
        if curr_dir is not None:
            make_dirs(curr_dir, creds)
            cmd = 'cd "%s" && %s' % (curr_dir, cmd)

        logging.info(cmd)
        stdout = client.exec_command(cmd)[1]
        output = stdout.read()
        logging.info(output)
    client.close()


def remote(cmd, creds, curr_dir=None):
    """
    runs a command on a remote machine and returns output
    """
    if isinstance(creds, dict):
        creds = Bunch(creds)

    client = paramiko.SSHClient()
    args = {'hostname':creds.host, 'username':creds.user}
    if 'key_filename' in creds:
        creds.key = os.path.expanduser(creds.key_filename[0])
    if 'key' in creds:
        key_path = os.path.expanduser(creds.key)
        key = paramiko.RSAKey.from_private_key_file(key_path)
        args['pkey'] = key
    if 'password' in creds:
        args['password'] = creds.password

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    args['timeout'] = SSH_TIMEOUT
    client.connect(**args)
    if curr_dir is not None:
        make_dirs(curr_dir, creds)
        cmd = 'cd "%s" && %s' % (curr_dir, cmd)
    stdout, stderr = client.exec_command(cmd)[1:3]
    output = stdout.read()
    err = stderr.read()
    client.close()
    if len(err) > 0:
        raise Exception(err)
    return output


def local_batch(cmds, curr_dir=None, tries=1, parallelism=10):
    """ runs a command on the local machine
    @cmds: list of commands to run
    @curr_dir(optional): the currenct directory to run t he command from
    @tries: int - number of times to try the command
    """
    make_dirs(curr_dir)
    pool = ThreadPool(processes=parallelism)
    func = partial(_local, curr_dir, tries)
    pool.map(func, cmds)
    pool.close()
    pool.join()


def local(cmd):
    """ runs a command locally """
    return _local(None, 1, cmd)


def _local(curr_dir, tries, cmd):
    """ runs a command on the local machine
    @cmd: command to run
    @curr_dir(optional): the currenct directory to run t he command from
    @tries: int - number of times to try the command
    """
    if curr_dir is not None:
        make_dirs(curr_dir)
        cmd = 'cd "%s" && %s' % (curr_dir, cmd)

    for count in range(tries):
        logging.info(cmd)
        proc = subprocess.Popen(cmd, shell=True,\
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = proc.communicate()
        if proc.returncode == 0:
            return output
        logging.warn('Command failed: %s', cmd)
        logging.error(err)
        logging.info('Reattempt %s', count + 1)
    raise Exception('The following command failed: %s' % cmd)


def delete_dir(path, creds=None):
    """ deletes a directory """
    run('rm -rf {}'.format(path), creds=creds)


def delete_files(start_dir, creds=None, include=[], exclude=[]):
    """
    deletes files on the local or remote host
    @start_dir: start directory
    @creds: dictionary of credentials.
        if None, the directories are created locally
        otherwise they will be created on the remote host
    @include: list of patterns of files to include
    """
    cmds = []
    for path in find(start_dir, creds, include=include, exclude=exclude, ftype='f'):
        cmds.append('rm "{}"'.format(path))
    if len(cmds) > 0:
        local_batch(cmds)


def make_dirs(dirs, creds=None):
    """
    @dirs: list of directory paths to create
    @creds: dictionary of credentials.
        if None, the directories are created locally
        otherwise they will be created on the remote host
    """
    if creds is None:
        if not isinstance(dirs, list):
            dirs = [dirs]

        for dir_path in dirs:
            if not os.path.exists(dir_path):
                logging.info('creating %s', dir_path)
                os.makedirs(dir_path)
    else:
        cmd = 'mkdir -p {}'.format(dirs)

        if isinstance(dirs, list):
            cmd = '" && mkdir -p "'.join(dirs)
            cmd = 'mkdir -p "{}"'.format(cmd)
        logging.info(cmd)
        remote(cmd, creds)


def find_dirs(start_dir, creds, include=[], exclude=[]):
    """ returns a list of directories """
    return find(start_dir, creds, include=[], exclude=exclude, ftype='d')


def find_files(start_dir, creds, include=[], exclude=[]):
    """ returns a list of files """
    return find(start_dir, creds, include=include, exclude=exclude, ftype='f')


def __make_patterns(patterns):
    res = []
    for pat in patterns:
        if '*' in pat:
            res.append('.*/{}/?$'.format(re.escape(pat).replace('\*', '.*')))
        else:
            res.append('.*/{}/'.format(re.escape(pat)))
    return res


def find(start_dir, creds, include=[], exclude=[], ftype='f'):
    """
    @exclude: list of wild card patterns
    """
    cmd = 'find "{}" -type {}'.format(start_dir, ftype)
    output = ''
    if creds is None:
        output = local(cmd)
    else:
        output = remote(cmd, creds)

    include2 = __make_patterns(include)
    exclude2 = __make_patterns(exclude)
    paths = []
    for path in output.splitlines():
        skipit = False
        if len(include2) > 0:
            skipit = True

        for pat in include2:
            if re.match(pat, path[len(start_dir):]):
                skipit = False
                break

        if skipit:
            continue

        for pat in exclude2:
            if re.match(pat, path[len(start_dir):]):
                skipit = True
                break

        if not skipit:
            paths.append(path)
    return paths


def path_exists(path, creds=None):
    """ returns boolean whether the path exists """
    if creds is None:
        return os.path.exists(path)
    else:
        try:
            cmd = 'ls {}'.format(path)
            print remote(cmd, creds)
            return True
        except Exception as ex:
            if not 'cannot access' in str(ex):
                traceback.print_exc()
            return False


def is_file(path, creds=None):
    """
    @path: string
    returns a boolean
    """
    res = run(['if [ -f "{}" ]; then echo "true";fi'.format(path)], creds=creds)
    return res != None and len(res) > 0

