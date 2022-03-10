# Run this script as main to initialize database
# default admin user will also be created

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy 
import os
import sqlite3
from flask_bcrypt import Bcrypt
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
import datetime
from elephant_functions import *

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

class Detection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(100), nullable=False)
    device = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Integer, nullable=True)
    longitude = db.Column(db.Integer, nullable=True)
    

class Server_activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.String(100), nullable=True)
    timezone = db.Column(db.String(100), nullable=True)

class Images(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(100), nullable=False, unique=True)
    path2 = db.Column(db.String(100), nullable=True, unique=True)
    json_path = db.Column(db.String(100), nullable=True, unique=True)
    source = db.Column(db.String(100), nullable=False)
    uploader = db.Column(db.String(100), nullable=True)
    tag = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Integer, nullable=True)
    longitude = db.Column(db.Integer, nullable=True)
    upload_date = db.Column(db.String(100), nullable=True)
    timezone = db.Column(db.String(100), nullable=True)

class end_device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    last_seen = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(100), nullable=True)
    timezone = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"Device_Stat_pipeline(name = {name}, last_seen = {last_seen}, message = {message})"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)#username must be unique
    password = db.Column(db.String(80), nullable=False)
    access_level = db.Column(db.String(20), nullable=False)
    date_created = db.Column(db.String(100), nullable=True)
    last_seen = db.Column(db.String(100), nullable=True)
    
    def has_role(self, role_name):
        #my_role = User.query.filter_by(access_level=role_name).first()
        if role_name == self.access_level:
            return True
        else:
            return False
            
if __name__ == "__main__":
    db.create_all()
    # Create default admin user
    bcrypt = Bcrypt(app)
    hashed_password = bcrypt.generate_password_hash("pwpw")
    date = getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p")
    new_user = User(username = "elephantking", password=hashed_password, access_level = "admin", date_created = date)
    db.session.add(new_user)
    db.session.commit()
    new_user = User(username = "jiayu", password=hashed_password, access_level = "admin", date_created = date)
    db.session.add(new_user)
    db.session.commit()
    new_user = User(username = "vinshen", password=hashed_password, access_level = "admin", date_created = date)
    db.session.add(new_user)
    db.session.commit()
    new_user = User(username = "jonathan", password=hashed_password, access_level = "admin", date_created = date)
    db.session.add(new_user)
    db.session.commit()
    new_user = User(username = "hoipang", password=hashed_password, access_level = "admin", date_created = date)
    db.session.add(new_user)
    db.session.commit()
    print("Default admin user created successfully")


