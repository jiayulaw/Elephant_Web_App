import ast
from operator import contains
from flask import Flask, render_template, request, redirect, url_for, flash, session
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


#------------------------------------------------------------
#-------------------------User Auth-------------------------
#------------------------------------------------------------

bcrypt = Bcrypt(app)

hashed_password = bcrypt.generate_password_hash("print")
print("Hashed", hashed_password)