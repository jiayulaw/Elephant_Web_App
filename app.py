from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy 
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField
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
import urllib.request
from werkzeug.utils import secure_filename

#Import database rows declaration, and also Flask app objects
from DB_class import Images, end_device,User, app, api, db, db_path, BASE_DIR

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
    from_date_str = None
    to_date_str = None

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
device_stat_put_args.add_argument("name", type=str, help="Name of the video is required", required=True)
device_stat_put_args.add_argument("status", type=str, help="Views of the video", required=True)
device_stat_put_args.add_argument("message", type=str, help="Likes on the video", required=True)

device_stat_update_args = reqparse.RequestParser()
device_stat_update_args.add_argument("name", type=str, help="Device name is required", required=True)
device_stat_update_args.add_argument("status", type=str, help="Views of the video", required=True)
device_stat_update_args.add_argument("message", type=str, help="Likes on the video", required=True)

resource_fields = {
	'id': fields.Integer,
	'name': fields.String,
	'status': fields.String,
	'message': fields.String
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

		device_record = end_device(id=device_id, name=args['name'], status=args['status'], message=args['message'])
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

		if args['status']:
			result.status = args['status']
			
		if args['message']:
			result.message = args['message']
	

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
    # Filter images from database
    image_id = []
    image_paths = []
    image_timestamps = []
    image_longitude = []
    image_latitude = []
    image_uploader = []
    image_source = []
    image_tag = []
    devices_name = []
    devices_status = []
    devices_message = []
    devices_timestamp_diff = []

    command = "SELECT * from images;"
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(command) 
    for image in cursor:
        image_id.append(image[0])
        image_timestamps.append(image[1])
        image_paths.append(image[2])
        image_source.append(image[3])
        image_uploader.append(image[4])
        image_tag.append(image[5])
        image_latitude.append(image[6])
        image_longitude.append(image[7])
    
    command = "SELECT * from end_device;"
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(command)

    now = datetime.datetime.now() # current date and time
    
    for device in cursor:
        

        #dealing with the timestamp formatting for display
        #try converting to 12 Hr format
        try:
            datetime_object = datetime.datetime.strptime(device[2], '%d/%m/%Y, %H:%M:%S')
            datetime_str_formatted = datetime.datetime.strftime(datetime_object, '%I:%M:%S %p, %d/%m/%Y')
            # getting the difference between 2 timestamps in seconds
            diff_in_seconds = (now - datetime_object).seconds
            # Dividing seconds by 60 we get minutes
            output = divmod(diff_in_seconds,60)
            diff_in_minutes = output[0]
        # If the timesstamp received cannot be parsed as datetime obj,
        # then just display it out
        # and then make the differrence in minutes a large number
        except:
            diff_in_minutes = 999
            datetime_str_formatted = device[2]

        # append all data to arrays to be displayed on web page
        devices_name.append(device[1])
        devices_timestamp_diff.append(diff_in_minutes)
        devices_status.append(datetime_str_formatted)
        devices_message.append(device[3])

    return render_template('index.html', active_state = "dashboard", image_latitude = image_latitude, devices_name = devices_name, devices_status = devices_status, devices_message = devices_message, devices_timestamp_diff = devices_timestamp_diff)

@app.route('/update_server', methods=['POST'])
def webhook():
    repo = git.Repo('./Elephant_Project_Web_Application')
    origin = repo.remotes.origin

    repo.create_head('main', origin.refs.main).set_tracking_branch(origin.refs.main).checkout()
    origin.pull()
    return 'Updated PythonAnywhere successfully', 200

@app.route("/login", methods = ['GET', 'POST'])
def login():
    msg = None
    form = LoginForm()
    if form.validate_on_submit():
        #Following line checks whether user is in database
        user = User.query.filter_by(username=form.username.data).first() 
        if user: #if user in database
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                user.authenticated = True
                return redirect(url_for('dashboard'))
        return render_template("login.html", form = form, msg = "Wrong username or password.")

    return render_template("login.html", form = form, msg = msg)

    
@app.route('/logout', methods = ['GET','POST'])
@login_required
def logout():
    logout_user()
    current_user.authenticated = False
    return redirect(url_for('login'))


@app.route("/admin/register", methods = ['GET', 'POST'])
@login_required
@require_role(role="admin", role2 = "admin")
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username = form.username.data, password=hashed_password, access_level = form.access_level.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration Success', 'success_msg')
        return redirect("/admin")
    return render_template("register.html", form = form, msg = None, active_state = "admin")

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
    return render_template('update_status.html', active_state = "data_center")

@app.route("/data_center/update_multiple_images", methods = ['POST'])
@login_required
@require_role(role="admin", role2 = "explorer")
def upload_multiple_image():
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
            file_path2 = os.path.join(BASE_DIR, file_path)
            # checks whether file path is redundant
            redundant_file_bool = Images.query.filter_by(path=file_path).first()

            if redundant_file_bool:
                flash('Upload Failed. Image with same filename exist in database directory. Please rename.', 'error_msg_multipleimgupload')
                return redirect('/data_center/update_status')
            else:
                flash('Image successfully uploaded to database.', 'success_msg_multipleimgupload')
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
                
                print(img_tag_input)
                print(current_user.username)
                print(img_source)
                print(img_latitude)
                print(img_longitude)

                #save the file to server directory
                file.save(file_path2)
                #saving file requires different format, therefore denotes as file_path2
                #print('upload_image filename: ' + filename)
                print("filepath: ", file_path)
                print("filepath2: ", file_path2)
                
                new_image = Images(timestamp = img_time, path = file_path, source= img_source, uploader = current_user.username, tag = img_tag_input, latitude = img_latitude, longitude = img_longitude)
                db.session.add(new_image)
                db.session.commit()
                data.input_date_str = request.args.get('timestamp_input',time.strftime("%Y-%m-%d %H:%M"))
                return render_template('update_status.html', file_path=file_path,  active_state = "data_center", input_date_str = data.input_date_str)

        else:
            flash('Upload Failed. Allowed image types are - png, jpg, jpeg, gif', 'error_msg_multipleimgupload')
            return redirect('/data_center/update_status')
        
   

@app.route("/data_center/update_status", methods = ['POST'])
@login_required
@require_role(role="admin", role2 = "explorer")
def upload_image():
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
        str = img_source + "/" + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], str)
        file_path2 = os.path.join(BASE_DIR, file_path)
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
            
            print(img_tag_input)
            print(current_user.username)
            print(img_source)
            print(img_latitude)
            print(img_longitude)

            #save the file to server directory
            file.save(file_path2)
            #saving file requires different format, therefore denotes as file_path2
            #print('upload_image filename: ' + filename)
            print("filepath: ", file_path)
            print("filepath2: ", file_path2)
            
            new_image = Images(timestamp = img_time, path = file_path, source= img_source, uploader = current_user.username, tag = img_tag_input, latitude = img_latitude, longitude = img_longitude)
            db.session.add(new_image)
            db.session.commit()
            data.input_date_str = request.args.get('timestamp_input',time.strftime("%Y-%m-%d %H:%M"))
            return render_template('update_status.html', file_path=file_path,  active_state = "data_center", input_date_str = data.input_date_str)

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

    # after deleting image, do not request new user input so the previous inputs remain
    # more user-friendly
    data.dontRequest = 1
    cursor = conn.execute("DELETE FROM Images WHERE id= \'" + str(img_id) +"\';")
    conn.commit()
    conn.close()
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
    if not data.dontRequest == 1:
        timezone, data.from_date_str, data.to_date_str, data.station = get_records()
    else:
        timezone 		= request.args.get('timezone','Etc/UTC')
        data.dontRequest = 0

    start = datetime.datetime.strptime(data.from_date_str, "%Y-%m-%d %H:%M")
    end = datetime.datetime.strptime( data.to_date_str, "%Y-%m-%d %H:%M")


    # check directory to update any new images added through SFTP or direct upload to server
    directory = rf"static/image uploads/{data.station}" 
    directory2 = os.path.join(BASE_DIR, directory)
    for filename in os.listdir(directory2):
        try:
            if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".jpeg"):
                date_time = filename.split(".")[0]
                #print(date_time)
                date_time_obj = datetime.datetime.strptime(date_time, "%Y-%m-%d %H-%M")
                path = os.path.join(directory, filename)
                path = f"static/image uploads/{data.station}/"+filename
                result = Images.query.filter_by(path=path).first()
                if result:
                    print("the file with same name already saved")
                else:
                    new_image = Images(timestamp = date_time, path = path, source=data.station, tag = "new image", latitude ="", longitude = "")
                    db.session.add(new_image)
                    db.session.commit()
            else:
                continue
        except:
            print("Filename is not formatted correctly, but it is ok, just ignore")

    # Filter images from database
    image_id = []
    image_paths = []
    image_timestamps = []
    image_longitude = []
    image_latitude = []
    image_uploader = []
    image_source = []
    image_tag = []
    command = "SELECT * from images WHERE source = \'" + str(data.station) + "\';"

    conn = sqlite3.connect(db_path)
    cursor = conn.execute(command) 
    for image in cursor:
      date_time = image[1] 
      date_time_obj = datetime.datetime.strptime(date_time, "%Y-%m-%d %H-%M")
      if start <= date_time_obj <= end:
          image_id.append(image[0])
          image_timestamps.append(image[1])
          image_paths.append(image[2])
          image_source.append(image[3])
          image_uploader.append(image[4])
          image_tag.append(image[5])
          image_latitude.append(image[6])
          image_longitude.append(image[7])

          
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
                            image_tag = image_tag,
                            current_source = data.station)

def get_records():
    """getting records from users at website's form"""
    from_date_str   = request.args.get('from',time.strftime("%Y-%m-%d %H:%M")) #Get the from date value from the URL
    to_date_str     = request.args.get('to',time.strftime("%Y-%m-%d %H:%M"))   #Get the to date value from the URL

    timezone 		= request.args.get('timezone','Etc/UTC')
    range_h_form	= request.args.get('range_h','');  #This will return a string, if field range_h exists in the request
    range_h_int 	= "nan"  # initialise this variable with not a number
    img_source       = request.args.get('station','end device 1')                           #Get img_source, or fall back to end device 1

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

    return [timezone, from_date_str, to_date_str, img_source]


def validate_date(d):
    try:
        datetime.datetime.strptime(d, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False

    
if __name__ == "__main__":
    app.run(debug=True)
    # app.run(debug=True, host='0.0.0.0', port=8080) #using thisline causing error to static path




