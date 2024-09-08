"""
This is the central module that does common operations
either locally or remotely.
It can do operations in parallel batches as well
"""
import signal
import re
import pathlib
import logging
import subprocess
from six import string_types
import paramiko
from . import Credential
logging.basicConfig(level='INFO')

from queue import Queue


def init_worker():
    """ use this Pool initializer to allow keyboard interruption """
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def remote(cmd: str, creds: Credential, curr_dir: str=None):
    """ runs commands on the remote machine in parallel
    @cmd: str, command to run on remote machine
    @creds: ssh credentials
    @curr_dir(optional): the currenct directory to run the command from
    returns the output as string
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(**creds.__dict__)
    if curr_dir is not None:
        make_dirs_remote({curr_dir}, creds)
        cmd = f'cd "{curr_dir}"; {cmd}'

    logging.debug(cmd)
    _, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status != 0:
        raise Exception('Failed to download a file\n%s\n%s' % (stdout.read().encode('utf-8'), stderr.read().encode('utf-8')))

    client.close()
    return stdout.read()


def run_remote_batch(cmds: list, creds: Credential, curr_dir: str=None, parallelism: int=10):
    """ runs commands on the remote machine in parallel
    @cmds: list of commands to run in parallel
    @creds: ssh credentials
    @curr_dir(optional): the currenct directory to run the command from
    @parallelism: int - how many commands to run at the same time
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(**creds.__dict__)
    except TimeoutError:
        raise Exception(f"Failed to connect to {creds.hostname}. Attempt timed out.")
    
    ind = 0
    while ind <len(cmds):
        cmd = '(%s)' % ') & ('.join(cmds[ind:ind+parallelism])
        if curr_dir is not None:
            make_dirs_remote({curr_dir}, creds)
            cmd = f'cd "{curr_dir}"; {cmd}'

        logging.debug(cmd)
        _, stdout, stderr = client.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            raise Exception('Failed to download a file\n%s\n%s' % (stdout.read().encode('utf-8'), stderr.read().encode('utf-8')))

        ind += parallelism
    client.close()


def local(cmd: str, tries: int=1):
    """ runs a command on the local machine
    @cmd: command to run
    @tries: int - number of times to try the command
    """
    for count in range(tries):
        logging.debug(cmd)
        proc = subprocess.Popen(cmd, shell=True,\
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = proc.communicate()
        if proc.returncode == 0:
            if not isinstance(output, string_types):
                output = output.decode('utf-8') # python3 returns bytes
            return output
        logging.warning('Command failed: %s', cmd)
        logging.error(err.decode('utf-8'))
        if count < tries:
            logging.info('Re-attempt %s', count + 1)
    raise Exception(f'The following command failed: {cmd}')


def make_dirs_remote(folders: set, creds: Credential):
    """
    @dirs: set of folder paths to create
    @creds: ssh credentials
    """
    if not isinstance(folders, set):
        raise Exception('Invalid parameter.')
    cmds = [f'mkdir -p "{folder}"' for folder in folders]
    run_remote_batch(cmds, creds)



def find_local(start_dir: str, include: str='*', exclude: list=None) -> list[str]:
    """
    @include: a wild card pattern to include files or folders, default is '*'
    @exclude: list of wild card patterns to exclude files or folders
    returns 2 lists of strings which are folder paths and file paths
    """
    files = []
    folders = []
    root = pathlib.Path(start_dir)
    for path in root.rglob(include):
        if path.is_file():
            path = path.absolute().as_posix()
            if exclude:
                for ex in exclude:
                    if re.match(ex.replace('*', '.*'), path):
                        continue
            files.append(path)
        else: # folder:
            folders.append(path.absolute().as_posix())
    return folders, files


def __add_path(path: str, files: list, folders: list):
    """
    @path: str, it starts with with 'F: ' or 'D: ' to distinguish file from folders
    @files: list of files to add to
    @folders: list of folders to add to
    """
    if path[:2] == 'F:':
        files.append(path[2:].strip())
    else:
        folders.append(path[2:].strip())
    
def find_remote(start_dir: str, creds: Credential, include: str='*', exclude: list=None):
    """
    @include: a wild card pattern
    returns 2 lists of strings which are folder paths and file paths
    """
    files = []
    folders = []
    cmd = 'find %s -type f -name "%s" -exec echo "F: {}" \\; -o -type d -exec echo "D: {}" \\;' % (start_dir, include)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(**creds.__dict__)

    stdout = client.exec_command(cmd)[1]
    output = stdout.read().decode('utf-8')
    paths = list(set(output.splitlines()))
    if exclude is None or len(exclude) < 1:
        for path in paths:
            __add_path(path, files, folders)
    else:
        exclude_pat = '|'.join(exclude).replace('*', '.*')
        for path in paths:
            path = path.strip()
            if not re.match(exclude_pat, path):
                __add_path(path, files, folders)
    return folders, files
