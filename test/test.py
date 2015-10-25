import unittest
import os, sys
import shutil
from bunch import Bunch

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.realpath('%s/..' % BASE_DIR))
from parallel_sync import url as _url
from parallel_sync import hasher
from parallel_sync import rsync
import yaml
TEST_DATA = yaml.load(open(os.path.join(BASE_DIR, "data.yaml"), 'r'))
TEST_DATA = Bunch(TEST_DATA)
LOCAL_TARGET = '/tmp/images'
REMOTE_TARGET = '/tmp/x/y'

class TestUpload(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        urls = open(os.path.join(BASE_DIR, 'urls.txt')).readlines()
        self.urls = [url.strip() for url in urls if len(url.strip()) > 0]


    def test_upload_with_key(self):
        _url.download(LOCAL_TARGET, self.urls)
        rsync.upload(LOCAL_TARGET, REMOTE_TARGET, creds=TEST_DATA.creds)
        act_hash = hasher.get_md5(REMOTE_TARGET, TEST_DATA.creds)
        assert act_hash==TEST_DATA.upload_md5,\
           'upload failed. Expected: {}, Actual: {}'\
           .format(TEST_DATA.zipped_download_md5, act_hash)

    def test_download_with_key(self):
        _url.download(REMOTE_TARGET, self.urls, creds=TEST_DATA.creds)
        rsync.download(REMOTE_TARGET, LOCAL_TARGET, creds=TEST_DATA.creds)
        act_hash = hasher.get_md5(REMOTE_TARGET, TEST_DATA.creds)
        assert act_hash==TEST_DATA.zipped_download_md5,\
           'upload failed. Expected: {}, Actual: {}'\
           .format(TEST_DATA.zipped_download_md5, act_hash)


    def test_local_download_urls(self):
        if os.path.exists(LOCAL_TARGET):
            shutil.rmtree(LOCAL_TARGET)

        _url.download(LOCAL_TARGET, self.urls)
        act_hash = hasher.get_md5(LOCAL_TARGET)
        assert act_hash==TEST_DATA.zipped_download_md5,\
           'local download failed. Expected: {}, Actual: {}'\
           .format(TEST_DATA.zipped_download_md5, act_hash)


    def est_local_download_extract_urls(self):# TODO: implement extract
        _url.download(LOCAL_TARGET, self.urls, extract=True, parallelism=2)
        hasher.get_md5(LOCAL_TARGET)
        assert hasher.get_md5(LOCAL_TARGET)==TEST_DATA.zipped_download_md5, 'local extraction failed'


    def test_remote_download_urls(self):
        _url.download(LOCAL_TARGET, self.urls, creds=TEST_DATA.creds)
        act_hash = hasher.get_md5(LOCAL_TARGET, TEST_DATA.creds)
        assert act_hash==TEST_DATA.zipped_download_md5,\
           'remote download failed. Expected: {}, Actual: {}'\
           .format(TEST_DATA.zipped_download_md5, act_hash)


if __name__ == '__main__':
    unittest.main()
