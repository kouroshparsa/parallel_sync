"""
parallel_sync
-----------

parallel_sync is a python package for uploading or downloading files using multiprocessing and md5 checks on Linux.
The files can be transferred from a remote linux host or a url.


Link
`````

* Source
  https://github.com/kouroshparsa/parallel_sync

"""
from setuptools import Command, setup, find_packages

version = '1.8.1'
import sys
setup(
    name='parallel_sync',
    version=version,
    url='https://github.com/kouroshparsa/parallel_sync',
    download_url='https://github.com/kouroshparsa/parallel_sync/packages/%s' % version,
    license='GNU',
    author='Kourosh Parsa',
    author_email="kouroshtheking@gmail.com",
    description='A Parallelized file/url syncing package',
    long_description=__doc__,
    packages=find_packages(),
    install_requires = ['paramiko>=1.15.2', 'bunch>=1.0.1'],
    include_package_data=True,
    zip_safe=False,
    platforms='Linux',
    classifiers=[
        'Operating System :: Unix',
        'Programming Language :: Python'
    ]
)

