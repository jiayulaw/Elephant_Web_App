import ast
from operator import contains
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy 
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
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
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
import urllib.request
from werkzeug.utils import secure_filename
import shutil
from os.path import exists
from elephant_functions import *
import threading


#Import database rows declaration, and also Flask app objects
from app_config import *

#------------------------------------------------------------
#-------------------------Initialization of variables-------------------------
#------------------------------------------------------------
class DataStorage():
    dontRequest = None
    station = "end device 1"
    from_date_str = getMalaysiaTime(datetime.datetime.now(), "%Y-%m-%d %H:%M")
    to_date_str = getMalaysiaTime(datetime.datetime.now(), "%Y-%m-%d %H:%M")
    
    detection_type = "any"
    input_date_str = None
    debug_arr = []

data = DataStorage()


#=============================================================================================
# Background threads mechanism
#=============================================================================================
#------------------------------------------------------------
#-------------------------Image update thread-------------------------
#------------------------------------------------------------
"""Following are the confgis of a thread that listens for change in 
directory and triggers the check and record of unrecorded image file."""
def on_created(event):
        print(f"CHANGE DETECTED IN IMAGE DIRECTORY - {event.src_path} has been created!")
        update_server_directory_images(Images, BASE_DIR, event.src_path)

def on_deleted(event):
    print(f"CHANGE DETECTED IN IMAGE DIRECTORY - {event.src_path} has been deleted!")
    update_server_directory_images(Images, BASE_DIR, event.src_path)
def on_modified(event):
    print(f"CHANGE DETECTED IN IMAGE DIRECTORY - {event.src_path} has been modified!")
    update_server_directory_images(Images, BASE_DIR, event.src_path)

def on_moved(event):
    print(f"CHANGE DETECTED IN IMAGE DIRECTORY - {event.src_path} was moved to {event.dest_path}")
    update_server_directory_images(Images, BASE_DIR, event.src_path)

    

patterns = ["*"]
ignore_patterns = None
ignore_directories = False
case_sensitive = True
my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
my_event_handler.on_created = on_created
my_event_handler.on_deleted = on_deleted
my_event_handler.on_modified = on_modified
my_event_handler.on_moved = on_moved
#relative path that needs to be checked for changes
path = os.path.join(BASE_DIR, 'static/image uploads')
go_recursively = True
my_observer = Observer()
my_observer.schedule(my_event_handler, path, recursive=go_recursively)
my_observer.start()       

#------------------------------------------------------------
#-------------------------Device status update thread-------------------------
#------------------------------------------------------------
thread1 = threading.Thread(target = update_device_status_thread)
# thread1.daemon = True
thread1.start()

#=============================================================================================
# Forms initialization
#=============================================================================================
class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Username"})
    
    password = PasswordField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Password"})
   
    # role = StringField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Access code"})

    role = SelectField(u'account type', choices=[('admin', 'Admin'), ('explorer', 'Explorer'), ('guest', 'Guest')])
    submit = SubmitField("Register")
    #Checks whether the username is redundant
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username = username.data).first()

        if existing_user_username:
            raise ValidationError(
                "That username already exists. Please choose a different one.")


class ChangePasswordForm(FlaskForm):
    # username = StringField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Username"})
    
    password = PasswordField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Current password"})

    new_password = PasswordField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "New password"})
    new_password2 = PasswordField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Confirm new password"})
   
    submit = SubmitField("Change password")

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Username"})
    
    password = PasswordField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Password"})
    
    submit = SubmitField("Login")

#=============================================================================================
# User Authentication System
#============================================================================================= 
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# login_manager.refresh_view = 'relogin'
# login_manager.needs_refresh_message = (u"Session timedout, please re-login")
# login_manager.needs_refresh_message_category = "info"

# code to run before every request
@app.before_request
def before_request():
    # permanent session
    session.permanent = True
    # session lifetime
    app.permanent_session_lifetime = datetime.timedelta(minutes=20)
    # reset lifetime timer for each new request
    session.modified = True

# define method to load user id
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#=============================================================================================
# Admin System
#=============================================================================================            
#------------------------------------------------------------
#-------------------------User role wrapper-------------------------
#------------------------------------------------------------
def require_role(role, role2):
    """make sure user has this role"""
    def decorator(func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            if not (current_user.has_role(role) or current_user.has_role(role2)):
                return redirect("/")
            else:
                return func(*args, **kwargs)
        return wrapped_function
    return decorator

#------------------------------------------------------------
#-------------------------Flask Admin (NOT USED ANYMORE) -------------------------
#------------------------------------------------------------
#Following class is user defined ModelView inherited from default 
# class MyModelView(ModelView):
#     #defines the condition for /admin/user to be accessible
#     def is_accessible(self):
#         return current_user.is_authenticated and current_user.has_role('admin')
#     #defines what to do if inaccesible
#     def inaccessible_callback(self, name, **kwargs):
#         return redirect(url_for('login'))

# #Following class is user defined AdminIndexView inherited from default 
# class MyAdminIndexView(AdminIndexView):
#     #defines the condition for URL '/admin' to be accessible
#     def is_accessible(self):
#         return current_user.is_authenticated and current_user.has_role('admin')
#     #defines what to do if inaccesible
#     def inaccessible_callback(self, name, **kwargs):
#         return redirect(url_for('dashboard'))

# #create admin object - template_mode defines which template we use from the lib for frontend
# admin = Admin(app, index_view = MyAdminIndexView(), template_mode = 'bootstrap4')
# #add ModelView class to admin
# admin.add_view(MyModelView(User, db.session))


#=============================================================================================
# REST API
#=============================================================================================  
device_stat_put_args = reqparse.RequestParser()
#help parameter is similar to error message we send back to sender when there is no valid input
#required parameter means the field is not optional
device_stat_put_args.add_argument("name", type=str, help="Device name is required", required=True)
device_stat_put_args.add_argument("last_seen", type=str, help="Device last_seen is required", required=True)
device_stat_put_args.add_argument("message", type=str, help="Device message is required", required=True)
device_stat_put_args.add_argument("status", type=str, help="Device status is required", required=True)
device_stat_put_args.add_argument("battery_voltage", type=str, help="Device battery voltage?", required=True)
device_stat_put_args.add_argument("battery_current", type=str, help="Device battery current?", required=True)
device_stat_put_args.add_argument("battery_temp_1", type=str, help="Device battery temp?", required=True)
device_stat_put_args.add_argument("battery_temp_2", type=str, help="Device battery temp?", required=True)
device_stat_put_args.add_argument("ambient_temp", type=str, help="Device ambient temp?", required=True)
device_stat_put_args.add_argument("battery_level", type=str, help="battery_level?")
device_stat_put_args.add_argument("battery_status", type=str, help="battery_status?")
device_stat_put_args.add_argument("instantaneous_power", type=str, help="instantaneous_power?")

device_stat_update_args = reqparse.RequestParser()
device_stat_update_args.add_argument("name", type=str, help="Device name is required", required=True)
device_stat_update_args.add_argument("last_seen", type=str, help="Device last_seen is required", required=True)
device_stat_update_args.add_argument("message", type=str, help="Device message is required", required=True)
device_stat_update_args.add_argument("status", type=str, help="Device status is required", required=True)
device_stat_update_args.add_argument("battery_voltage", type=str, help="Device battery voltage?", required=True)
device_stat_update_args.add_argument("battery_current", type=str, help="Device battery current?",required=True)
device_stat_update_args.add_argument("battery_temp_1", type=str, help="Device battery temp?", required=True)
device_stat_update_args.add_argument("battery_temp_2", type=str, help="Device battery temp?", required=True)
device_stat_update_args.add_argument("ambient_temp", type=str, help="Device ambient temp?", required=True)
device_stat_update_args.add_argument("battery_level", type=str, help="battery_level?")
device_stat_update_args.add_argument("battery_status", type=str, help="battery_status?")
device_stat_update_args.add_argument("instantaneous_power", type=str, help="instantaneous_power?")


resource_fields = {
	'id': fields.Integer,
	'name': fields.String,
	'last_seen': fields.String,
	'message': fields.String,
    'status': fields.String,
    'battery_current': fields.String,
    'battery_current': fields.String,   
    'battery_temp_1': fields.String,
    'battery_temp_2': fields.String,
    'ambient_temp': fields.String
}

#marshal_with to serialize object
class Device_Stat_pipeline(Resource):
    @marshal_with(resource_fields)
    def get(self, device_id):
        result = end_device.query.filter_by(id=device_id).first()
        if not result:
            abort(404, message="Could not find device record in database")
        return result, 200

    @marshal_with(resource_fields)
    def put(self, device_id):
        args = device_stat_put_args.parse_args()
        result = end_device.query.filter_by(id=device_id).first()

        datetime_object = datetime.datetime.strptime(args['last_seen'], '%Y-%m-%d %H-%M-%S')
        #hardcode the timezone as Malaysia timezone
        timezone = pytz.timezone("Asia/Kuala_Lumpur")
        #add timezone attribute to datetime object
        datetime_object_timezone = timezone.localize(datetime_object, is_dst=None)
        datetime_str_formatted = datetime.datetime.strftime(datetime_object_timezone, '%I:%M:%S %p, %d/%m/%Y')

        if not result:
            battery_level, instantaneous_power, battery_status = battery_health_algorithm(args['battery_voltage'], args['battery_current'])
            device_record = end_device(id=device_id, name=args['name'], last_seen=datetime_str_formatted, status=args['status'], message=args['message'], battery_voltage =args['battery_voltage'] , battery_current =args['battery_current'], battery_temp_1 =args['battery_temp_1'], battery_temp_2 =args['battery_temp_2'], ambient_temp =args['ambient_temp'], battery_level = battery_level, instantaneous_power = instantaneous_power, battery_status = battery_status)
            db.session.add(device_record)
            
            db.session.commit()
            return_val = device_record
            logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "End device added", "Device - " + args['name'] + " added to database.", db)
            number = 201

        else: 
            if args['name']: 
                result.name = args['name']

            if args['last_seen']:
                result.last_seen = datetime_str_formatted
                
            if args['message']:
                result.message = args['message']

            if args['battery_voltage']:
                result.battery_voltage = args['battery_voltage']

            if args['battery_current']:
                result.battery_current = args['battery_current']

            if args['battery_temp_1']:
                result.battery_temp_1 = args['battery_temp_1']

            if args['battery_temp_2']:
                result.battery_temp_2 = args['battery_temp_2']

            if args['ambient_temp']:
                result.ambient_temp = args['ambient_temp']
            
            if args['status']:
                if result.status != args['status']:
                    logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Status change", "Device - " + args['name'] + " changed status from " + result.status + " to " + args['status'], db)      
                result.status = args['status']

            result.battery_level, result.instantaneous_power, result.battery_status = battery_health_algorithm(result.battery_voltage, result.battery_current)
            db.session.commit()
            return_val = result
            number = 200

        return return_val, number
        

    @marshal_with(resource_fields)
    def patch(self, device_id):
        args = device_stat_update_args.parse_args()
        result = end_device.query.filter_by(id=device_id).first()
        if not result:
            abort(404, message="Device record doesn't exist, cannot update")

        if args['name']:
            result.name = args['name']

        if args['last_seen']:
            datetime_object = datetime.datetime.strptime(args['last_seen'], '%Y-%m-%d %H-%M-%S')
            #hardcode the timezone as Malaysia timezone
            timezone = pytz.timezone("Asia/Kuala_Lumpur")
            #add timezone attribute to datetime object
            datetime_object_timezone = timezone.localize(datetime_object, is_dst=None)
            datetime_str_formatted = datetime.datetime.strftime(datetime_object_timezone, '%I:%M:%S %p, %d/%m/%Y')
            result.last_seen = datetime_str_formatted
            
        if args['message']:
            result.message = args['message']

        if args['battery_voltage']:
            result.battery_voltage = args['battery_voltage']

        if args['battery_current']:
            result.battery_current = args['battery_current']

        if args['battery_temp_1']:
            result.battery_temp_1 = args['battery_temp_1']

        if args['battery_temp_2']:
            result.battery_temp_2 = args['battery_temp_2']

        if args['ambient_temp']:
            result.ambient_temp = args['ambient_temp']
        
        if args['status']:
            if result.status != args['status']:
                logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Status change", "Device - " + args['name'] + " changed status from " + result.status + " to " + args['status'], db)      

            result.status = args['status']
    
        db.session.commit()
        return result, 200

    # def delete(self, device_id):
    # 	# need to abort if the database doesnt exist, else might cause error
    #     # #abort_if_video_id_doesnt_exist(video_id)
    # 	del end_device[device_id]
    # 	return '', 204


api.add_resource(Device_Stat_pipeline, "/device_stat/<int:device_id>")

#------------------------------------------------------------
#------------------------------------------------------------
#------------------------------------------------------------





@app.route("/update_image")
@login_required
@require_role(role="admin", role2 ="explorer")
def update_image():

    update_server_directory_images(Images, BASE_DIR)
        
    return redirect("/display_image")

@app.route("/")
@app.route("/dashboard")
@login_required #we can only access dashboard when logged in
def dashboard():
    navbar_items = [["Device status", "#device_status"], ["Elephant Radar", "#elephant_radar"]]
    # Filter images from database
    image1 = []
    image2 = []
    image3 = []
    devices_name = []
    devices_last_seen = []
    devices_message = []
    devices_status = []
    devices_battery_voltage = []
    devices_battery_current = []
    devices_battery_level = []
    devices_power_level = []
    devices_battery_status = []


    descending = Images.query.order_by(Images.id.desc()).filter_by(source = "end device 1")

    result = descending.first()
    if result:
        image1.append(result.path)
        image1.append(result.timestamp)
        image1.append(result.tag)
        image1.append(result.latitude)
        image1.append(result.longitude)
    db.session.commit()

    descending = Images.query.order_by(Images.id.desc()).filter_by(source = "end device 2")

    result = descending.first()
    if result:
        image2.append(result.path)
        image2.append(result.timestamp)
        image2.append(result.tag)
        image2.append(result.latitude)
        image2.append(result.longitude)
    db.session.commit()

    descending = Images.query.order_by(Images.id.desc()).filter_by(source = "end device 3")

    result = descending.first()
    if result:
        image3.append(result.path)
        image3.append(result.timestamp)
        image3.append(result.tag)
        image3.append(result.latitude)
        image3.append(result.longitude)
    db.session.commit()

    cursor = end_device.query.all()
    for device in cursor:
        # append all data to arrays to be displayed on web page
        devices_name.append(device.name)
        devices_last_seen.append(device.last_seen)
        
        devices_status.append(device.status)
        devices_message.append(device.message)

        devices_battery_current.append(device.battery_current)
        devices_battery_voltage.append(device.battery_voltage)

        devices_battery_level.append(device.battery_level)
        devices_power_level.append(device.instantaneous_power)
        devices_battery_status.append(device.battery_status)

    #  Analytics graph display on home page
    #Filter the number of images for past 7 days
    end_datetime = datetime.datetime.strptime(getMalaysiaTime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
    start_datetime = end_datetime - datetime.timedelta(days=7)
    this_week_x_array, this_week_y_array = getImageNumOverTime(None, None, start_datetime, end_datetime)
    this_week_device1_x_array, this_week_device1_y_array = getImageNumOverTime("end device 1", None, start_datetime, end_datetime)
    this_week_device2_x_array, this_week_device2_y_array = getImageNumOverTime("end device 2", None, start_datetime, end_datetime)
    this_week_device3_x_array, this_week_device3_y_array = getImageNumOverTime("end device 3", None, start_datetime, end_datetime)


    this_week_big_Y_array_device1 = map_XYvalues_to_Larger_range(this_week_x_array, this_week_device1_x_array, this_week_device1_y_array)
    this_week_big_Y_array_device2 = map_XYvalues_to_Larger_range(this_week_x_array, this_week_device2_x_array, this_week_device2_y_array)
    this_week_big_Y_array_device3 = map_XYvalues_to_Larger_range(this_week_x_array, this_week_device3_x_array, this_week_device3_y_array)

    return render_template('index.html', active_state = "dashboard", image1 = image1, image2 = image2, image3 = image3, 
    devices_name = devices_name, devices_last_seen = devices_last_seen, devices_message = devices_message, 
    devices_status = devices_status, devices_battery_current = devices_battery_current, 
    devices_battery_voltage = devices_battery_voltage, devices_battery_level = devices_battery_level, 
    devices_battery_status = devices_battery_status, devices_power_level = devices_power_level, navbar_items = navbar_items,
    this_week_x_array = this_week_x_array, this_week_y_array = this_week_y_array, this_week_big_Y_array_device1 = this_week_big_Y_array_device1,
    this_week_big_Y_array_device2 = this_week_big_Y_array_device2, this_week_big_Y_array_device3 = this_week_big_Y_array_device3)

@app.route("/device_monitoring")
@login_required #we can only access dashboard when logged in
def device_monitoring():
    navbar_items = []
    devices_name = []
    devices_last_seen = []
    devices_message = []
    devices_status = []
    devices_battery_voltage = []
    devices_battery_current = []
    devices_battery_level = []
    devices_power_level = []
    devices_battery_status = []
    devices_battery_temp_1 = []
    devices_battery_temp_2 = []
    devices_ambient_temp = []
    images = []
    images.append(check_and_create_img_thumbnail(BASE_DIR, 'static/img/end_device.png', 100, data)[1])


    cursor = end_device.query.all()
    for device in cursor:
        # append all data to arrays to be displayed on web page
        devices_name.append(device.name)
        devices_last_seen.append(device.last_seen)
        
        devices_status.append(device.status)
        devices_message.append(device.message)

        devices_battery_temp_1.append(device.battery_temp_1)
        devices_battery_temp_2.append(device.battery_temp_2)
        devices_ambient_temp.append(device.ambient_temp)

        devices_battery_current.append(device.battery_current)
        devices_battery_voltage.append(device.battery_voltage)

        devices_battery_level.append(device.battery_level)
        devices_power_level.append(device.instantaneous_power)
        devices_battery_status.append(device.battery_status)

    return render_template('device_monitoring.html', active_state = "device", devices_name = devices_name, 
    devices_last_seen = devices_last_seen, devices_message = devices_message, devices_status = devices_status, 
    devices_battery_current = devices_battery_current, devices_battery_voltage = devices_battery_voltage, 
    devices_battery_level = devices_battery_level, devices_battery_status = devices_battery_status, 
    devices_power_level = devices_power_level, devices_battery_temp_1 = devices_battery_temp_1,
    devices_battery_temp_2 = devices_battery_temp_2, devices_ambient_temp = devices_ambient_temp, navbar_items = navbar_items, images = images)

# @app.route('/update_server', methods=['POST'])
# def webhook():
#     repo = git.Repo('./Elephant_Project_Web_Application')
#     origin = repo.remotes.origin

#     repo.create_head('main', origin.refs.main).set_tracking_branch(origin.refs.main).checkout()
#     origin.pull()
#     return 'Updated PythonAnywhere successfully', 200

@app.route("/login", methods = ['GET', 'POST'])
def login():
    navbar_items = []
    msg = None
    form = LoginForm()
    if form.validate_on_submit():
        #Following line checks whether user is in database
        user = User.query.filter_by(username=form.username.data).first() 
        if user: #if user in database
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=False)
                user.authenticated = True
                current_time = getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p")
                user.last_seen = current_time
                logServerActivity(current_time, "Login", "User - " + current_user.username + " logged in.", db)
                db.session.commit() 
                return redirect(url_for('dashboard'))
        return render_template("login.html", form = form, msg = "Wrong username or password.")

    return render_template("login.html", form = form, msg = msg, navbar_items = navbar_items)

    
@app.route('/logout', methods = ['GET','POST'])
@login_required
def logout():
    logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Logout", "User - " + current_user.username + " logged out.", db)
    logout_user()
    current_user.authenticated = False
    return redirect(url_for('login'))


@app.route("/admin/register", methods = ['GET', 'POST'])
@login_required
@require_role(role="admin", role2 = "admin")
def register():
    navbar_items = [["Activity", url_for('admin_home')], ["Create account", url_for('register')], ["Manage", url_for('admin_manage')]]
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        date_created = getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p")


        new_user = User(username = form.username.data, password=hashed_password, role = form.role.data, date_created = date_created)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration Success', 'success_msg')
        logServerActivity(date_created, "Account creation", "User - " + current_user.username + " created another user account - " + form.username.data, db)
        return redirect("/admin/register")
    return render_template("register.html", form = form, msg = None, active_state = "admin", navbar_items = navbar_items)


@app.route("/user/change_password", methods = ['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        result = User.query.filter_by(username = current_user.username).first()
        if not result:
            return render_template("change_password.html", active_state = "account", form = form, msg = "Error! This no account no longer exist.") 
        if not  bcrypt.check_password_hash(result.password, form.password.data):
            return render_template("change_password.html", active_state = "account", form = form, msg = "Current password is incorrect.") 
            
        if not (form.new_password.data == form.new_password2.data):
            return render_template("change_password.html", active_state = "account", form = form, msg = "Inconsistent entry of new password.")

        # if the inputs pass all the verification, change password
        new_hashed_password = bcrypt.generate_password_hash(form.new_password.data)
        result.password = new_hashed_password
        db.session.commit() 

        flash('Password changed', 'success_msg')
        return render_template("change_password.html", active_state = "account", form = form, msg = None) 

    return render_template("change_password.html", active_state = "account", form = form, msg = None)  

@app.route("/admin/home", methods = ['GET', 'POST'])
@login_required
@require_role(role="admin", role2 = "admin")
def admin_home():
    navbar_items = [["Activity", url_for('admin_home')], ["Create account", url_for('register')], ["Manage", url_for('admin_manage')]]
    activity_description = []
    activity_date = []
    activity_type = []
    result = Server_activity.query.all()
    for row in result:
        activity_description.append(row.description)
        activity_date.append(row.timestamp)
        
        activity_type.append(row.type)
    db.session.commit()
    activity_description.reverse()
    activity_date.reverse()
    activity_type.reverse()
    return render_template("/admin/admin_home.html", active_state = "admin", activity_description = activity_description, activity_date = activity_date, activity_type = activity_type, navbar_items = navbar_items)

@app.route("/admin/admin_manage", methods = ['GET', 'POST'])
@login_required
@require_role(role="admin", role2 = "admin")
def admin_manage():
    navbar_items = [["Activity", url_for('admin_home')], ["Create account", url_for('register')], ["Manage", url_for('admin_manage')]]
    usernames = []
    user_roles = []
    user_ids = []
    user_date_created = []
    user_last_seen = []
    result = User.query.all()
    for row in result:
        user_ids.append(row.id)
        usernames.append(row.username)
        user_roles.append(row.role)
        user_date_created.append(row.date_created)
        user_last_seen.append(row.last_seen)
        
    db.session.commit()
    return render_template("/admin/admin_manage.html", active_state = "admin", user_ids = user_ids, usernames = usernames, user_roles = user_roles, user_date_created = user_date_created, user_last_seen = user_last_seen, navbar_items = navbar_items)


@app.route("/admin/delete_user/<user_id>")
@login_required
@require_role(role="admin", role2 = "admin")
def delete_user(user_id):
    result = User.query.filter(User.id == user_id).first()
    logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Account deletion", "User - " + current_user.username + " deleted another user account - " + result.username, db)
    User.query.filter(User.id == user_id).delete()
    db.session.commit()
    
    return redirect(url_for('admin_manage'))


@app.route("/analytics", methods = ['GET', 'POST'])
@login_required
@require_role(role="admin", role2 = "explorer")
def analytics():
    navbar_items = []

    # User inputs
    data.from_date_str   = request.args.get('from', getMalaysiaTime(datetime.datetime.now(), "%Y-%m-%d %H:%M")) #Get the from date value from the URL
    data.to_date_str     = request.args.get('to', getMalaysiaTime(datetime.datetime.now(), "%Y-%m-%d %H:%M"))   #Get the to date value from the URL
    
    if getDatetimeObject(data.from_date_str, ['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S']) == 0:
        from_date_str   = getMalaysiaTime(datetime.datetime.now(), "%Y-%m-%d %H:%M")
    if getDatetimeObject(data.to_date_str, ['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S']) == 0:
        to_date_str   = getMalaysiaTime(datetime.datetime.now(), "%Y-%m-%d %H:%M")


    # use try except to convert datetime string to datetime object
    from_date_obj = getDatetimeObject(data.from_date_str, ['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'])
    to_date_obj = getDatetimeObject(data.to_date_str, ['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'])
    #ensure time input is valid
    current_time = datetime.datetime.strptime(getMalaysiaTime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
    if to_date_obj > current_time:
        to_date_obj = current_time

    
    if from_date_obj > to_date_obj:
        from_date_obj = to_date_obj
    # get the desired format from datetime object
    data.from_date_str = datetime.datetime.strftime(from_date_obj, "%Y-%m-%d %H:%M:%S")
    data.to_date_str = datetime.datetime.strftime(to_date_obj, "%Y-%m-%d %H:%M:%S")

    detection_type       = request.args.get('detection_type','any')
    data.detection_type = detection_type
    # Hint: getImageNumOverTime(img_source, detection_type, start_datetime, end_datetime)
    #Filter the number of images based on input

    input_filter_x_array, input_filter_y_array = getImageNumOverTime(None, detection_type, from_date_obj, to_date_obj)
    input_filter_device1_x_array, input_filter_device1_y_array = getImageNumOverTime("end device 1", detection_type, from_date_obj, to_date_obj)
    input_filter_device2_x_array, input_filter_device2_y_array = getImageNumOverTime("end device 2", detection_type, from_date_obj, to_date_obj)
    input_filter_device3_x_array, input_filter_device3_y_array = getImageNumOverTime("end device 3", detection_type, from_date_obj, to_date_obj)


    input_filter_big_Y_array_device1 = map_XYvalues_to_Larger_range(input_filter_x_array, input_filter_device1_x_array, input_filter_device1_y_array)
    input_filter_big_Y_array_device2 = map_XYvalues_to_Larger_range(input_filter_x_array, input_filter_device2_x_array, input_filter_device2_y_array)
    input_filter_big_Y_array_device3 = map_XYvalues_to_Larger_range(input_filter_x_array, input_filter_device3_x_array, input_filter_device3_y_array)

    
    #Filter the number of images for all time
    all_time_x_array, all_time_y_array = getImageNumOverTime(None, None, None, None)
    all_time_device1_x_array, all_time_device1_y_array = getImageNumOverTime("end device 1", None, None, None)
    all_time_device2_x_array, all_time_device2_y_array = getImageNumOverTime("end device 2", None, None, None)
    all_time_device3_x_array, all_time_device3_y_array = getImageNumOverTime("end device 3", None, None, None)

    all_time_big_Y_array_device1 = map_XYvalues_to_Larger_range(all_time_x_array, all_time_device1_x_array, all_time_device1_y_array)
    all_time_big_Y_array_device2 = map_XYvalues_to_Larger_range(all_time_x_array, all_time_device2_x_array, all_time_device2_y_array)
    all_time_big_Y_array_device3 = map_XYvalues_to_Larger_range(all_time_x_array, all_time_device3_x_array, all_time_device3_y_array)


    #Filter the number of images for past 7 days
    end_datetime = datetime.datetime.strptime(getMalaysiaTime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
    start_datetime = end_datetime - datetime.timedelta(days=7)
    this_week_x_array, this_week_y_array = getImageNumOverTime(None, None, start_datetime, end_datetime)
    this_week_device1_x_array, this_week_device1_y_array = getImageNumOverTime("end device 1", None, start_datetime, end_datetime)
    this_week_device2_x_array, this_week_device2_y_array = getImageNumOverTime("end device 2", None, start_datetime, end_datetime)
    this_week_device3_x_array, this_week_device3_y_array = getImageNumOverTime("end device 3", None, start_datetime, end_datetime)


    this_week_big_Y_array_device1 = map_XYvalues_to_Larger_range(this_week_x_array, this_week_device1_x_array, this_week_device1_y_array)
    this_week_big_Y_array_device2 = map_XYvalues_to_Larger_range(this_week_x_array, this_week_device2_x_array, this_week_device2_y_array)
    this_week_big_Y_array_device3 = map_XYvalues_to_Larger_range(this_week_x_array, this_week_device3_x_array, this_week_device3_y_array)


    return render_template("analytics.html", msg = None, active_state = "analytics", navbar_items = navbar_items, 
    all_time_x_array = all_time_x_array, all_time_y_array = all_time_y_array, all_time_big_Y_array_device1 = all_time_big_Y_array_device1,
    all_time_big_Y_array_device2 = all_time_big_Y_array_device2, all_time_big_Y_array_device3 = all_time_big_Y_array_device3,
    this_week_x_array = this_week_x_array, this_week_y_array = this_week_y_array, this_week_big_Y_array_device1 = this_week_big_Y_array_device1,
    this_week_big_Y_array_device2 = this_week_big_Y_array_device2, this_week_big_Y_array_device3 = this_week_big_Y_array_device3,
    input_filter_x_array = input_filter_x_array, input_filter_y_array = input_filter_y_array, input_filter_big_Y_array_device1 = input_filter_big_Y_array_device1,
    input_filter_big_Y_array_device2 = input_filter_big_Y_array_device2, input_filter_big_Y_array_device3 = input_filter_big_Y_array_device3,
    from_date = data.from_date_str, to_date = data.to_date_str, current_detection_type =  data.detection_type)

#------------------------------------------------------------
#-------------------------Image upload-------------------------
#------------------------------------------------------------
UPLOAD_FOLDER = 'static/image uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/data_center/upload_image")
@login_required
@require_role(role="admin", role2 ="explorer")
def upload_image():
    navbar_items = [["View", url_for('display_image')], ["Upload", url_for('upload_image')]]
    return render_template('upload_image.html', active_state = "data_center", navbar_items = navbar_items)

@app.route("/data_center/update_multiple_images", methods = ['POST'])
@login_required     
@require_role(role="admin", role2 = "explorer")
def upload_multiple_image():
    navbar_items = [["View", url_for('display_image')], ["Upload", url_for('upload_image')]]
    if 'files' not in request.files:
        flash('Upload Failed. No file part', 'error_msg_multipleimgupload')
        return redirect('/data_center/upload_image')

    for file in request.files.getlist('files'):
        if file.filename == '':
            flash('Upload Failed. No image selected for uploading', 'error_msg_multipleimgupload')
            return redirect(request.url)
        if file and allowed_file(file.filename): 
            img_source = request.form['img_source']
            filename = secure_filename(file.filename)
            str = img_source + "/" + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], str)
            absolute_file_path = os.path.join(BASE_DIR, file_path)
            # if the directory already contain file with same name, then rename before 
            # saving the file to prevent overwrite
            file_path, absolute_file_path = checkFilePath(file_path, absolute_file_path, img_source, filename, BASE_DIR, app)

            # checks whether file path is redundant
            redundant_file_bool = Images.query.filter_by(path=file_path).first()

            if redundant_file_bool:
                flash('Upload Failed. Image with same filename exist in database directory. Please rename.', 'error_msg_singleimgupload')
                return redirect(request.url)
            else:
                flash('Image successfully uploaded to database.', 'success_msg_multipleimgupload')
                #=============== Get other user input =============== 
                # timestamp_str   = request.args.get('timestamp_input',time.strftime("%Y-%m-%d %H:%M")) #Get the from date value from the URL
                timestamp_str   = request.form['timestamp_input']

                # Create datetime object so that we can convert to UTC from the browser's local time
                timestamp_str = datetime.datetime.strptime(timestamp_str,'%Y-%m-%d %H:%M')

                img_time = timestamp_str.strftime("%Y-%m-%d %H:%M:%S")

                img_tag_input = request.form['img_tag_input']
                
                img_latitude = request.form['img_latitude']
                img_longitude = request.form['img_longitude']
                upload_date = getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p")
                #save the file to server directory
                file.save(absolute_file_path)
                #saving file requires different format, therefore denotes as absolute_file_path

                new_image = Images(timestamp = img_time, path = file_path, source= img_source, uploader = current_user.username, tag = img_tag_input, latitude = img_latitude, longitude = img_longitude, upload_date = upload_date)
                db.session.add(new_image)
                db.session.commit()

                # server activity
                logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Image upload", "User - " + current_user.username + " uploaded an image", db)

        else:
            flash('Upload Failed. Allowed image types are - png, jpg, jpeg, gif', 'error_msg_multipleimgupload')
            return redirect('/data_center/upload_image')
    data.input_date_str = request.args.get('timestamp_input',time.strftime("%Y-%m-%d %H:%M"))
    return render_template('upload_image.html', file_path=file_path,  active_state = "data_center", input_date_str = data.input_date_str, navbar_items = navbar_items)
        


@app.route('/delete_img/<img_id>')
@login_required
@require_role(role="admin", role2 = "explorer")
def delete_img(img_id):
    result = Images.query.filter_by(id=img_id).first()

    for filepath in [result.path, result.path2, result.json_path]:
        print(filepath)
        if filepath:
            if os.path.exists(filepath):
                os.remove(filepath)
                print("file deleted")
        else:
            print("The file does not exist")

    logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Image deletion", "User - " + current_user.username + " deleted an image with id " + img_id + ".", db)

    # after deleting image, do not request new user input so the previous inputs remain
    # more user-friendly
    data.dontRequest = 1
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("DELETE FROM Images WHERE id= \'" + str(img_id) +"\';")
    conn.commit()
    conn.close()
    return redirect(url_for('display_image'))




@app.route('/edit_img/<img_id>')
@login_required
@require_role(role="admin", role2 = "explorer")
def edit_img(img_id):
    result = Images.query.filter_by(id=img_id).first()
    if not result:
        abort(404, message="Image record doesn't exist, cannot update")

    timestamp_str = request.args.get('timestamp_input')

    # Create datetime object so that we can convert to UTC from the browser's local time

    try:
        timestamp_str = datetime.datetime.strptime(timestamp_str,'%Y-%m-%d %H:%M')
    except:
        timestamp_str = datetime.datetime.strptime(timestamp_str,'%Y-%m-%d %H:%M:%S')

    img_time = timestamp_str.strftime("%Y-%m-%d %H:%M:%S")

    result.timestamp  =  img_time

    # changing file path of the image when user change the image source
    img_source = request.args.get('modal-img_source')
    result.source  = img_source
    path = request.args.get('img_path_input')
    original_absolute_file_path = os.path.join(BASE_DIR, path)
    filename = os.path.basename(path)
    
    if "edited" in filename:
        str = img_source + "/" + filename
    else:
        str = img_source + "/edited_" + filename

    new_relative_file_path = os.path.join(app.config['UPLOAD_FOLDER'], str)
    new_absolute_file_path = os.path.join(BASE_DIR, new_relative_file_path)

    new_relative_file_path, new_absolute_file_path = checkFilePath(new_relative_file_path, new_absolute_file_path, img_source, filename, BASE_DIR, app)

    result.path  = new_relative_file_path
    shutil.move(original_absolute_file_path, new_absolute_file_path)
    
    result.tag  = request.args.get('img_tag_input')
    result.latitude  = request.args.get('img_latitude')
    result.longitude  = request.args.get('img_longitude')
    db.session.commit()

    logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Image edition", "User - " + current_user.username + " editted an image with id " + img_id + ".", db)
    # after editing image, do not request new user input so the previous inputs remain
    # more user-friendly
    data.dontRequest = 1

    return redirect(url_for('display_image'))

#------------------------------------------------------------
#------------------------------------------------------------
#------------------------------------------------------------

@app.route("/debug")
@login_required
@require_role(role="admin", role2 = "admin")
def debug():
    activity_description = []
    activity_date = []
    activity_type = []
    result = Server_debugger.query.all()
    for row in result:
        activity_description.append(row.description)
        activity_date.append(row.timestamp)
        activity_type.append(row.type)
    db.session.commit()
    activity_description.reverse()
    activity_date.reverse()
    activity_type.reverse()

    return render_template("debug.html", active_state = "debug", activity_description = activity_description, activity_date = activity_date, activity_type = activity_type)

##################################################################
###################### Load testing URLs #####################
##################################################################


@app.route("/debugger_xlxs")
def debugger_xlxs():
    workbook = Workbook('debugger_log.xlsx')
    worksheet = workbook.add_worksheet()
    conn=sqlite3.connect('database.sqlite')
    c=conn.cursor()
    c.execute("select * from Server_debugger")
    mysel=c.execute("select * from Server_debugger ")
    for i, row in enumerate(mysel):
        for j, value in enumerate(row):
            worksheet.write(i, j, value)
    workbook.close()
    return redirect("/debug")


@app.route("/server_activity_xlxs")
def server_activity_xlxs():
    workbook = Workbook('server_activities_log.xlsx')
    worksheet = workbook.add_worksheet()
    conn=sqlite3.connect('database.sqlite')
    c=conn.cursor()
    c.execute("select * from Server_activity")
    mysel=c.execute("select * from Server_activity")
    for i, row in enumerate(mysel):
        for j, value in enumerate(row):
            worksheet.write(i, j, value)
    workbook.close()
    return redirect("/admin/home")



##################################################################

@app.route("/about_us")
@login_required
def about_us():
    images = []
    # images.append(check_and_create_img_thumbnail(BASE_DIR, 'static/img/motivation.png', 5000, data)[1])
    # images.append(check_and_create_img_thumbnail(BASE_DIR, 'static/img/introduction.png', 5000, data)[1])
    # images.append(check_and_create_img_thumbnail(BASE_DIR, 'static/img/features.png', 5000, data)[1])
    # images.append(check_and_create_img_thumbnail(BASE_DIR, 'static/img/system_overview.png', 5000, data)[1])
    # images.append(check_and_create_img_thumbnail(BASE_DIR, 'static/img/system_flowchart.png', 5000, data)[1])
    # images.append(check_and_create_img_thumbnail(BASE_DIR, 'static/img/results_and_discussion.png', 5000, data)[1])
    # images.append(check_and_create_img_thumbnail(BASE_DIR, 'static/img/future_development.png', 5000, data)[1])
    # images.append(check_and_create_img_thumbnail(BASE_DIR, 'static/img/vision.png', 5000, data)[1])
    return render_template("about_us.html", active_state = "about_us", images = images)



# @app.route("/start_thread")
# @login_required
# @require_role(role="admin", role2="admin")
# def start_thread():
#     thread1 = threading.Thread(target = update_server_thread)
#     thread1.daemon = True
#     thread1.start()


#     return render_template('thread.html')

# @app.route("/end_devices")
# @login_required
# @require_role(role="admin", role2="explorer")
# def end_devices():
#     end_device_name1 = "?"
#     end_device_name2 = "?"
#     end_device_name3 = "?"
#     conn = sqlite3.connect(db_path)
#     cursor = conn.execute("SELECT name FROM end_device WHERE id = 1")
#     for row in cursor:
#         end_device_name1 = row[0]
#     cursor = conn.execute("SELECT name FROM end_device WHERE id = 2")
#     for row in cursor:
#         end_device_name2 = row[0]
#     cursor = conn.execute("SELECT name FROM end_device WHERE id = 3")
#     for row in cursor:
#         end_device_name3 = row[0]

#     return render_template("end_devices.html", active_state = "end_devices", end_device_name1 = end_device_name1, end_device_name2 = end_device_name2, end_device_name3 = end_device_name3)
    



@app.route("/display_image")
@login_required
@require_role(role="admin", role2 = "explorer")
def display_image():
    navbar_items = [ ["Upload new image", url_for('upload_image')]]
    range_h = 'none'
    if not data.dontRequest == 1:
        timezone, start_datetime, end_datetime, data.station, data.detection_type, range_h = get_records()
        start = datetime.datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
        end = datetime.datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")
    else:
        # timezone 		= request.args.get('timezone','Etc/UTC')
        data.dontRequest = 0
        start = datetime.datetime.strptime(data.from_date_str, "%Y-%m-%d %H:%M:%S")
        end = datetime.datetime.strptime(data.to_date_str, "%Y-%m-%d %H:%M:%S")

    try:
        range_h = int(range_h)
    except:
        print("range_h cannot be converted to an integer")
    


    current_time = datetime.datetime.strptime(getMalaysiaTime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
    if isinstance(range_h, int):
        end = current_time
        start = current_time - datetime.timedelta(hours=range_h)


    else:
        if end > current_time:
            end = current_time
        #if start time is later than end time, then force start time to be = end
        if start > end:
            start = end

    # append the start and end time to memory (class variable that is accesible by all)
    data.to_date_str = end.strftime("%Y-%m-%d %H:%M:%S")
    data.from_date_str = start.strftime("%Y-%m-%d %H:%M:%S")

    # Filter images from database
    image_id = []
    image_paths = []
    image_paths_high_res = []
    image_paths2 = []
    image_timestamps = []
    image_longitude = []
    image_latitude = []
    image_uploader = []
    image_source = []
    image_tag = []
    image_upload_date = []

    if (data.station == "any"):
        cursor = Images.query.all()
        
    else:
        cursor = Images.query.filter_by(source=data.station)
    
    for image in cursor:
        image_criteria_pass = 0 #boolean variable to filter image
        date_time = image.timestamp
        try: 
            date_time_obj = datetime.datetime.strptime(date_time, "%Y-%m-%d %H-%M-%S")
        except:
            date_time_obj = datetime.datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")

        if start <= date_time_obj <= end:
          if data.detection_type == "any":
              image_criteria_pass = 1
          
          elif data.detection_type == "human":
              if "person" in image.tag or "human" in image.tag:
                  image_criteria_pass = 1
          else:
              if data.detection_type in image.tag:
                  image_criteria_pass = 1

        if image_criteria_pass == 1:
            image_id.append(image.id)
            datetime_str_formatted = datetime.datetime.strftime(date_time_obj, '%Y-%m-%d %H:%M:%S')
            image_timestamps.append(datetime_str_formatted)
            image_paths.append(check_and_create_img_thumbnail(BASE_DIR, image.path, 300, data)[1])
            # image_paths.append(image.path)
            image_paths_high_res.append(image.path)

            if image.path2:
            #this if loop is to prevent when file path is none type
                image_paths2.append(check_and_create_img_thumbnail(BASE_DIR, image.path2, 300, data)[1])
            else:
                image_paths2.append(image.path2)

            # image_paths2.append(image.path2)

            image_source.append(image.source)
            image_uploader.append(image.uploader)
            image_tag.append(image.tag)
            image_latitude.append(image.latitude)
            image_longitude.append(image.longitude)
            image_upload_date.append(image.upload_date)  
            

    #reverse the array so that image file with latest timestamp is displayed at top, 
    # but this method cannnot completely sort all the image, as it depend upon the sequence of being added to database
    # therefore, sorting should be carried out base on time represented by each image in database, not depending
    #on the sequence of them being read
    image_id.reverse()
    image_timestamps.reverse()
    image_paths.reverse()
    image_paths_high_res.reverse()
    image_paths2.reverse()
    image_source.reverse()
    image_uploader.reverse()
    image_tag.reverse()
    image_latitude.reverse()
    image_longitude.reverse()
    image_upload_date.reverse()
    
    return render_template( "display_image.html", 
                            from_date = data.from_date_str,
                            to_date = data.to_date_str,
                            query_string = request.query_string,
                            active_state = "data_center",
                            image_paths = image_paths, image_paths2 = image_paths2, image_paths_high_res = image_paths_high_res,
                            image_timestamps = image_timestamps,
                            image_longitude = image_longitude,
                            image_latitude = image_latitude,
                            image_uploader = image_uploader,
                            image_source = image_source,
                            image_id = image_id,
                            image_tag = image_tag, image_upload_date = image_upload_date,
                            current_source = data.station, current_detection_type = data.detection_type, navbar_items = navbar_items)

def get_records():
    """getting records from users at website's form"""
    from_date_str   = request.args.get('from', getMalaysiaTime(datetime.datetime.now(), "%Y-%m-%d %H:%M")) #Get the from date value from the URL
    to_date_str     = request.args.get('to', getMalaysiaTime(datetime.datetime.now(), "%Y-%m-%d %H:%M"))   #Get the to date value from the URL

    # use try except to convert datetime string to datetime object
    from_date_obj = getDatetimeObject(from_date_str, ['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'])
    to_date_obj = getDatetimeObject(to_date_str, ['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'])


    # get the desired format from datetime object
    from_date_str = datetime.datetime.strftime(from_date_obj, "%Y-%m-%d %H:%M:%S")
    to_date_str = datetime.datetime.strftime(to_date_obj, "%Y-%m-%d %H:%M:%S")

    timezone 		= request.args.get('timezone','Etc/UTC')
    img_source       = request.args.get('station','end device 1')                           #Get img_source, or fall back to end device 1
    detection_type       = request.args.get('detection_type','any')

    range_h       = request.args.get('range_h','none') 

    print ("Received from browser: %s, %s, %s" % (from_date_str, to_date_str, timezone))



    print ('2. From: %s, to: %s, timezone: %s' % (from_date_str,to_date_str,timezone))

    return [timezone, from_date_str, to_date_str, img_source, detection_type, range_h]


def validate_date(d):
    try:
        datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
        return True
    except ValueError:
        return False

def runApp():
    app.run(debug=True, use_reloader=False)
    # app.run(debug=True)

if __name__ == "__main__":
    t1 = threading.Thread(target=runApp, daemon=True).start()
    while True:
        time.sleep(1)

        
    # thread3 = threading.Thread(target=lambda: app.run(debug=True, use_reloader=False)).start()
    # app.run(debug=True, use_reloader=False)
    # app.run(debug=True)
    # app.run(debug=True, host='0.0.0.0', port=8080) #using thisline causing error to static path
    # Start new Threads
else:
    pass
    # thread1 = threading.Thread(target = update_server_thread)
    # thread1.daemon = True
    # thread1.start()






