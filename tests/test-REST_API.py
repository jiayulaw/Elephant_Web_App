
#https://www.techwithtim.net/flask-rest-api/

import requests

# BASE = "http://127.0.0.1:5000/"

BASE = "https://d3m318b1ejw1x6.cloudfront.net/"
# set device_id to specify the device to update
# i.e., 1 is for end device 1, 2 is for end device 2, and 3 is for ...
# set last_seen to modify time
# set message to attach a message
# the name will be what will be displayed on server
# set status as online
device_id = "1"
name = "end device 1"
last_seen = "2022-04-13 17-22-20"
message  = "alive"
status = "Online"
battery_voltage = "12"
battery_current = "0.77"
battery_temp_1 = "37"
battery_temp_2 = "38"
ambient_temp = "30"

# this is a function to send 
def update_device_stat(device_id, name, last_seen, message, status, battery_voltage, battery_current, battery_temp_1, battery_temp_2, ambient_temp):
    print("Trying to create or update row in DB")
    response = requests.put(BASE + "device_stat/" + device_id, {"name":name, "last_seen":last_seen,"message":message, "status": status, "battery_voltage": battery_voltage, "battery_current": battery_current, "battery_temp_1": battery_temp_1, "battery_temp_2": battery_temp_2, "ambient_temp": ambient_temp})
    print(response.json())

    # print("Update existing row in DB")
    # response = requests.patch(BASE + "device_stat/" + device_id, {"name":name, "last_seen":last_seen,"message":message, "status": status, "battery_voltage": battery_voltage, "battery_current": battery_current})
    # print(response.json())

    # print("Displaying updated row in DB")
    # response = requests.get(BASE + "device_stat/" + device_id)
    # print(response.json())

update_device_stat(device_id, name, last_seen, message, status, battery_voltage, battery_current, battery_temp_1, battery_temp_2, ambient_temp)