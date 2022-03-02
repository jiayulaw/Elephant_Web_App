#turorial: https://www.tutorialspoint.com/sqlite/sqlite_python.htm


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
from DB_class import Images, end_device, User, Detection, Server_activity, app, api, db, db_path, BASE_DIR
import threading
import pytz
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import logging

def checkFilePath(file_path, absolute_file_path, img_source, filename, BASE_DIR, app):
        # if the directory already contain file with same name, then rename before 
        # saving the file to prevent overwrite
        while exists(absolute_file_path):
            n = random.randint(0,999999)
            namestr = img_source + "/" + str(n) + "_" + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], namestr)
            absolute_file_path = os.path.join(BASE_DIR, file_path)
        return file_path, absolute_file_path


# this function converts a datetime object that contains 
# a local timezone attribute to UTC time
def Local2UTC_time(LocalTime):
    EpochSecond = time.mktime(LocalTime.timetuple())
    utcTime = datetime.datetime.utcfromtimestamp(EpochSecond)
    return utcTime

def getMalaysiaTime(timestamp):
    UTC_timestamp = Local2UTC_time(timestamp)
    Malaysia_timezone_timestamp = UTC_timestamp + datetime.timedelta(hours=8)
    date_created = Malaysia_timezone_timestamp.strftime("%d/%m/%Y %I:%M:%S %p")
    return date_created

def update_server_directory_images():
    # check directory to update any new images added through SFTP or direct upload to server
    for device_name in ['end device 1', 'end device 2', 'end device 3', 'uploaded']:
        directory = rf"static/image uploads/{device_name}" 
        directory2 = os.path.join(BASE_DIR, directory)
        for filename in os.listdir(directory2):
            try:
                if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".jpeg"):
                    #strip away file format extension
                    str1 = filename.split(".")[0]
                    #strip between datetime and detection type
                    arr1 = str1.split("-x-")
                    date_time = arr1[0]
                    detection_type = arr1[1]
                    date_time_obj = datetime.datetime.strptime(date_time, "%Y-%m-%d %H-%M")
                    path = os.path.join(directory, filename)
                    path = f"static/image uploads/{device_name}/"+filename
                    result = Images.query.filter_by(path=path).first()
                    if result:
                        print("the file with same name already saved")
                    else:
                        new_image = Images(timestamp = date_time, path = path, source=device_name, tag = detection_type, latitude ="", longitude = "")
                        db.session.add(new_image)
                        db.session.commit()
                else:
                    continue
            except:
                print("Filename is not formatted correctly, but it is ok, just ignore")


def logServerActivity(timestmp, type, description, db):
    new_activity = Server_activity(timestamp = timestmp, type = type, description=description )
    db.session.add(new_activity)
    db.session.commit()


class myThread (threading.Thread):
   def __init__(self, threadID, name, delay):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = delay

   def run(self):
       #watchdog tutorial
       #https://thepythoncorner.com/posts/2019-01-13-how-to-create-a-watchdog-in-python-to-look-for-filesystem-changes/#
       #https://michaelcho.me/article/using-pythons-watchdog-to-monitor-changes-to-a-directory
      def on_created(event):
          print(f"CHANGE DETECTED IN IMAGE DIRECTORY - {event.src_path} has been created!")
          update_server_directory_images()

      def on_deleted(event):
          print(f"CHANGE DETECTED IN IMAGE DIRECTORY - {event.src_path} has been deleted!")
          update_server_directory_images()
      def on_modified(event):
          print(f"CHANGE DETECTED IN IMAGE DIRECTORY - {event.src_path} has been modified!")
          update_server_directory_images()

      def on_moved(event):
          print(f"CHANGE DETECTED IN IMAGE DIRECTORY - {event.src_path} was moved to {event.dest_path}")
          update_server_directory_images()

      patterns = ["*"]
      ignore_patterns = None
      ignore_directories = False
      case_sensitive = True
      my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
      my_event_handler.on_created = on_created
      my_event_handler.on_deleted = on_deleted
      my_event_handler.on_modified = on_modified
      my_event_handler.on_moved = on_moved
     
      path = os.path.join(BASE_DIR, 'static/image uploads')
    #   path = r"C:\Users\user10\Desktop\Hobby\Programming\EEEY3 Project\Web App\Elephant_Web_App_v2\static\image uploads"
      go_recursively = True
      my_observer = Observer()
      my_observer.schedule(my_event_handler, path, recursive=go_recursively)
      my_observer.start()

      print ("Starting " + self.name)
      while 1:
          f = open("test-thread888-running.txt", "w") 
          f.write("The thread888 is running!!")
          f.close() 
          f = open("test-thread888-running.txt", "r")
          print(f.read())

          cursor = end_device.query.all()        
          cursor = end_device.query.all()
          UTCnow = datetime.datetime.utcnow() # current date and time in UTC
          for device in cursor:
              datetime_object = datetime.datetime.strptime(device.last_seen, '%d/%m/%Y, %H:%M:%S')
              #hardcode the timezone as Malaysia timezone
              timezone = pytz.timezone("Asia/Kuala_Lumpur")
              #add timezone attribute to datetime object
              datetime_object_timezone = timezone.localize(datetime_object, is_dst=None)
              datetime_str_formatted = datetime.datetime.strftime(datetime_object_timezone, '%I:%M:%S %p, %d/%m/%Y')
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
              if diff_in_minutes > 30:
                  if device.status != "Offline":
                      logServerActivity(getMalaysiaTime(datetime.datetime.now()), "Status change", "Device - " + device.name + " changed status from " + device.status + " to " + "Offline", db)
                      device.status = "Offline"
            
          db.session.commit()
          time.sleep(self.counter)
     
      print ("Exiting " + self.name)




def getImageNumOverTime(img_source, detection_type, start_datetime, end_datetime):
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
        datetime_obj = datetime.datetime.strptime(image.timestamp,"%Y-%m-%d %H-%M")
        #if the time range is given, filter the time
        if start_datetime and end_datetime:
            if start_datetime <= datetime_obj <= end_datetime:
                bool1 = 1
        else:
            bool1 = 1

        if detection_type:
            if detection_type in image.tag:
                bool2 = 1
        else:
            bool2 = 1

        if bool1 and bool2:
            img_timestamps.append(datetime_obj)

    sorted_img_timestamps = sorted(img_timestamps)
    sorted_img_timestamps_string = [date.strftime("%Y-%m-%d %H-%M") for date in sorted_img_timestamps]

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
    counter = 0
    bigger_y_array = [0]*len(bigger_x_array)
    for item in inputX_array:
        try:
            indexnum = bigger_x_array.index(item)
            bigger_y_array[indexnum] = inputY_array[counter]
        except:
            print("Error! The bigger X array does not contain all elements of smaller x array.")

    return bigger_y_array