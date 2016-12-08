import subprocess
import os
import logging
from parallel_sync import executor


def get_unzip_cmd(path):
    if path.endswith('.tar.gz'):
        return 'tar -zxf'
    elif path.endswith('.gz'):
        return 'gunzip'
    elif path.endswith('.zip'):
        return 'unzip'
    else:
        return None


def extract(target_path, creds=None):
    """
    unzipps or untars a files or multiple files under a directory
        either locally or on a remote host
    @target_path: string - directory or file path
    @creds: a dictionary or Bunch object used for remote execution
    """
    if not executor.path_exists(target_path, creds):
        logging.warn('Invalid path: %s' % target_path)
        return

    cmds = []
    if executor.is_file(target_path, creds):
        target_dir = os.path.dirname(target_path)
        filename = os.path.basename(target_path)
        cmd = get_unzip_cmd(filename)
        if cmd is not None:
            cmds.append('cd {}; {} {}'\
                        .format(target_dir,\
                                get_unzip_cmd(filename),\
                                filename))

    else: # directory
        files = executor.find_files(target_path, creds, include=['*.gz', '*.zip'])
        for path in files:
            target_dir = os.path.dirname(path)
            filename = os.path.basename(path)
            unzip_cmd = get_unzip_cmd(filename)
            if unzip_cmd is not None:
                cmds.append('cd {}; {} {}'\
                    .format(target_dir, unzip_cmd, filename))

    executor.run(cmds, creds)

