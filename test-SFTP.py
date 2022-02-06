"""how to put a file to server using Python"""
import pysftp
import datetime
import os
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None

HOST_NAME = "192.168.0.192"
PORT = 22
USERNAME = "pi"
PASS_WORD = "iamadog99"
datetime_now = ""


def get_datetime():
    return str(datetime.date.today())

#THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
#print(THIS_FOLDER)

datetime_now = get_datetime()

with pysftp.Connection(HOST_NAME, port=PORT, username=USERNAME, password=PASS_WORD, cnopts=cnopts) as sftp:
    print("CONNECTED!!")
    with sftp.cd(f'/home/pi/Desktop'):
        sftp.put('C:\\Users\\user10\\Desktop\\Picture2.png', f'SFTP/sensor1/{datetime_now}', preserve_mtime=True)
    #sftp.put('helloo.txt')
        ## copy files from images, to remote static/images directory, preserving modification time

