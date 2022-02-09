"""how to put a file to server using Python"""
import pysftp
import datetime
import os
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None

HOST_NAME = "13.213.160.244"
USERNAME = "ubuntu"
KEYFILE=r'C:\Users\user10\Desktop\lightsailtest\LightsailDefaultKey-ap-southeast-1.pem'
datetime_now = ""


def get_datetime():
    return str(datetime.date.today())

#THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
#print(THIS_FOLDER)

datetime_now = get_datetime()

with pysftp.Connection(HOST_NAME, username=USERNAME, private_key=KEYFILE, cnopts=cnopts) as sftp:
    print("CONNECTED!!")
    with sftp.cd(f'/var/www'):
        # sftp.put('C:\\Users\\user10\\Desktop\\testtPicture1.png', f'www', preserve_mtime=True)
        sftp.put('C:\\Users\\user10\\Desktop\\testttPicture1.png')
    #sftp.put('helloo.txt')
        ## copy files from images, to remote static/images directory, preserving modification time

