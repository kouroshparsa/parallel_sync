find /tmp/images -type f -exec md5sum {} \; | sort | md5sum
