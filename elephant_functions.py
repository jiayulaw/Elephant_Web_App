#turorial: https://www.tutorialspoint.com/sqlite/sqlite_python.htm

import shutil
import sqlite3
from sqlite3.dbapi2 import enable_shared_cache
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy 
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import sys
import time
import datetime
import arrow
import os
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView 
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from os.path import exists
import random
# 
import pytz
from app_config import *
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import logging
import requests
import base64
# For roboflow API
import cv2
from roboflow_config import *
from PIL import Image
import io
import ast
from pathlib import Path
import sqlite3
from xlsxwriter.workbook import Workbook

def logServerActivity(timestmp, type, description, db):
    """
    Record server activity to database table based on timestamp, activity type, 
    and description provided.
    """
    new_activity = Server_activity(timestamp = timestmp, type = type, description=description)
    db.session.add(new_activity)
    db.session.commit()

def logServerDebugger(timestmp, type, description, db):
    """
    Record server debugger to database table based on timestamp, activity type, 
    and description provided.
    """
    new_activity = Server_debugger(timestamp = timestmp, type = type, description=description)
    db.session.add(new_activity)
    db.session.commit()

def checkFilePath(file_path, absolute_file_path, img_source, filename, BASE_DIR, app):
    """ 
    Checks whether directory name exists. 
    If directory already exists, it returns a directory name with random integers appended.
    Else, the original directory name will be returned.
    """
    while exists(absolute_file_path):
        n = random.randint(0,999999)
        namestr = img_source + "/" + str(n) + "_" + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], namestr)
        absolute_file_path = os.path.join(BASE_DIR, file_path)
    return file_path, absolute_file_path


def Local2UTC_time(LocalTime):
    """
    Converts a datetime object that contains local timezone information to UTC datetime object.
    """
    EpochSecond = time.mktime(LocalTime.timetuple())
    utcTime = datetime.datetime.utcfromtimestamp(EpochSecond)
    return utcTime

def getMalaysiaTime(timestamp, format):
    """
    Converts a local datetime object to UTC and then to UTC+8 (Malaysia) timezone.
    Returns Malaysia timezone datetime string with specified format.
    """
    # Convert to UTC
    UTC_timestamp = Local2UTC_time(timestamp)
    # Adds 8 hours to UTC to get Malaysia time 
    Malaysia_timezone_timestamp = UTC_timestamp + datetime.timedelta(hours=8)
    date_created = Malaysia_timezone_timestamp.strftime(format)
    return date_created

def bounding_box_and_text(annotations, img):
    """
    Accepts image annottaion and an image in numpy array format (BGR).
    Returns an annotated image with boxes and labels, in numpy array format (BGR).
    """
    copy_image = img.copy()
    for box in annotations:
        label = box['label']
        x = box['coordinates']['x']
        y = box['coordinates']['y']
        w = box['coordinates']['width']
        h = box['coordinates']['height']
        confidence = box['confidence']
        # shift x & y as annotations was meant for roboflow
        x  -= w/2
        y  -= h/2
        x = int(x)
        y = int(y)
        # draw rectangle
        
        cv2.rectangle(copy_image, (x, y), (x + w, h + y), color=(0, 205, 255), thickness=2)
        # Setting label to print about bounding box
        text_box = label + str(" (") + str(round(confidence*100,2)) +str("%)")

        # Get location of bounding box
        labelSize, baseLine = cv2.getTextSize(text_box, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)  # Get font size

        # Put text above bounding box
        cv2.rectangle(copy_image, (x, y), (x+labelSize[0]+5, y+baseLine-30), (0, 205, 255), cv2.FILLED)
        # cv2.rectangle(copy_image, (x - labelSize[0]/2 - 2, y), (x+labelSize[0]/2+2, y-baseLine-), (0, 205, 255), cv2.FILLED)
        cv2.putText(copy_image, text_box, (x+10, y-7), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0, 0, 0), 2)
    return copy_image

def annotate_img_and_send_to_roboflow(BASE_DIR, path, common_name, detection_datetime, detection_type, fileformat, db):
    """
    Triggers the annotation of image if a corresponding json file is found within the same directory of image.
    Save the annotated image at the same directory.
    Send the unannotated image together with annotation files to Roboflow platform through REST API.
    """
    absolute_path = os.path.join(BASE_DIR, path)
    original_img = cv2.imread(absolute_path)
    JsonFileName = common_name + ".json"
    # JsonFilePath = os.path.join(directory, JsonFileName)

    JsonFilePath = os.path.dirname(path)+"/" + JsonFileName
    # JsonFilePath = os.path.join(rf"static/image uploads/{device_name}", JsonFileName)
    JsonFilePath_absolute = os.path.join(BASE_DIR, JsonFilePath)
    annotated_filename = detection_datetime + "xxx" + detection_type + "_annotated." + fileformat
    annotated_filepath = os.path.dirname(path)+"/" + annotated_filename
    annotated_filepath_absolute = os.path.join(BASE_DIR, annotated_filepath)

    #if the image is annotated and there exist an annotation file for it
    if (os.path.exists(annotated_filepath_absolute)) and os.path.exists(JsonFilePath_absolute):
        result = Images.query.filter_by(path=path).first()
        #if there is no annotation record
        if not result.path2:
            #this happens when performing database reset where it forgets
            # about previous annotation
            # # then just update the database with annotation record 
            result.path2 = annotated_filepath
            result.json_path = JsonFilePath
            db.session.commit()

    #if the image is not yet annotated and there exist an annotation file for it
    if (not os.path.exists(annotated_filepath_absolute)) and os.path.exists(JsonFilePath_absolute):
    #    Read Annotation as String
        annotationStr = open(JsonFilePath_absolute, "r").read()
        annotationList = ast.literal_eval(annotationStr)
        print(annotationList)
        print(type(annotationList))

        try: #sometimes unknown error occurs due to this line... so i use try except here
            annotated_img = bounding_box_and_text(annotationList[0]['annotations'],original_img)
            logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Image Annotation Success", "Image @ " + path + " was successfully annotated." , db)
            logServerDebugger(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Image Annotation Success", "Image @ " + path + " was successfully annotated." , db)
        except:
            print("an error occured when annotating image. Image now set to original image.")
            annotated_img = original_img
            logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Image Annotation Failed", "Image @ " + path + " failed to be annotated." , db)
            logServerDebugger(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Image Annotation Failed", "Image @ " + path + " failed to be annotated." , db)
            
        cv2.imwrite(annotated_filepath_absolute, annotated_img)
        result = Images.query.filter_by(path=path).first()
        result.path2 = annotated_filepath
        result.json_path = JsonFilePath
        img_id = result.id
        db.session.commit()

        # remember to remove confidence from the annotations before sending to roboflow api
        for box in annotationList[0]['annotations']:
            del box['confidence']

        # PROCEED TO ROBOFLOW API
        # After all detections, Convert image
        roboflow_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
        pilImage = Image.fromarray(roboflow_img)

        # Convert to JPEG Buffer
        buffered = io.BytesIO()
        pilImage.save(buffered, quality=90, format="JPEG")

        # Base 64 Encode
        img_str = base64.b64encode(buffered.getvalue())
        img_str = img_str.decode("ascii")
        print("decoded and ready to send!")
        # Construct the URL
        image_upload_url = "".join([
            "https://api.roboflow.com/dataset/", DATASET_NAME, "/upload",
            "?api_key=", ROBOFLOW_API_KEY,
            "&name=", os.path.basename(path),
            "&split=train"
        ])

        r = requests.post(image_upload_url, data=img_str, headers={
            "Content-Type": "application/x-www-form-urlencoded"
        })
        # try:
        imageId = r.json()['id']
        print(imageId)
        logServerDebugger(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Roboflow Image Id", "Image id " + str(imageId)  + " was obtained from Roboflow platform.", db)

        #Writing  out .json will have permission error on Linux server
        # # After all detections,
        # # Save to Json File
        # with open("activeLearning.json", 'w') as outfile:
        #     json.dump(annotationList, outfile)
        # # Read Annotation as String
        # annotationStr2 = open("activeLearning.json", "r").read()

        # print("below is string read from json:")
        # print(annotationStr2)

        
        annotationStr2 = str(annotationList)
        annotationStr2 = annotationStr2.replace("\'", "\"")
        print("below is string read converted from list:")
        print(annotationStr2)

        # Construct the URL
        annotation_upload_url = "".join([
            "https://api.roboflow.com/dataset/", DATASET_NAME, "/annotate/", imageId,
            "?api_key=", ROBOFLOW_API_KEY,
            "&name=activeLearning.json"
        ])
        print(annotation_upload_url)
        # POST to the API
        print("below is string converted from list using str method:")
        annotationStr = str(annotationList)
        r = requests.post(annotation_upload_url, data=annotationStr2, headers={
            "Content-Type": "text/plain"
        })
        print("annotate sent!")
        print(annotationStr2)
        print(type(annotationStr2))
        logServerDebugger(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Roboflow annotation str", "Image with id " + str(img_id)  + ": annotation str generated >> " + annotationStr2, db)

        try:
            print(r.json()['success'])
            logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Roboflow Upload Success", "Image with id " + str(img_id)  + " succesfully uploaded to Roboflow platform.", db)
            logServerDebugger(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Roboflow Upload Success", "Image with id " + str(img_id)  + " succesfully uploaded to Roboflow platform.", db)
        except:
            logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Roboflow Upload Failed", "Image with id " + str(img_id)  + " failed to be uploaded to Roboflow platform.", db)
            logServerDebugger(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Roboflow Upload Failed", "Image with id " + str(img_id)  + " failed to be uploaded to Roboflow platform.", db)

    
        print("Done Bossku")


def update_server_directory_images(Images, BASE_DIR):
    """ 
    Check directory to look for any image file (of certain naming format) that is not recorded in database.
    Proceed to record the unrecorded image if any.
    """
    print("Updating server directory images and detection information...")
    for device_name in ['end device 1', 'end device 2', 'end device 3', 'uploaded']:
        directory = rf"static/image uploads/{device_name}" 
        directory2 = os.path.join(BASE_DIR, directory)
        for filename in os.listdir(directory2):
            try: #dont use try except here! it is only making things complicated!
                if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".jpeg"):
                    if '-x-' in filename and 'thumbnail' not in filename and 'edited' not in filename:
                        #strip away file format extension
                        common_name = filename.split(".")[0]
                        fileformat = filename.split(".")[1]
                        #strip between datetime and detection type
                        arr1 = common_name.split("-x-")
                        detection_date_time = arr1[0]
                        date_time_obj = datetime.datetime.strptime(detection_date_time,'%Y-%m-%d %H-%M-%S')
                        date_time = datetime.datetime.strftime(date_time_obj, "%Y-%m-%d %H:%M:%S")
                        
                        detection_type = arr1[1]
                        # path = os.path.join(directory, filename)
                        path = rf"static/image uploads/{device_name}/"+filename

                        result = Images.query.filter_by(path=path).first()
                        if result:
                            # print("the file with same name already saved")
                            annotate_img_and_send_to_roboflow(BASE_DIR, path, common_name, detection_date_time, detection_type, fileformat, db)
                        else:
                            ######################################################
                            # Save a copy of image to NodeRed folder 
                            ######################################################
                            src_absolute_path = os.path.join(BASE_DIR, path)
                            dest_path = f'NodeRed/{device_name}/new_image.' + fileformat
                            dest_absolute_path = os.path.join(BASE_DIR, dest_path)
                            shutil.copy2(src_absolute_path, dest_absolute_path)
                            ######################################################
                            # Record new image to database 
                            ######################################################
                            new_image = Images(timestamp = date_time, path = path, source=device_name, tag = detection_type, latitude ="", longitude = "")
                            db.session.add(new_image)
                            db.session.commit()
                            logServerDebugger(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Object Detection", "New image from " + device_name + " detected and recorded to database.", db)
                            logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Object Detection", "New image from " + device_name + " detected and recorded to database.", db)

                            ######################################################
                            # Check and send .json file associated with the image (if any)
                            ######################################################
                            annotate_img_and_send_to_roboflow(BASE_DIR, path, common_name, detection_date_time, detection_type, fileformat, db)
                else:
                    continue
            except Exception as e:
                logServerDebugger(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Exception: Update image directory", str(e), db)
                



# def update_end_device_database_thread():
#         ###########################################################################
#     # Update end device online/offline status
#     ###########################################################################
#     while True:
#         print("Updating end devices status...")
#         cursor = end_device.query.all()        
#         UTCnow = datetime.datetime.utcnow() # current date and time in UTC
#         for device in cursor:
#             datetime_object = datetime.datetime.strptime(device.last_seen, '%d/%m/%Y, %H:%M:%S')
#             #hardcode the timezone as Malaysia timezone
#             timezone = pytz.timezone("Asia/Kuala_Lumpur")
#             #add timezone attribute to datetime object
#             datetime_object_timezone = timezone.localize(datetime_object, is_dst=None)
#             utc_datetime_obj = datetime_object_timezone.astimezone(pytz.utc)
#             # need to convert datetime obj above into a naive object to prevent
#             # # error during subtraction with another datetime
#             #Refrence: https://stackoverflow.com/questions/796008/cant-subtract-offset-naive-and-offset-aware-datetimes 
#             naive = utc_datetime_obj.replace(tzinfo=None)
#             # getting the difference between the received datetime string and current datetime in seconds
#             diff_in_seconds = (UTCnow - naive).seconds
#             # Dividing seconds by 60 we get minutes
#             output = divmod(diff_in_seconds,60)
#             diff_in_minutes = output[0]
#             if diff_in_minutes > 30:
#                 if device.status != "Offline":
#                     logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Status change", "Device - " + device.name + " changed status from " + device.status + " to " + "Offline", db)
#                     device.status = "Offline"
        
#         db.session.commit()
#         time.sleep(2)
#         print ("Exiting ")
    

def update_device_status_thread():
    """
    An infinite loop that checks the status of device and update status 
    to "Offline" if not being seen for more than 30 minutes.
    """
    try:
        while True:
            print("Updating end devices status...")
            cursor = end_device.query.all()        
            UTCnow = datetime.datetime.utcnow() # current date and time in UTC
            for device in cursor:
                datetime_object = datetime.datetime.strptime(device.last_seen, '%I:%M:%S %p, %d/%m/%Y')
                #hardcode the timezone as Malaysia timezone
                timezone = pytz.timezone("Asia/Kuala_Lumpur")
                #add timezone attribute to datetime object
                datetime_object_timezone = timezone.localize(datetime_object, is_dst=None)
                utc_datetime_obj = datetime_object_timezone.astimezone(pytz.utc)
                # need to convert datetime obj above into a naive object to prevent
                # # error during subtraction with another datetime
                #Refrence: https://stackoverflow.com/questions/796008/cant-subtract-offset-naive-and-offset-aware-datetimes 
                naive = utc_datetime_obj.replace(tzinfo=None)
                # getting the difference between the received datetime string and current datetime in seconds
                diff_in_seconds = (UTCnow - naive).seconds
                # Dividing seconds by 60 we get minutes
                output = divmod(diff_in_seconds,60)
                diff_in_minutes = output[0]
                if diff_in_minutes > 15:
                    if device.status != "Offline":
                        logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Status change", "Device - " + device.name + " changed status from " + device.status + " to " + "Offline", db)
                        device.status = "Offline"
            
            db.session.commit()



            db_path = os.path.join(BASE_DIR, "database.sqlite")
            # generation of Excel file from SQLite referenced from https://stackoverflow.com/questions/24577349/flask-download-a-file
            print ("Updating debugger log excel")
            workbook = Workbook(os.path.join(BASE_DIR, 'static/debugger_log.xlsx'))
            worksheet = workbook.add_worksheet()
            conn=sqlite3.connect(db_path)
            c=conn.cursor()
            mysel=c.execute("select * from Server_debugger ")
            for i, row in enumerate(mysel):
                for j, value in enumerate(row):
                    worksheet.write(i, j, value)
            workbook.close()

            print ("Updating server activity log excel")
            workbook = Workbook(os.path.join(BASE_DIR,'static/server_activities_log.xlsx'))
            worksheet = workbook.add_worksheet()
            conn=sqlite3.connect(db_path)
            c=conn.cursor()
            mysel=c.execute("select * from Server_activity")
            for i, row in enumerate(mysel):
                for j, value in enumerate(row):
                    worksheet.write(i, j, value)
            workbook.close()

            print ("Update device thread starts sleeping for 15 s")
            time.sleep(15)
            
    except Exception as e:
            logServerDebugger(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Exception: Update server thread", str(e), db)

def getImageNumOverTime(img_source, detection_type, start_datetime, end_datetime):
    """
    Returns 2 arrays containing image information that satisfy the img_source, 
    detection type and time range input.
    1st array contains the number of occurence of each image per day.
    2nd array contains day (date) corrresponding to the array of image occurence.
    """
    x_array = []
    y_array = []
    if img_source:
        allImages = Images.query.all()
        selectedImages = Images.query.filter_by(source = img_source)
    else:
        allImages = Images.query.all()
        selectedImages = allImages

    img_timestamps = []
    for image in selectedImages:
        bool1 = 0
        bool2 = 0
        #convert to datetime object
        datetime_obj = datetime.datetime.strptime(image.timestamp,"%Y-%m-%d %H:%M:%S")
        #if the time range is given, filter the time
        if start_datetime and end_datetime:
            if start_datetime <= datetime_obj <= end_datetime:
                bool1 = 1
        else:
            bool1 = 1

        if detection_type:
            if detection_type in image.tag:
                bool2 = 1
            elif detection_type == "any":
                bool2 = 1
        else:
            bool2 = 1

        if bool1 and bool2:
            img_timestamps.append(datetime_obj)

    sorted_img_timestamps = sorted(img_timestamps)
    sorted_img_timestamps_string = [date.strftime("%Y-%m-%d") for date in sorted_img_timestamps]
    # sorted_img_timestamps_string = [date.strftime("%Y-%m-%d %H-%M") for date in sorted_img_timestamps]

    for timestamp in sorted_img_timestamps_string:
        try:
            #find the index number of the same timestamp in
            # array if it exist.
            # if the timestamp does not exist, then index()
            # function will return error
            indexnum = x_array.index(timestamp)
            y_array[indexnum] = y_array[indexnum] + 1
            
        except:
            x_array.append(timestamp)
            y_array.append(1)
    return x_array, y_array


def map_XYvalues_to_Larger_range(bigger_x_array, inputX_array, inputY_array):
    """
    Maps information from a smaller x and y arrays to a bigger x array containing more elements.
    This is done for plotting using same x array.
    """
    counter = 0
    bigger_y_array = [0]*len(bigger_x_array)
    for item in inputX_array:
        try:
            indexnum = bigger_x_array.index(item)
            bigger_y_array[indexnum] = inputY_array[counter]
        except:
            print("Error! The bigger X array does not contain all elements of smaller x array.")
        counter = counter + 1

    return bigger_y_array


def getDatetimeObject(datetime_str, formats):
    """
    This function returns a datetime object by trying to
    read datetime string using multiple formats specified within list.
    """
    bool = 0
    for format in formats:
        
        try:
            datetime_object = datetime.datetime.strptime(datetime_str,format)
            bool = 1
        except:
            pass

    if bool == 1:
        return datetime_object
    else:
        return None


def check_and_create_img_thumbnail(BASE_DIR, path, max_size_in_kb, data):
    """ 
    check_and_create_img_thumbnail(dir, filename, max_size_in_kb)
    Returns the boolean indicating whether input file is greater than max_size_in_kb.
    Also returns the path of the compressed image (if oversized), else returns original file path.
    """
    #read the img
    # path = dir + filename
    filename = os.path.basename(path)
    absolute_path =  os.path.join(BASE_DIR, path)
    dir = os.path.dirname(path)
    path2 = dir + "/thumbnail_" + filename
    absolute_path2 =  os.path.join(BASE_DIR, path2)

    if os.path.exists(absolute_path2):
        print("existing thumbnail found")
        # if we have thumbnail exist, change target path to that file
        path = path2
        absolute_path = absolute_path2

    im = Image.open(absolute_path)
    # check filesize
    file_size = os.stat(absolute_path)
    print("Size of file :", file_size.st_size, "bytes")
    # size_bool indicates whether the original file passed into function is over the limit
    size_bool = 0
    while (int(file_size.st_size)/1024) > max_size_in_kb:
        size_bool = 1
        #create thumbnail
        MAX_SIZE = (im.size[0]*0.8, im.size[1]*0.8)
        im.thumbnail(MAX_SIZE)
        # creating thumbnail
        path = dir + "/thumbnail_" + filename
        absolute_path =  os.path.join(BASE_DIR, path)
        im.save(absolute_path)
        # im.show()
        file_size = os.stat(absolute_path)
        print("Compressed image to size:", file_size.st_size)

    return size_bool, path

def battery_health_algorithm(battery_voltage, battery_current):
        full_battery_voltage = 13
        min_battery_voltage = 11.3
        battery_operating_range = full_battery_voltage - min_battery_voltage
        battery_level = ((float(battery_voltage) - min_battery_voltage)/battery_operating_range)*100
        battery_level = int((battery_level * 100) + 0.5) / 100.0 # Adding 0.5 rounds it up

        if battery_level > 100:
            battery_level = 100
        elif battery_level < 0:
            battery_level = 0
        
        # Battery stats
        current_battery_voltage = float(battery_voltage)
        current_battery_current = float(battery_current)


        current_power_level = current_battery_voltage*current_battery_current*10**-3 #10^-3 because current is in mA
        current_power_level = int((current_power_level * 10000) + 0.5) / 10000.0 # Adding 0.5 rounds it up


        if current_battery_voltage > full_battery_voltage:
            stat = "Charging"
        elif current_battery_voltage == full_battery_voltage:
            stat = "Fully charged"
        elif current_battery_voltage > min_battery_voltage and current_battery_voltage < 13:
            stat = "Operating"
        elif current_battery_voltage <= min_battery_voltage:
            stat = "Running out"
        else:
            stat = "Unknown"

        db.session.commit()
        return battery_level, current_power_level, stat