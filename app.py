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
import git
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

class end_device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Video(name = {name}, status = {status}, message = {message})"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)#username must be unique
    password = db.Column(db.String(80), nullable=False)
    access_level = db.Column(db.String(20), nullable=False)
    
    def has_role(self, role_name):
        #my_role = User.query.filter_by(access_level=role_name).first()
        if role_name == self.access_level:
            return True
        else:
            return False

    
#db.create_all()
def require_role(role):
    """make sure user has this role"""
    def decorator(func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            if not current_user.has_role(role):
                return redirect("/")
            else:
                return func(*args, **kwargs)
        return wrapped_function
    return decorator
#------------------------------------------------------------
#-------------------------Initialization of variables-------------------------
#------------------------------------------------------------

#------------------------------------------------------------
#-------------------------Device status query-------------------------
#------------------------------------------------------------
video_put_args = reqparse.RequestParser()
#help parameter is similar to error message we send back to sender when there is no valid input
#required parameter means the field is not optional
video_put_args.add_argument("name", type=str, help="Name of the video is required", required=True)
video_put_args.add_argument("status", type=int, help="Views of the video", required=True)
video_put_args.add_argument("message", type=int, help="Likes on the video", required=True)

video_update_args = reqparse.RequestParser()
video_update_args.add_argument("name", type=str, help="Name of the video is required")
video_update_args.add_argument("status", type=int, help="Views of the video")
video_update_args.add_argument("message", type=int, help="Likes on the video")

resource_fields = {
	'id': fields.Integer,
	'name': fields.String,
	'status': fields.Integer,
	'message': fields.Integer
}

#marshal_with to serialize object
class Video(Resource):
	@marshal_with(resource_fields)
	def get(self, video_id):
		result = end_device.query.filter_by(id=video_id).first()
		if not result:
			abort(404, message="Could not find video with that id")
		return result

	@marshal_with(resource_fields)
	def put(self, video_id):
		args = video_put_args.parse_args()
		result = end_device.query.filter_by(id=video_id).first()
		if result:
			abort(409, message="Video id taken...")

		video = end_device(id=video_id, name=args['name'], status=args['status'], message=args['message'])
		db.session.add(video)
		db.session.commit()
		return video, 201 #this number is just a number in http protocol, can change to other num

	@marshal_with(resource_fields)
	def patch(self, video_id):
		args = video_update_args.parse_args()
		result = end_device.query.filter_by(id=video_id).first()
		if not result:
			abort(404, message="Video doesn't exist, cannot update")

		if args['name']:
			result.name = args['name']
		if args['status']:
			result.status = args['status']
		if args['message']:
			result.message = args['message']

		db.session.commit()

		return result


	def delete(self, video_id):
		abort_if_video_id_doesnt_exist(video_id)
		del videos[video_id]
		return '', 204


api.add_resource(Video, "/video/<int:video_id>")

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
   
    access_level = StringField(validators=[InputRequired(), Length(min = 4, max = 20)], render_kw = {"placeholder": "Access code"})
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
@app.route("/")
@app.route("/dashboard")
@login_required #we can only access dashboard when logged in
def dashboard():
    return render_template('index.html', active_state = "dashboard")


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
@require_role(role="admin")
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username = form.username.data, password=hashed_password, access_level = form.access_level.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration Success')
        return redirect("/admin")
    return render_template("register.html", form = form, msg = None)


@app.route("/debug")
def debug():
    return render_template("debug.html", active_state = "debug")

@app.route("/test")
def test():
    return render_template("test.html")

@app.route("/about_us")
def about_us():
    return render_template("about_us.html", active_state = "about_us")

# @app.route("/data_center")
# def data_center():
#     return render_template("display_image.html", active_state = "data_center")

@app.route("/end_devices")
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
def display_image():
    timezone, from_date_str, to_date_str, station = get_records()
    start = datetime.datetime.strptime(from_date_str, "%Y-%m-%d %H:%M")
    end = datetime.datetime.strptime( to_date_str, "%Y-%m-%d %H:%M")
    query_image_1 =[]
    query_image_2 =[]
    query_image_3 =[]

    directory = rf"C:\Users\user10\Desktop\Hobby\Programming\EEEY3 Project\Elephant\Web_Dev\static\station_{station}" 
    for filename in os.listdir(directory):
        if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".jpeg"):
            date_time = filename.split(".")[0]
            print(date_time)
            date_time_obj = datetime.datetime.strptime(date_time, "%Y-%m-%d %H-%M")
            print(os.path.join(directory, filename))

            print(station)
            print(type(station))
            # add image within customer selected time frame to an array

            if ((station == '1') and (start <= date_time_obj <= end)):
                query_image_1.append(f"static/station_{station}/"+filename)
                #query_image.append(filename)
            
            elif ((station == '2') and (start <= date_time_obj <= end)):
                query_image_2.append(f"static/station_{station}/"+filename)

            elif ((station == '3') and (start <= date_time_obj <= end)):
                query_image_3.append(f"static/station_{station}/"+filename)


        else:
            continue

    #if station == "all":

    print("query_1:", query_image_1)
    print("query_2:", query_image_2)
    print("query_3:", query_image_3)
  
    return render_template( "display_image.html", 
                            from_date = from_date_str,
                            to_date = to_date_str,
                            query_string = request.query_string,
                            timezone = timezone,
                            station = station,
                            query_image_1 = query_image_1,
                            query_image_2 = query_image_2,
                            query_image_3 = query_image_3, active_state = "data_center")

def get_records():
    """getting records from users at website's form"""
    from_date_str   = request.args.get('from',time.strftime("%Y-%m-%d 00:00")) #Get the from date value from the URL
    to_date_str     = request.args.get('to',time.strftime("%Y-%m-%d %H:%M"))   #Get the to date value from the URL

    timezone 		= request.args.get('timezone','Etc/UTC');
    range_h_form	= request.args.get('range_h','');  #This will return a string, if field range_h exists in the request
    range_h_int 	= "nan"  # initialise this variable with not a number
    station       = request.args.get('station','1')                           #Get the sensor ID, or fall back to 1

    print ("REQUEST:")
    print (request.args)

    try:
        range_h_int	= int(range_h_form)
    except:
        print ("range_h_form not a number")


    print ("Received from browser: %s, %s, %s, %s" % (from_date_str, to_date_str, timezone, range_h_int))

    if not validate_date(from_date_str):			# Validate date format
        from_date_str 	= time.strftime("%Y-%m-%d 00:00")
    if not validate_date(to_date_str):
        to_date_str 	= time.strftime("%Y-%m-%d %H:%M")		# Validate date format

    print ('2. From: %s, to: %s, timezone: %s' % (from_date_str,to_date_str,timezone))

    # Create datetime object so that we can convert to UTC from the browser's local time
    from_date_obj       = datetime.datetime.strptime(from_date_str,'%Y-%m-%d %H:%M')
    to_date_obj         = datetime.datetime.strptime(to_date_str,'%Y-%m-%d %H:%M')

    # If range_h is defined, we don't need the from and to times
    if isinstance(range_h_int,int):
        arrow_time_from = arrow.utcnow().shift(hours=-range_h_int)
        arrow_time_to   = arrow.utcnow()
        from_date_utc   = arrow_time_from.strftime("%Y-%m-%d %H:%M")
        to_date_utc     = arrow_time_to.strftime("%Y-%m-%d %H:%M")
        from_date_str   = arrow_time_from.to(timezone).strftime("%Y-%m-%d %H:%M")
        to_date_str	    = arrow_time_to.to(timezone).strftime("%Y-%m-%d %H:%M")
    else:
        pass
	
    return [timezone, from_date_str, to_date_str, station] 

def validate_date(d):
    try:
        datetime.datetime.strptime(d, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False

    
if __name__ == "__main__":
    app.run(debug=True)
    # app.run(debug=True, host='0.0.0.0', port=8080) #using thisline causing error to static path




