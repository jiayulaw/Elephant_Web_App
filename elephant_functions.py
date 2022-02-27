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

def update_server_directory_images(BASE_DIR, Images, data, db):
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
                        new_image = Images(timestamp = date_time, path = path, source=data.station, tag = detection_type, latitude ="", longitude = "")
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