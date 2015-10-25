import subprocess
cmd = 'find /tmp/images -type f -exec md5sum {} \; | sort | md5sum'
proc = subprocess.Popen(cmd, shell=True,\
    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output, err = proc.communicate()
print output
