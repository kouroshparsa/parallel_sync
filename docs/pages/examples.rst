parallel_sync Usage
==========

parallel_sync is a python package for uploading or downloading files using multiprocessing and md5 checks on Linux.
The files can be transferred from a remote linux host or a url.

Benefits:
- Very fast file transfer (parallelized)
- If the file exists and is not changed, it will not waste time copying it
- You can specify retries in case you have a bad connection
- It can handle large files

Upstream Example:
::
    from parallel_sync import rsync
    creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31'}
    rsync.upload('/tmp/local_dir', '/tmp/remote_dir', creds=creds)

Downstream Example:
::
    from parallel_sync import rsync
    creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31'}
    rsync.download('/tmp/remote_dir', '/tmp/local_dir', creds=creds)


File Download Example:
::
    from parallel_sync import url as _url
    urls = ['http://something.png', 'http://somthing.tar.gz', 'http://somthing.zip']
    _url.download('/tmp', urls=urls, extract=True)

    # download on a remote machine:
    creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31'}
    _url.download('/tmp', urls=urls, creds=creds)

    # To untar or unzip compressed files after download:
    _url.download('/tmp', urls=urls, creds=creds, extract=True)


Example extracting a file on a remote host:
::
    creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31'}
    rom parallel_sync import compression
    compression.extract('/tmp/x.tar.gz', creds=creds)


Example checking that a files exists:
::
    from parallel_sync import executor
    if executor.path_exists(path, creds):
        print "yes"


Example finding files or directories:
::
    from parallel_sync import executor
    files = executor.find_files(dir_path, creds, include=['*.png', '*.jpg'])
    dirs = executor.find_dirs(dir_path, creds, include=['test'])

Note that if creds is None, then it will search on localhost


Example Running commands:
::
    from parallel_sync import executor
    cmds = ['mv /tmp/x /tmp/y', 'touch /tmp/z']
    executor.run(cmds, creds=creds, parallelism=len(cmds)):
    print executor.run('pwd', creds=creds, curr_dir='/tmp')


Example using parallel_sync within fabric:
::
    from fabric.api import env
    from parallel_sync import rsync
    rsync.upload('/tmp/x', '/tmp/y', creds=env)
    rsync.download('/tmp/y', '/tmp/z', creds=env)



If you come across any bugs, please report it on github.

