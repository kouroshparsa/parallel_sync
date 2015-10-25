parallel_sync
==========

parallel_sync is a python package for uploading or downloading files using multiprocessing and md5 checks on Linux.
The files can be transferred from a remote linux host or a url.

How to install:
`pip install parallel_sync`

Requirement:
- Python 2.7
- ssh service must be installed and running.
- To use the rsync features, you need to have rsync installed.
- to use the url module, you need to install wget on the target machine

Benefits:
- Very fast file transfer (parallelized)
- If the file exists and is not changed, it will not waste time copying it
- You can specify retries in case you have a bad connection
- It can handle large files

Upstream Example:
```
from parallel_sync import rsync
creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31'}
rsync.upload('/tmp/x', '/tmp/y', creds=creds)
```

Downstream Example:
```
from parallel_sync import rsync
creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31'}
rsync.download('/tmp/y', '/tmp/z', creds=creds)
```

File Download Example:
```
from parallel_sync import url as _url
urls = ['http://something.png', 'http://somthing.tar.gz', 'http://somthing.zip']
_url.download('/tmp', urls=urls, extract=True)

# download on a remote machine:
creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31'}
_url.download('/tmp', urls=urls, creds=creds)
```

Example using parallel_sync within fabric:
```
from fabric.api import env
from parallel_sync import rsync
rsync.upload('/tmp/x', '/tmp/y', env=env)
rsync.download('/tmp/y', '/tmp/z', env=env)
```

If you come across any bugs, please report it on github.
I will be adding more features such as file extraction soon.

