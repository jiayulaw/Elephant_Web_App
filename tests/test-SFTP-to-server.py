
import pysftp
import datetime
import os
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None

HOST_NAME = "13.213.160.244"
USERNAME = "ubuntu"

# This is the path to the .pem file
KEYFILE=r'C:\Users\user10\Desktop\lightsailtest\LightsailDefaultKey-ap-southeast-1.pem'
# This is station number, can also try station 2 and station 3
station = "end device 1"
#this is the server path, do not modify
path = '/var/www/Elephant_Web_App/static/image uploads/' + station

# this is the path to img
# the file should have the format of '2021-10-17 22-30' at server side
# image = r"C:\Users\user10\Desktop\2022-02-21 21-21-21-x-maggimee.jpg"

image = r'C:\Users\user10\Desktop\Hobby\Programming\EEEY3 Project\Web App\Elephant_Web_App_v2\static\image uploads\end device 2\2022-03-08 19-20-17-x-roboflowtestt4.jpg'
jsonn = r'C:\Users\user10\Desktop\Hobby\Programming\EEEY3 Project\Web App\Elephant_Web_App_v2\static\image uploads\end device 2\2022-03-08 19-20-17-x-roboflowtestt4.json'



with pysftp.Connection(HOST_NAME, username=USERNAME, private_key=KEYFILE, cnopts=cnopts) as sftp:
    print("CONNECTED!!")
    with sftp.cd(f"{path}"):
        sftp.put(jsonn)
        sftp.put(image)
        

