"""
This module manages file operations such as parallel download
"""
import os
import sys
BASE_DIR = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.realpath("{}/..".format(BASE_DIR)))
import executor
import compression
TIMEOUT = 40

def __url_to_filename(url):
    """ retrieves the filename from the url """
    filename = os.path.basename(url).strip()
    if filename.endswith('?'):
        filename = filename[:-1]
    return filename


def download(target_dir, urls,\
    parallelism=10, creds=None, tries=3, extract=False):
    """ downloads large files either locally or on a remote machine
    @target_dir: where to download to
    @urls: a list of urls or a single url
    @parallelism(default=10): number of parallel processes to use
    @creds: dictionary with credentials
        if None, it will download locally
        if not None, then wget command will be run on a remote host
    @extract: boolean - whether to extract tar or zip files after download
    """
    if isinstance(urls, str):
        urls = [urls]

    if not isinstance(urls, list):
        raise Exception('Expected a list of urls. Received %s' % urls)

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    cmds = []
    for _url in urls:
        filename = __url_to_filename(_url)
        file_path = os.path.join(target_dir, filename)
        cmd = 'wget -O "{}" -t {} -T {} -q "{}"'.format(file_path, tries, TIMEOUT, _url)
        if extract:
            ext = compression.get_unzip_cmd(file_path)
            if ext is not None:
                cmd = "{};cd {};{} {}".format(cmd, target_dir, ext, filename)
        cmds.append(cmd)
    executor.run(cmds, parallelism=parallelism, curr_dir=target_dir, creds=creds)


