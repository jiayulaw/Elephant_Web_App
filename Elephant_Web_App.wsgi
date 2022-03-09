import sys
sys.path.insert(0, "/var/www/Elephant_Web_App")
sys.path.append('/var/www/Elephant_Web_App/env/lib/python3.8/site-packages/')
from app import app as application

from app import update_server_thread
import threading
thread1 = threading.Thread(target = update_server_thread)
thread1.daemon = True
thread1.start()