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

def create_DB_Tables():
    app = Flask(__name__)
    api = Api(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + 'database.sqlite'
    app.config['SECRET_KEY'] = 'thisisasecretkey'
    db = SQLAlchemy(app)

    class end_device(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        status = db.Column(db.Integer, nullable=False)
        message = db.Column(db.Integer, nullable=False)

        def __repr__(self):
            return f"end_device(name = {name}, views = {status}, likes = {message})"

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(20), nullable=False, unique=True)#username must be unique
        password = db.Column(db.String(80), nullable=False)
        access_level = db.Column(db.String(20), nullable=False)
        

    db.create_all()



def create_DBtable():
    #Connect to / Open sqlite db
    conn = sqlite3.connect('users.db')
    print ("Opened database successfully");
    #Create table
    conn.execute('''CREATE TABLE users_table
            (NAME           TEXT    NOT NULL,
            PW            TEXT     NOT NULL,
            ACCESS         INT);''')
    print ("Table created successfully")
    #Cursor selection
    cursor = conn.execute("SELECT NAME, PW, ACCESS from users_table")
    #print out using cursor
    for row in cursor:
        print ("NAME = ", row[0])
        print ("PW = ", row[1])
        print ("ACCESS = ", row[2])
        print ("Operation done successfully")
    #Close connector
    conn.close()


def DB_insert_user(DB_name, DB_table, username, password, access):
    conn = sqlite3.connect('users.db')
    conn.execute("INSERT INTO users_table (NAME, PW, ACCESS) \
        VALUES ('elephantking', 'pw', 0)")
    conn.commit()
    print ("Records created successfully")
    #Cursor selection
    cursor = conn.execute("SELECT NAME, PW, ACCESS from users_table")
    #print out using cursor
    for row in cursor:
        print ("NAME = ", row[0])
        print ("PW = ", row[1])
        print ("ACCESS = ", row[2])
    conn.close()


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


