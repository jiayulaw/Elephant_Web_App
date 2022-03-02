import sys
sys.path.insert(0, "/var/www/Elephant_Web_App")
sys.path.append('/var/www/Elephant_Web_App/env/lib/python3.8/site-packages/')
from app import app as application

import datetime
f = open("test-uwsgi-running.txt", "w") 
f.write("The uwsgi is running!!" + str(datetime.datetime.now()))
f.close() 
#from app import background_task
#import threading
#t2 = threading.Thread(target = background_task, daemon=True).start()