from operator import contains
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy 
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import sys
import random
import pytz
import time
import datetime
import arrow
import os
import sqlite3
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView 
# import git
from functools import wraps
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
import urllib.request
from werkzeug.utils import secure_filename
import shutil
from os.path import exists
from elephant_functions import *

#Import database rows declaration, and also Flask app objects
from app_config import Images, end_device, User, Detection, Server_activity, app, api, db, db_path, BASE_DIR

x_array = []
y_array = []
img_source = None

detection_type = None
start_datetime = None
end_datetime = None

if img_source:
    allImages = Images.query.filter_by(source = img_source)
else:
    allImages = Images.query.all()



for image in allImages:
    try:
        #find the index number of the same timestamp in
        # array if it exist.
        # if the timestamp does not exist, then index()
        # function will return error
        indexnum = x_array.index(image.timestamp)
        y_array[indexnum] = y_array[indexnum] + 1

    except:
        x_array.append(image.timestamp)
        y_array.append(1)

img_timestamps = []
for image in allImages:
    img_timestamps.append(datetime.datetime.strptime(image.timestamp,"%Y-%m-%d %H-%M"))

sorted_img_timestamps = sorted(img_timestamps)
sorted_img_timestamps_string = [date.strftime("%Y-%m-%d %H-%M") for date in sorted_img_timestamps]
print(sorted_img_timestamps_string)
print(x_array)
print(y_array)
