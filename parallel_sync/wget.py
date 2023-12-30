"""
This module manages file operations such as parallel download
"""
import os
from . import executor, compression, Credential
TIMEOUT = 40


def __url_to_filename(url: str):
    """ retrieves the filename from the url """
    filename = os.path.basename(url).strip()
    if filename.endswith('?'):
        filename = filename[:-1]
    return filename


def download(creds: Credential, target_dir: str, urls: list,
             filenames: list=None, parallelism: int=10, tries: int=3,
             extract: bool=False, timeout: int=TIMEOUT):
    """ downloads large files on a remote machine
    @creds: ssh credentials
    @target_dir: where to download to
    @urls: a list of urls or a single url
    @filenames: list of filenames. If used, the the urls will be downloaded to
        those file names
    @parallelism(default=10): number of parallel processes to use
    @extract: boolean - whether to extract tar or zip files after download
    """
    if isinstance(urls, str):
        urls = [urls]

    if not isinstance(urls, list):
        raise ValueError(f'Expected a list of urls. Received {urls}')

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    cmds = []
    if filenames is not None and len(filenames) != len(urls):
        raise ValueError('You have specified filenames but the number '\
                        'of filenames does not match the number of urls')

    filenames = [__url_to_filename(url) for url in urls]
    for ind, _url in enumerate(urls):
        filename = filenames[ind]
        file_path = f'{target_dir}/{filename}'
        cmd = f'wget -O "{file_path}" -t {tries} -T {timeout} "{_url}"'
        # note: don't use the -q option because
        # if it fails, you don't get any message or return code
        if extract:
            ext = compression.get_unzip_cmd(file_path)
            if ext is not None:
                cmd = f'{cmd};cd "{target_dir}";{ext} "{filename}"'
        cmds.append(cmd)
    
    executor.run_remote_batch(cmds, creds, curr_dir=target_dir, parallelism=parallelism)
