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
# Forms initialization
#=============================================================================================
class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Username"})
    
    password = PasswordField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Password"})
   
    # access_level = StringField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Access code"})

    access_level = SelectField(u'account type', choices=[('admin', 'Admin'), ('explorer', 'Explorer'), ('guest', 'Guest')])
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
#-------------------------User permission Config-------------------------
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
#-------------------------Flask Admin -------------------------
#------------------------------------------------------------
#Following class is user defined ModelView inherited from default 
class MyModelView(ModelView):
    #defines the condition for /admin/user to be accessible
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')
    #defines what to do if inaccesible
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

#Following class is user defined AdminIndexView inherited from default 
class MyAdminIndexView(AdminIndexView):
    #defines the condition for URL '/admin' to be accessible
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')
    #defines what to do if inaccesible
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('dashboard'))

#create admin object - template_mode defines which template we use from the lib for frontend
admin = Admin(app, index_view = MyAdminIndexView(), template_mode = 'bootstrap4')
#add ModelView class to admin
admin.add_view(MyModelView(User, db.session))


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

device_stat_update_args = reqparse.RequestParser()
device_stat_update_args.add_argument("name", type=str, help="Device name is required", required=True)
device_stat_update_args.add_argument("last_seen", type=str, help="Device last_seen is required", required=True)
device_stat_update_args.add_argument("message", type=str, help="Device message is required", required=True)
device_stat_update_args.add_argument("status", type=str, help="Device status is required", required=True)
device_stat_update_args.add_argument("battery_voltage", type=str, help="Device battery voltage?", required=True)
device_stat_update_args.add_argument("battery_current", type=str, help="Device battery current?",required=True)


resource_fields = {
	'id': fields.Integer,
	'name': fields.String,
	'last_seen': fields.String,
	'message': fields.String,
    'status': fields.String,
    'battery_voltage': fields.String,
    'battery_current': fields.String
}

#marshal_with to serialize object
class Device_Stat_pipeline(Resource):
	@marshal_with(resource_fields)
	def get(self, device_id):
		result = end_device.query.filter_by(id=device_id).first()
		if not result:
			abort(404, message="Could not find device record in database")
		return result

	@marshal_with(resource_fields)
	def put(self, device_id):
		args = device_stat_put_args.parse_args()
		result = end_device.query.filter_by(id=device_id).first()
		if result:
			abort(409, message="Device id taken...")

		device_record = end_device(id=device_id, name=args['name'], last_seen=args['last_seen'], status=args['status'])
		db.session.add(device_record)
		db.session.commit()
		return device_record, 201 #this number is just a number in http protocol, can change to other num

	@marshal_with(resource_fields)
	def patch(self, device_id):
		args = device_stat_update_args.parse_args()
		result = end_device.query.filter_by(id=device_id).first()
		if not result:
			abort(404, message="Device record doesn't exist, cannot update")

		if args['name']:
			result.name = args['name']

		if args['last_seen']:
			result.last_seen = args['last_seen']
			
		if args['message']:
			result.message = args['message']

		if args['battery_voltage']:
			result.battery_voltage = args['battery_voltage']

		if args['battery_current']:
			result.battery_current = args['battery_current']
        
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





@app.route("/roboflow")
@login_required
def roboflow():

    update_server_directory_images()
        
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
        datetime_object = datetime.datetime.strptime(device.last_seen, '%Y-%m-%d %H-%M-%S')
        #hardcode the timezone as Malaysia timezone
        timezone = pytz.timezone("Asia/Kuala_Lumpur")
        #add timezone attribute to datetime object
        datetime_object_timezone = timezone.localize(datetime_object, is_dst=None)
        datetime_str_formatted = datetime.datetime.strftime(datetime_object_timezone, '%I:%M:%S %p, %d/%m/%Y')

        # append all data to arrays to be displayed on web page
        devices_name.append(device.name)
        devices_last_seen.append(datetime_str_formatted)
        devices_message.append(device.message)
        devices_status.append(device.status)
        current_battery_current = float(device.battery_current)
        devices_battery_current.append(current_battery_current)
        # Battery stats
        current_battery_voltage = float(device.battery_voltage)
        devices_battery_voltage.append(current_battery_voltage)
        full_battery_voltage = 13
        min_battery_voltage  = 11.5
        battery_operating_range = full_battery_voltage - min_battery_voltage
        battery_level = ((float(device.battery_voltage) - min_battery_voltage)/battery_operating_range)*100
        battery_level = int((battery_level * 100) + 0.5) / 100.0 # Adding 0.5 rounds it up
        devices_battery_level.append(battery_level)


        current_power_level = current_battery_voltage*current_battery_current*10**-3 #10^-3 because current is in mA
        current_power_level = int((current_power_level * 10000) + 0.5) / 10000.0 # Adding 0.5 rounds it up
        devices_power_level.append(current_power_level)
        

        if current_battery_voltage > 13:
            stat = "Charging"
        elif current_battery_voltage == 13:
            stat = "Fully charged"
        elif current_battery_voltage > 10 and current_battery_voltage < 13:
            stat = "Operating"
        elif current_battery_voltage <= 10:
            stat = "Running out"
        else:
            stat = "Unknown"
            
        devices_battery_status.append(stat)


        db.session.commit()

    return render_template('index.html', active_state = "dashboard", image1 = image1, image2 = image2, image3 = image3, devices_name = devices_name, devices_last_seen = devices_last_seen, devices_message = devices_message, devices_status = devices_status, devices_battery_current = devices_battery_current, devices_battery_voltage = devices_battery_voltage, devices_battery_level = devices_battery_level, devices_battery_status = devices_battery_status, devices_power_level = devices_power_level, navbar_items = navbar_items)

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


        new_user = User(username = form.username.data, password=hashed_password, access_level = form.access_level.data, date_created = date_created)
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
        user_roles.append(row.access_level)
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

    # Hint: getImageNumOverTime(img_source, detection_type, start_datetime, end_datetime)
    #Filter the number of images for all time
    all_time_x_array, all_time_y_array = getImageNumOverTime(None, None, None, None)
    all_time_device1_x_array, all_time_device1_y_array = getImageNumOverTime("end device 1", None, None, None)
    all_time_device2_x_array, all_time_device2_y_array = getImageNumOverTime("end device 2", None, None, None)
    all_time_device3_x_array, all_time_device3_y_array = getImageNumOverTime("end device 3", None, None, None)

    all_time_big_Y_array_device1 = map_XYvalues_to_Larger_range(all_time_x_array, all_time_device1_x_array, all_time_device1_y_array)
    all_time_big_Y_array_device2 = map_XYvalues_to_Larger_range(all_time_x_array, all_time_device2_x_array, all_time_device2_y_array)
    all_time_big_Y_array_device3 = map_XYvalues_to_Larger_range(all_time_x_array, all_time_device3_x_array, all_time_device3_y_array)


    #Filter the number of images for past 7 days
    end_datetime = datetime.datetime.now()
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
    this_week_big_Y_array_device2 = this_week_big_Y_array_device2, this_week_big_Y_array_device3 = this_week_big_Y_array_device3 )

#------------------------------------------------------------
#-------------------------Image upload-------------------------
#------------------------------------------------------------
UPLOAD_FOLDER = 'static/image uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/data_center/update_status")
@login_required
@require_role(role="admin", role2 ="explorer")
def update_status():
    navbar_items = [["View", url_for('display_image')], ["Upload", url_for('update_status')]]
    return render_template('update_status.html', active_state = "data_center", navbar_items = navbar_items)

@app.route("/data_center/update_multiple_images", methods = ['POST'])
@login_required     
@require_role(role="admin", role2 = "explorer")
def upload_multiple_image():
    navbar_items = [["View", url_for('display_image')], ["Upload", url_for('update_status')]]
    if 'files' not in request.files:
        flash('Upload Failed. No file part', 'error_msg_multipleimgupload')
        return redirect('/data_center/update_status')

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
            return redirect('/data_center/update_status')
    data.input_date_str = request.args.get('timestamp_input',time.strftime("%Y-%m-%d %H:%M"))
    return render_template('update_status.html', file_path=file_path,  active_state = "data_center", input_date_str = data.input_date_str, navbar_items = navbar_items)
        
   

# @app.route("/data_center/update_status", methods = ['POST'])
# @login_required
# @require_role(role="admin", role2 = "explorer")
# def upload_image():
#     navbar_items = [["View", url_for('display_image')], ["Upload", url_for('update_status')]]
#     if 'file' not in request.files:
#         flash('Upload Failed. No file part', 'error_msg_singleimgupload')
#         return redirect(request.url)
#     file = request.files['file']
#     if file.filename == '':
#         flash('Upload Failed. No image selected for uploading', 'error_msg_singleimgupload')
#         return redirect(request.url)

#     if file and allowed_file(file.filename): 
#         img_source = request.form['img_source']
#         filename = secure_filename(file.filename)
#         timestamp = datetime.datetime.now().strftime("uploaded-on_%y-%m-%d_%H-%M-%S_")
#         str = img_source + "/" + timestamp + filename
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], str)
#         absolute_file_path = os.path.join(BASE_DIR, file_path)

#         file_path, absolute_file_path = checkFilePath(file_path, absolute_file_path, img_source, filename, BASE_DIR, app)

#         # checks whether file path is redundant
#         redundant_file_bool = Images.query.filter_by(path=file_path).first()

#         if redundant_file_bool:
#             flash('Upload Failed. Image with same filename exist in database directory. Please rename.', 'error_msg_singleimgupload')
#             return redirect(request.url)
#         else:


     
#             flash('Image successfully uploaded to database.', 'success_msg_singleimgupload')
#             #=============== Get other user input =============== 
#             timestamp_str   = request.form['timestamp_input']
#             # Create datetime object so that we can convert to UTC from the browser's local time
#             timestamp_str = datetime.datetime.strptime(timestamp_str,'%Y-%m-%d %H:%M')
#             img_time = timestamp_str.strftime("%Y-%m-%d %H:%M:%S")

#             img_tag_input = request.form['img_tag_input']
            
#             img_latitude = request.form['img_latitude']
#             img_longitude = request.form['img_longitude']
#             upload_date = getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p")

#             #save the file to server directory
#             file.save(absolute_file_path)
            
#             new_image = Images(timestamp = img_time, path = file_path, source= img_source, uploader = current_user.username, tag = img_tag_input, latitude = img_latitude, longitude = img_longitude, upload_date = upload_date)
#             db.session.add(new_image)
#             db.session.commit()

#             # server activity
#             logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Image upload", "User - " + current_user.username + " uploaded an image", db)

#             timestamp_str = request.args.get('timestamp_input',time.strftime("%Y-%m-%d %H:%M"))
#             data.input_date_str = datetime.datetime.strptime(timestamp_str,'%Y-%m-%d %H:%M')
#             data.input_date_str = data.input_date_str.strftime("%Y-%m-%d %H:%M:%S")
            
#             return render_template('update_status.html', file_path=file_path,  active_state = "data_center", input_date_str = data.input_date_str, navbar_items = navbar_items)

#     else:
#         flash('Upload Failed. Allowed image types are - png, jpg, jpeg, gif', 'error_msg_singleimgupload')
#         return redirect(request.url)
        
# @app.route('/display/<file_path>')
# def display_img(filename):
#     #print('display_image filename: ' + filename)
#     return redirect(url_for('static', filename='image uploads/uploaded/' + filename), code=301)

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

    img_time = timestamp_str.strftime("%Y-%m-%d %H-%M-%S")

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

# @app.route("/test")
# def test():
#     return render_template("test.html")


@app.route("/about_us")
@login_required
def about_us():
    images = []
    images.append(check_and_create_img_thumbnail(BASE_DIR, 'static/img/bigpicture.png', 1000, data)[1])
    return render_template("about_us.html", active_state = "about_us", images = images)

@app.route("/start_thread")
@login_required
@require_role(role="admin", role2="admin")
def start_thread():
    thread1 = threading.Thread(target = update_server_thread)
    thread1.daemon = True
    thread1.start()
    
    # thread2 = threading.Thread(target = update_end_device_database_thread)
    # thread2.daemon = True
    # thread2.start()

    return render_template('thread.html')

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
    navbar_items = [["Update database", url_for('roboflow')], ["Upload", url_for('update_status')]]
    if not data.dontRequest == 1:
        timezone, start_datetime, end_datetime, data.station, data.detection_type = get_records()
        start = datetime.datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
        end = datetime.datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")
    else:
        timezone 		= request.args.get('timezone','Etc/UTC')
        data.dontRequest = 0
        start = datetime.datetime.strptime(data.from_date_str, "%Y-%m-%d %H:%M:%S")
        end = datetime.datetime.strptime(data.to_date_str, "%Y-%m-%d %H:%M:%S")


    current_time = datetime.datetime.strptime(getMalaysiaTime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
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
                            timezone = timezone,
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
    from_date_str   = request.args.get('from',time.strftime("%Y-%m-%d %H:%M")) #Get the from date value from the URL
    to_date_str     = request.args.get('to',time.strftime("%Y-%m-%d %H:%M"))   #Get the to date value from the URL

    # use try except to convert datetime string to datetime object
    from_date_obj = getDatetimeObject(from_date_str, ['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'])
    to_date_obj = getDatetimeObject(to_date_str, ['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'])


    # get the desired format from datetime object
    from_date_str = datetime.datetime.strftime(from_date_obj, "%Y-%m-%d %H:%M:%S")
    to_date_str = datetime.datetime.strftime(to_date_obj, "%Y-%m-%d %H:%M:%S")

    timezone 		= request.args.get('timezone','Etc/UTC')
    img_source       = request.args.get('station','end device 1')                           #Get img_source, or fall back to end device 1
    detection_type       = request.args.get('detection_type','any') 

    print ("Received from browser: %s, %s, %s" % (from_date_str, to_date_str, timezone))



    print ('2. From: %s, to: %s, timezone: %s' % (from_date_str,to_date_str,timezone))

    return [timezone, from_date_str, to_date_str, img_source, detection_type]


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





