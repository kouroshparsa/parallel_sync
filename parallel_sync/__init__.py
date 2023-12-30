"""
This module is the core package module
"""
import logging
from dataclasses import dataclass
logging.basicConfig(level='INFO')
logging.getLogger("paramiko").setLevel(logging.WARNING)

class IllegalArgumentError(ValueError):
    pass
@dataclass
class Credential:
    key_filename: str
    username: str
    hostname: str
    port: int = 22
    timeout: int = 10 # seconds


def get_fabric_credentials(conn) -> Credential:
    """
    @conn: fabric connection object of type fabric.connection.Connection
    Returns a Credential object
    """
    import fabric
    if not isinstance(conn, fabric.connection.Connection):
        raise IllegalArgumentError('Invalid parameter. You are supposed to pass '
                        'an object of type fabric.connection.Connection')
    user = conn.user
    host = conn.host
    port = conn.port
    key = conn.connect_kwargs['key_filename'][0]
    return Credential(key_filename=key, username=user, hostname=host, port=port)
