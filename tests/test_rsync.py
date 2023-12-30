"""
This file has the unittests, to run use this command:
pytest
"""
from parallel_sync import rsync, Credential
import pytest
from unittest.mock import patch

def test_upload_null_params():
    with pytest.raises(Exception):
        rsync.upload(None, None, creds=None)


def test_get_dst_path():
    assert rsync.__get_dst_path('/x', '/x/a', '/tmp') == '/tmp/a'
    assert rsync.__get_dst_path('/x', '/x/a/b', '/tmp') == '/tmp/a/b'
    assert rsync.__get_dst_path('/x/filename', '/x/filename', '/tmp') == '/tmp/filename'
    assert rsync.__get_dst_path('C:\\x\\filename', 'C:\\x\\filename', '/tmp') == '/tmp/filename'

class MockStdOut:
    class Channel:
        def recv_exit_status(self):
            return 0
    channel = Channel()
    def read(self):
        return ''

@patch('parallel_sync.executor.find_local')
@patch('paramiko.SSHClient.connect')
@patch('paramiko.SSHClient.exec_command')
@patch('parallel_sync.rsync.__get_transfer_commands')
def test_upload(mock_tr_cmd, mock_exec_command, mock_connect, mock_find_local):
    creds = Credential(username='u', hostname='h',port=3022, key_filename='k')
    mock_find_local.return_value = ['/src_dir/a', '/src_dir/b']
    mock_connect.return_value = None
    buffer = MockStdOut()
    mock_exec_command.return_value = [None, buffer, buffer]
    mock_tr_cmd.return_value = []
    rsync.upload('/src_dir', '/dst_dir', creds=creds)
    assert mock_tr_cmd.called

@patch('parallel_sync.rsync.__is_rsync_installed')
def test_get_transfer_commands_rsync_upstream(mock_is_rsync_installed):
    mock_is_rsync_installed.return_value = True
    creds = Credential(username='u', hostname='h',port=3022, key_filename='k')
    paths = [('/src/1', '/dst/1'),
             ('/src/2', '/dst/2')]# first source, then destination path
    cmds = rsync.__get_transfer_commands(creds, True, paths)
    assert cmds == ['rsync -c -e \'ssh -i k\' -o StrictHostKeyChecking=no -o ServerAliveInterval=100 "/src/1" u@h:"/dst/1" --port 3022',
                    'rsync -c -e \'ssh -i k\' -o StrictHostKeyChecking=no -o ServerAliveInterval=100 "/src/2" u@h:"/dst/2" --port 3022']

@patch('parallel_sync.rsync.__is_rsync_installed')
def test_get_transfer_commands_rsync_downstream(mock_is_rsync_installed):
    mock_is_rsync_installed.return_value = True
    creds = Credential(username='u', hostname='h',port=3022, key_filename='k')
    paths = [('/src/1', '/dst/1'),
             ('/src/2', '/dst/2')]# first source, then destination path
    cmds = rsync.__get_transfer_commands(creds, False, paths)
    assert cmds == ['rsync -c -e \'ssh -i k\' -o StrictHostKeyChecking=no -o ServerAliveInterval=100 u@h:"/src/1" "/dst/1"',
                    'rsync -c -e \'ssh -i k\' -o StrictHostKeyChecking=no -o ServerAliveInterval=100 u@h:"/src/2" "/dst/2"']

@patch('parallel_sync.rsync.__is_rsync_installed')
def test_get_transfer_commands_scp_upstream(mock_is_rsync_installed):
    mock_is_rsync_installed.return_value = False
    creds = Credential(username='u', hostname='h',port=3022, key_filename='k')
    paths = [('/src/1', '/dst/1'),
             ('/src/2', '/dst/2')]# first source, then destination path
    cmds = rsync.__get_transfer_commands(creds, True, paths)
    assert cmds == ['scp -P 3022 -i "k" "/src/1" u@h:"/dst/1"',
                    'scp -P 3022 -i "k" "/src/2" u@h:"/dst/2"']

@patch('parallel_sync.rsync.__is_rsync_installed')
def test_get_transfer_commands_scp_downstream(mock_is_rsync_installed):
    mock_is_rsync_installed.return_value = False
    creds = Credential(username='u', hostname='h',port=3022, key_filename='k')
    paths = [('/src/1', '/dst/1'),
             ('/src/2', '/dst/2')]# first source, then destination path
    cmds = rsync.__get_transfer_commands(creds, False, paths)
    assert cmds == ['scp -P 3022 -i "k" u@h:"/src/1" "/dst/1"',
                    'scp -P 3022 -i "k" u@h:"/src/2" "/dst/2"']
