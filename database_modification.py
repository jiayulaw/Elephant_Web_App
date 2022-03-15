from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy 
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import sys
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
app = Flask(__name__, static_folder='static')
api = Api(app)
#need to set base dir to prevent path issue in pythonanywhere
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database.sqlite")
#------------------------------------------------------------
#-------------------------Database Config-------------------------
#------------------------------------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SECRET_KEY'] = 'thisisasecretkey'
db = SQLAlchemy(app)

from app_config import Images, end_device, User

command = "DELETE FROM Images WHERE timestamp='2022-01-28 00:00:00';"
command = "DELETE FROM Images;"
conn = sqlite3.connect(db_path)
cursor = conn.execute(command)
conn.commit()
print ("Records created successfully")
conn.close()


# new_image = Images(timestamp = "2021-10", path = "", source="station 1", tag = "bello", latitude = 90, longitude = 90)
# db.session.add(new_image)
# db.session.commit()