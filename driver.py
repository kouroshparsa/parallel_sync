from parallel_sync import rsync, Credential
creds = Credential(username='user',
     hostname='192.168.168.9',
     port=3022,
     key_filename='~/.ssh/id_rsa')
rsync.upload('/tmp/x', '/tmp/y', creds=creds, exclude=['*.pyc', '*.sh'])