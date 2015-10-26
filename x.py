from parallel_sync import executor
creds={'user': 'kparsa', 'key':'~/.ssh/id_rsa', 'host':'192.168.168.31'}
#print executor.run('pwd', creds=creds, curr_dir='/tmp')
executor.delete_dir('/tmp/qq', creds=creds)

