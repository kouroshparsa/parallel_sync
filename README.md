# V2.x parallel_sync Documentation

Documentation for the older versions of the package are at: <a href="./V1_Doc.md">V1_Doc</a>

**Introduction**

parallel_sync is a python package for uploading or downloading files using multiprocessing and md5 checks. It can do operations such as rsync, scp, wget.
It can use used on both Windows and Linux and Mac OS. Note that on Windows, you need to have OpenSsh enabled and the package will automaticalled use scp instead of rsync.

**How to install:**

`pip install parallel_sync`

**Requirement:**
- Python >= 3
- ssh service must be installed and running.
- if rsync is installed on the local machine, it will be used, otherwise it will fall back to using scp.
- To use the wget method, you need to install wget on the target machine
- To untar/unzip files you need tar/zip packages installed on the target machine

**Benefits:**
- Very fast file transfer (parallelized)
- If the file exists and is not changed, it will not waste time copying it
- You can specify retries in case you have a bad connection
- It can handle large files

In most of the examples below, you can specify `parallelism` and `tries` which allow you to parallelize tasks and retry upon failure.
By default `parallelism` is set to 10 workers and tries is 1.

## Upstream Example:
```python
from parallel_sync import rsync, Credential
creds = Credential(username='user',
     hostname='192.168.168.9',
     port=3022,
     key_filename='~/.ssh/id_rsa')
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
from parallel_sync import rsync, Credential
creds = Credential(username='user',
     hostname='192.168.168.9',
     port=3022,
     key_filename='~/.ssh/id_rsa')
rsync.download('/tmp/y', '/tmp/z', creds=creds)
```


## Downloading files on a remote machine:

For this, you need to have wget installed on the remote machine.
```python
from parallel_sync import wget, Credential
creds = Credential(username='user',
     hostname='192.168.168.9',
     port=3022,
     key_filename='~/.ssh/id_rsa')
urls = ['http://something.png', 'http://somthing.tar.gz', 'http://somthing.zip']
wget.download('/tmp', urls=urls, creds=creds)
```

## Downloading files on the local machine
Downloading files using requests package locally is simple but what if you want to parallelize it?
Here is the solution for that:
```python
from parallel_sync import downloader
urls = ['http://something1', 'http://somthing2', 'http://somthing3']
download('c:/temp/x',
    extension='.png', parallelism=10)
```

## Integration with Fabric:
```
from fabric import task
from parallel_sync import rsync, wget, get_fabric_credentials

@task
def deploy(conn):
    creds = get_fabric_credentials(conn)
    urls = ['http://something1', 'http://somthing2', 'http://somthing3']
    wget.download(creds, '/tmp/images', urls)
    rsync.upload('/src', '/dst', creds, tries=3)
```


If you come across any bugs, please report it on github.
