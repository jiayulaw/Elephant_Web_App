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
from DB_class import Images, end_device, User, Detection, Server_activity, app, api, db, db_path, BASE_DIR

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
#-------------------------Initialization of variables-------------------------
#------------------------------------------------------------

class DataStorage():
    dontRequest = None
    station = "end device 1"
    from_date_str = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M")
    to_date_str = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M")
    detection_type = "any"

    input_date_str = None

data = DataStorage()

#------------------------------------------------------------
#-------------------------User Auth-------------------------
#------------------------------------------------------------
basedir = os.path.abspath(os.path.dirname(__file__))
print(basedir)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
@login_manager.user_loader

def load_user(user_id):
    return User.query.get(int(user_id))


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
    username = StringField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Username"})
    
    password = PasswordField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Current password"})

    new_password = PasswordField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "New password"})
    new_password2 = PasswordField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Confirm new password"})
   
    submit = SubmitField("Change password")
    #Checks whether the username is redundant
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username = username.data).first()

        if not existing_user_username:
            raise ValidationError("The username does not exist.")



class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Username"})
    
    password = PasswordField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Password"})
    
    submit = SubmitField("Login")

#------------------------------------------------------------
#-------------------------User Admin-------------------------
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
    #defines the condition for /admin to be accessible
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')


#create admin object - template_mode defines which template we use from the lib for frontend
admin = Admin(app, index_view = MyAdminIndexView(), template_mode = 'bootstrap4')
#add ModelView class to admin
admin.add_view(MyModelView(User, db.session))


#------------------------------------------------------------
#------------------------------------------------------------
#------------------------------------------------------------

#------------------------------------------------------------
#-------------------------REST API-------------------------
#------------------------------------------------------------
device_stat_put_args = reqparse.RequestParser()
#help parameter is similar to error message we send back to sender when there is no valid input
#required parameter means the field is not optional
device_stat_put_args.add_argument("name", type=str, help="Device name is required", required=True)
device_stat_put_args.add_argument("last_seen", type=str, help="Device last_seen is required", required=True)
device_stat_put_args.add_argument("message", type=str, help="Device message is required", required=True)
device_stat_put_args.add_argument("status", type=str, help="Device status is required", required=True)

device_stat_update_args = reqparse.RequestParser()
device_stat_update_args.add_argument("name", type=str, help="Device name is required", required=True)
device_stat_update_args.add_argument("last_seen", type=str, help="Device last_seen is required", required=True)
device_stat_update_args.add_argument("message", type=str, help="Device message is required", required=True)
device_stat_update_args.add_argument("status", type=str, help="Device status is required", required=True)


resource_fields = {
	'id': fields.Integer,
	'name': fields.String,
	'last_seen': fields.String,
	'message': fields.String,
    'status': fields.String
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
        
		if args['status']:
			if result.status != args['status']:
				logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Status change", "Device - " + args['name'] + " changed status from " + result.status + " to " + args['status'], db)      

			result.status = args['status']
	

		db.session.commit()
		return result

	# def delete(self, device_id):
	# 	# need to abort if the database doesnt exist, else might cause error
    #     # #abort_if_video_id_doesnt_exist(video_id)
	# 	del end_device[device_id]
	# 	return '', 204


api.add_resource(Device_Stat_pipeline, "/device_stat/<int:device_id>")

#------------------------------------------------------------
#------------------------------------------------------------
#------------------------------------------------------------

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
        datetime_object = datetime.datetime.strptime(device.last_seen, '%d/%m/%Y, %H:%M:%S')
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

        db.session.commit()

    return render_template('index.html', active_state = "dashboard", image1 = image1, image2 = image2, image3 = image3, devices_name = devices_name, devices_last_seen = devices_last_seen, devices_message = devices_message, devices_status = devices_status, navbar_items = navbar_items)

@app.route('/update_server', methods=['POST'])
def webhook():
    repo = git.Repo('./Elephant_Project_Web_Application')
    origin = repo.remotes.origin

    repo.create_head('main', origin.refs.main).set_tracking_branch(origin.refs.main).checkout()
    origin.pull()
    return 'Updated PythonAnywhere successfully', 200

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
                login_user(user)
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

        hashed_password = bcrypt.generate_password_hash(form.password.data)
        result = User.query.filter_by(username = form.username.data).first()
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


    # #convert list items to datetime object
    # big_array_x_datetime_obj = [datetime.datetime.strptime(date, "%Y-%m-%d %H-%M") for date in big_array_x]
    # #sort the list based on datetime
    # sorted_big_array_x_datetime_obj = sorted(big_array_x_datetime_obj)
    # #convert back to string
    # sorted_big_array_x = [date.strftime("%Y-%m-%d %H-%M") for date in sorted_big_array_x_datetime_obj]
    # #remove redundant elements in list by converting to dictionary then convert back
    # sorted_big_array_x = list(dict.fromkeys(sorted_big_array_x))

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
                if not validate_date(timestamp_str):			# Validate date format
                    timestamp_str 	= time.strftime("%Y-%m-%d %H:%M")
                # Create datetime object so that we can convert to UTC from the browser's local time
                timestamp_str = datetime.datetime.strptime(timestamp_str,'%Y-%m-%d %H:%M')

                img_time = timestamp_str.strftime("%Y-%m-%d %H-%M")

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

                data.input_date_str = request.args.get('timestamp_input',time.strftime("%Y-%m-%d %H:%M"))
                return render_template('update_status.html', file_path=file_path,  active_state = "data_center", input_date_str = data.input_date_str, navbar_items = navbar_items)

        else:
            flash('Upload Failed. Allowed image types are - png, jpg, jpeg, gif', 'error_msg_multipleimgupload')
            return redirect('/data_center/update_status')
        
   

@app.route("/data_center/update_status", methods = ['POST'])
@login_required
@require_role(role="admin", role2 = "explorer")
def upload_image():
    navbar_items = [["View", url_for('display_image')], ["Upload", url_for('update_status')]]
    if 'file' not in request.files:
        flash('Upload Failed. No file part', 'error_msg_singleimgupload')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('Upload Failed. No image selected for uploading', 'error_msg_singleimgupload')
        return redirect(request.url)

    if file and allowed_file(file.filename): 
        img_source = request.form['img_source']
        filename = secure_filename(file.filename)
        timestamp = datetime.datetime.now().strftime("uploaded-on_%y-%m-%d_%H-%M-%S_")
        str = img_source + "/" + timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], str)
        absolute_file_path = os.path.join(BASE_DIR, file_path)

        file_path, absolute_file_path = checkFilePath(file_path, absolute_file_path, img_source, filename, BASE_DIR, app)

        # checks whether file path is redundant
        redundant_file_bool = Images.query.filter_by(path=file_path).first()

        if redundant_file_bool:
            flash('Upload Failed. Image with same filename exist in database directory. Please rename.', 'error_msg_singleimgupload')
            return redirect(request.url)
        else:


     
            flash('Image successfully uploaded to database.', 'success_msg_singleimgupload')
            #=============== Get other user input =============== 
            # timestamp_str   = request.args.get('timestamp_input',time.strftime("%Y-%m-%d %H:%M")) #Get the from date value from the URL
            timestamp_str   = request.form['timestamp_input']
            if not validate_date(timestamp_str):			# Validate date format
                timestamp_str 	= time.strftime("%Y-%m-%d %H:%M")
            # Create datetime object so that we can convert to UTC from the browser's local time
            timestamp_str = datetime.datetime.strptime(timestamp_str,'%Y-%m-%d %H:%M')
            # img_tim = datetime.datetime.strptime(from_date_str, "%Y-%m-%d %H:%M")

            img_time = timestamp_str.strftime("%Y-%m-%d %H-%M")

            img_tag_input = request.form['img_tag_input']
            
            img_latitude = request.form['img_latitude']
            img_longitude = request.form['img_longitude']
            upload_date = getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p")

            #save the file to server directory
            file.save(absolute_file_path)
            #saving file requires different format, therefore denotes as file_path2
            #print('upload_image filename: ' + filename)
        
            
            new_image = Images(timestamp = img_time, path = file_path, source= img_source, uploader = current_user.username, tag = img_tag_input, latitude = img_latitude, longitude = img_longitude, upload_date = upload_date)
            db.session.add(new_image)
            db.session.commit()

            # server activity
            logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Image upload", "User - " + current_user.username + " uploaded an image", db)

            data.input_date_str = request.args.get('timestamp_input',time.strftime("%Y-%m-%d %H:%M"))
            return render_template('update_status.html', file_path=file_path,  active_state = "data_center", input_date_str = data.input_date_str, navbar_items = navbar_items)

    else:
        flash('Upload Failed. Allowed image types are - png, jpg, jpeg, gif', 'error_msg_singleimgupload')
        return redirect(request.url)
        
# @app.route('/display/<file_path>')
# def display_img(filename):
#     #print('display_image filename: ' + filename)
#     return redirect(url_for('static', filename='image uploads/uploaded/' + filename), code=301)

@app.route('/delete_img/<img_id>')
def delete_img(img_id):
   
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT path from images WHERE id=\'" + str(img_id) + "\';")
    for row in cursor:
        filepath = row[0]
        if os.path.exists(filepath):
            os.remove(filepath)
            print("file deleted")
        else:
            print("The file does not exist")

    logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Image deletion", "User - " + current_user.username + " deleted an image with id " + img_id + ".", db)

    # after deleting image, do not request new user input so the previous inputs remain
    # more user-friendly
    data.dontRequest = 1
    cursor = conn.execute("DELETE FROM Images WHERE id= \'" + str(img_id) +"\';")
    conn.commit()
    conn.close()
    return redirect(url_for('display_image'))

@app.route('/edit_img/<img_id>')
def edit_img(img_id):
    result = Images.query.filter_by(id=img_id).first()
    if not result:
        abort(404, message="Image record doesn't exist, cannot update")

    timestamp_str = request.args.get('timestamp_input')

    if not validate_date(timestamp_str):			# Validate date format
        timestamp_str 	= time.strftime("%Y-%m-%d %H:%M")
    # Create datetime object so that we can convert to UTC from the browser's local time
    timestamp_str = datetime.datetime.strptime(timestamp_str,'%Y-%m-%d %H:%M')
    img_time = timestamp_str.strftime("%Y-%m-%d %H-%M")

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
    return render_template("debug.html", active_state = "debug")

@app.route("/test")
def test():
    return render_template("test.html")


@app.route("/about_us")
def about_us():
    return render_template("about_us.html", active_state = "about_us")

@app.route("/start_thread")
@login_required
@require_role(role="admin", role2="admin")
def start_thread():
    thread1 = myThread(1, "Thread-1", 2)
    thread1.daemon = True
    thread1.start()

@app.route("/end_devices")
@login_required
@require_role(role="admin", role2="explorer")
def end_devices():
    end_device_name1 = "?"
    end_device_name2 = "?"
    end_device_name3 = "?"
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM end_device WHERE id = 1")
    for row in cursor:
        end_device_name1 = row[0]
    cursor = conn.execute("SELECT name FROM end_device WHERE id = 2")
    for row in cursor:
        end_device_name2 = row[0]
    cursor = conn.execute("SELECT name FROM end_device WHERE id = 3")
    for row in cursor:
        end_device_name3 = row[0]

    return render_template("end_devices.html", active_state = "end_devices", end_device_name1 = end_device_name1, end_device_name2 = end_device_name2, end_device_name3 = end_device_name3)
    
@app.route("/display_image")
@login_required
@require_role(role="admin", role2 = "explorer")
def display_image():
    #this function updates server directory for new images
    # update_server_directory_images()
    navbar_items = [["View", url_for('display_image')], ["Upload", url_for('update_status')]]
    if not data.dontRequest == 1:
        timezone, start_datetime, end_datetime, data.station, data.detection_type = get_records()
    else:
        timezone 		= request.args.get('timezone','Etc/UTC')
        data.dontRequest = 0

    start = datetime.datetime.strptime(start_datetime, "%Y-%m-%d %H:%M")
    end = datetime.datetime.strptime(end_datetime, "%Y-%m-%d %H:%M")
    current_time = datetime.datetime.strptime(getMalaysiaTime(datetime.datetime.now(), "%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M")
    if end > current_time:
        end = current_time

    #if start time is later than end time, then force start time to be = end
    if start > end:
        start = end

    # append the start and end time to memory (class variable that is accesible by all)
    data.to_date_str = end.strftime("%Y-%m-%d %H:%M")
    data.from_date_str = start.strftime("%Y-%m-%d %H:%M")

    # Filter images from database
    image_id = []
    image_paths = []
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
            date_time_obj = datetime.datetime.strptime(date_time, "%Y-%m-%d %H-%M")
        except:
            date_time_obj = datetime.datetime.strptime(date_time, "%Y-%m-%d %H:%M")

        if start <= date_time_obj <= end:
          if data.detection_type == "any":
              image_criteria_pass = 1
          else:
              if data.detection_type in image.tag:
                  image_criteria_pass = 1

        if image_criteria_pass == 1:
            image_id.append(image.id)
            datetime_str_formatted = datetime.datetime.strftime(date_time_obj, '%Y-%m-%d %H:%M')
            image_timestamps.append(datetime_str_formatted)
            image_paths.append(image.path)
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
    image_source.reverse()
    image_uploader.reverse()
    image_tag.reverse()
    image_latitude.reverse()
    image_longitude.reverse()
    
    return render_template( "display_image.html", 
                            from_date = data.from_date_str,
                            to_date = data.to_date_str,
                            query_string = request.query_string,
                            timezone = timezone,
                            active_state = "data_center",
                            image_paths = image_paths,
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

    timezone 		= request.args.get('timezone','Etc/UTC')
    range_h_form	= request.args.get('range_h','');  #This will return a string, if field range_h exists in the request
    range_h_int 	= "nan"  # initialise this variable with not a number
    img_source       = request.args.get('station','end device 1')                           #Get img_source, or fall back to end device 1
    detection_type       = request.args.get('detection_type','any') 
    

    print ("REQUEST:")
    print (request.args)

    try:
        range_h_int	= int(range_h_form)
    except:
        print ("range_h_form not a number")

    print ("Received from browser: %s, %s, %s, %s" % (from_date_str, to_date_str, timezone, range_h_int))

    if not validate_date(from_date_str):			# Validate date format
        from_date_str 	= time.strftime("%Y-%m-%d %H:%M")
    if not validate_date(to_date_str):
        to_date_str 	= time.strftime("%Y-%m-%d %H:%M")		# Validate date format

    print ('2. From: %s, to: %s, timezone: %s' % (from_date_str,to_date_str,timezone))

    # Create datetime object so that we can convert to UTC from the browser's local time
    from_date_obj       = datetime.datetime.strptime(from_date_str,'%Y-%m-%d %H:%M')
    to_date_obj         = datetime.datetime.strptime(to_date_str,'%Y-%m-%d %H:%M')

    return [timezone, from_date_str, to_date_str, img_source, detection_type]


def validate_date(d):
    try:
        datetime.datetime.strptime(d, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False

def background_task():
    while True:
        print(datetime.datetime.now())
        f = open("test-thread222228-running.txt", "w") 
        
        f.write("The thread22222228 is running!!" + str(datetime.datetime.now()))
        f.close() 
        f = open("test-thread222228-running.txt", "r")
        print(f.read())

        time.sleep(1)

def update_server_thread():
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

    print ("Starting ")
    while True:
        f = open("test-thread888-running.txt", "w") 
        f.write("The thread888 is running!!")
        f.close() 
        f = open("test-thread888-running.txt", "r")
        print(f.read())

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
                    logServerActivity(getMalaysiaTime(datetime.datetime.now(), "%d/%m/%Y %I:%M:%S %p"), "Status change", "Device - " + device.name + " changed status from " + device.status + " to " + "Offline", db)
                    device.status = "Offline"
        
        db.session.commit()
        time.sleep(2)
        print ("Exiting ")

def runApp():
    app.run(debug=True, use_reloader=False)
    # app.run(debug=True)

if __name__ == "__main__":
    # Create new thread
    # thread1 = myThread(1, "Thread-1", 2)
    # thread1.daemon = True
    # thread1.start()
    
    # thread2 = threading.Thread(target = background_task)
    # thread2.daemon = True
    # thread2.start()

    t1 = threading.Thread(target=runApp, daemon=True).start()
    # t2 = threading.Thread(target = background_task, daemon=True).start()
    while True:
        time.sleep(1)
    # thread3 = threading.Thread(target=lambda: app.run(debug=True, use_reloader=False)).start()
    # app.run(debug=True, use_reloader=False)
    # app.run(debug=True)
    # app.run(debug=True, host='0.0.0.0', port=8080) #using thisline causing error to static path
    # Start new Threads
# else:
#     t2 = threading.Thread(target = background_task, daemon=True).start()


    






