from fabric import task
from parallel_sync import rsync, wget, get_fabric_credentials

@task
def deploy(conn):
    creds = get_fabric_credentials(conn)
    urls = ['https://images.unsplash.com/photo-1682695798256-28a674122872?q=80&w=3870&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDF8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
            'https://images.unsplash.com/photo-1682687982360-3fbab65f9d50?q=80&w=3870&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDF8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D']
    wget.download(creds, '/tmp/images', urls)
