"""
This file has smoke tests. Here is how you can run them:
python .\smoke_tests\rsync.py
"""
from parallel_sync import rsync, Credential
import unittest

class TestStringMethods(unittest.TestCase):

    def test_upload_file(self):
        creds = Credential(username='kourosh', hostname='localhost', port=3022, key_filename='C:/kourosh/virtualbox_ssh_key/id_rsa')
        rsync.upload('c:/temp/test.txt', '/tmp/', creds=creds)

    def test_upload_dir(self):
        creds = Credential(username='kourosh', hostname='localhost', port=3022, key_filename='C:/kourosh/virtualbox_ssh_key/id_rsa')
        rsync.upload('c:/temp/testdir', '/tmp/testdir', creds=creds)

    def test_download_file(self):
        creds = Credential(username='kourosh', hostname='localhost', port=3022, key_filename='C:/kourosh/virtualbox_ssh_key/id_rsa')
        rsync.download('/tmp/test.txt', 'C:/temp/x/', creds=creds)

    def test_download_dir(self):
        creds = Credential(username='kourosh', hostname='localhost', port=3022, key_filename='C:/kourosh/virtualbox_ssh_key/id_rsa')
        rsync.download('/tmp/testdir', 'c:/temp/z', creds=creds)

if __name__ == '__main__':
    unittest.main()