
#https://www.techwithtim.net/flask-rest-api/

import requests

BASE = "http://127.0.0.1:5000/"


# set device_id to specify the device to update
# i.e., 1 is for end device 1, 2 is for end device 2, and 3 is for ...
# set status to modify time
# set message to atach a message
# the name will be what will be displayed on server
device_id = "99"
name = "base station"
status = "8.10 pm 20-02-2022"
message  = "777 hello"

# this is a function to send 
def update_device_stat(device_id, name, status, message):
    print("Trying to create new row in DB")
    response = requests.put(BASE + "device_stat/" + device_id, {"name":name, "status":status,"message":message})
    print(response.json())

    print("Update existing row in DB")
    response = requests.patch(BASE + "device_stat/" + device_id, {"name":name, "status":status,"message":message})
    print(response.json())

    print("Displaying updated row in DB")
    response = requests.get(BASE + "device_stat/" + device_id)
    print(response.json())

update_device_stat(device_id, name, status, message)