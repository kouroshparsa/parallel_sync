"""
This module is for handling unziping of archived files
"""

def get_unzip_cmd(path: str):
    """
    @path: str
    returns the command to unzip that specified file
    """
    if path.endswith('.tar.gz'):
        return 'tar -zxf'
    elif path.endswith('.gz'):
        return 'gunzip'
    elif path.endswith('.zip'):
        return 'unzip'
    
    return None
