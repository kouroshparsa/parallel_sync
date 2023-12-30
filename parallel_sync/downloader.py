import os
from multiprocessing.pool import ThreadPool
from functools import partial
from urllib import parse, request

def __download(folder: str, url: str, extension: str=None):
    """
    @folder: where to download to
    @url: url to download from
    @extension: if specified, then you'd add this extension to the filename
    """
    scheme, netloc, path, query, fragment = parse.urlsplit(url)
    filename = os.path.basename(path)
    if extension is not None:
        if not extension.startswith('.'):
            extension = f'.{extension}'
        filename = f'{filename}{extension}'

    with request.urlopen(url) as f:
        with open(os.path.join(folder, filename), 'wb') as output:
            output.write(f.read())

def download(folder: str, urls: list, extension=None, parallelism: int=10):
    pool = ThreadPool(processes=parallelism)
    async_results = []
    for url in urls:
        async_results.append(pool.apply_async(__download, (folder, url, extension)))

    for res in async_results:
        res.get()
