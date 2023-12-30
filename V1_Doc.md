
# V1.x parallel_sync Documentation

**Introduction**

parallel_sync is a python package for uploading or downloading files using multiprocessing and md5 checks on Linux.
The files can be transferred from a remote linux host or a url.

**How to install:**

`pip install parallel_sync`

**Requirement:**
- Python >= 2.6 Linux Only!
- ssh service must be installed and running.
- To use the rsync features, you need to have rsync installed.
- to use the url module, you need to install wget on the target machine
- To untar/unzip files you need tar/zip packages installed

**Benefits:**
- Very fast file transfer (parallelized)
- If the file exists and is not changed, it will not waste time copying it
- You can specify retries in case you have a bad connection
- It can handle large files

In most of the examples below, you can specify `parallelism` and `tries` which allow you to parallelize tasks and retry upon failure.
By default `parallelism` is set to 10 workers.

## Upstream Example:
```python
from parallel_sync import rsync
creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31'}
rsync.upload('/tmp/x', '/tmp/y', creds=creds, exclude=['*.pyc', '*.sh'])
```

## Downstream Example:

```python
from parallel_sync import rsync
creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31'}
rsync.download('/tmp/y', '/tmp/z', creds=creds)
```

## Using non-default Ports
```python
from parallel_sync import rsync
creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31', 'port': 1234}
rsync.download('/tmp/y', '/tmp/z', creds=creds)
```


## File Download Example:

```python
from parallel_sync import wget
urls = ['http://something.png', 'http://somthing.tar.gz', 'http://somthing.zip']
wget.download('/tmp', urls=urls, extract=True)

# download locally with a specified filename:

wget.download(LOCAL_TARGET, 'http://something/else/file.zip',\
              filenames='x.zip', extract=True)

# download on a remote machine:

creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31'}
wget.download('/tmp', urls=urls, creds=creds)

# To untar or unzip compressed files after download:
wget.download('/tmp', urls=urls, creds=creds, extract=True)
```

Example extracting a file on a remote host:

```python
creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31'}
from parallel_sync import compression
compression.extract('/tmp/x.tar.gz', creds=creds)
```

Example checking that a files exists on the remote server:

```python
from parallel_sync import executor
creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31'}
path = '/tmp/myfile'
if executor.path_exists(path, creds):
    print("yes")
```

Example finding files or directories on a remote server:

```python
from parallel_sync import executor
creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31'}
dir_path = '/tmp/mydir'
files = executor.find_files(dir_path, creds, include=['*.png', '*.jpg'])

dirs = executor.find_dirs(dir_path, creds, include=['test'])

# Note that if creds is None, then it will search on localhost
```

Example Running commands:

```python
from parallel_sync import executor

cmds = ['mv /tmp/x /tmp/y', 'touch /tmp/z']
creds = {'user': 'myusername', 'key':'~/.ssh/id_rsa', 'host':'192.168.16.31'}
executor.run(cmds, creds=creds, parallelism=len(cmds))

print(executor.run('pwd', creds=creds, curr_dir='/tmp'))
```

Example using parallel_sync within fabric:

```python
from fabric.api import env
from parallel_sync import rsync

rsync.upload('/tmp/x', '/tmp/y', creds=env)
rsync.download('/tmp/y', '/tmp/z', creds=env)
```

To transfer files locally:

```python
from parallel_sync import rsync
rsync.copy('/tmp/x', '/tmp/y', exclude=['*.pyc'], parallelism=10, extract=False, validate=False)
```

where /tmp/x is a directory.


If you come across any bugs, please report it on github.
