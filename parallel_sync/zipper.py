import subprocess
import os
import logging

def unzip(target_path):
    target_dir = os.path.dirname(target_path)
    filename = os.path.basename(target_path)
    if target_path.endswith('.tar.gz'):
        logging.info('untarring %s', filename)
        subprocess.check_output('cd {};tar -zxf {}'\
        .format(target_dir, filename), shell=True)
    elif target_path.endswith('.gz'):
        logging.info('gunzipping %s', filename)
        subprocess.check_output('cd {};gunzip {}'\
        .format(target_dir, filename), shell=True)
    elif target_path.endswith('.zip'):
        logging.info('unzipping %s', filename)
        subprocess.check_output('cd {};unzip {}'\
        .format(target_dir, filename), shell=True)

