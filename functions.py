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





