# https://thepythoncorner.com/posts/2019-01-13-how-to-create-a-watchdog-in-python-to-look-for-filesystem-changes/#
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


def on_created(event):
     print(f"hey, {event.src_path} has been created!")
 
def on_deleted(event):
     print(f"what?! Someone deleted {event.src_path}!")
 
def on_modified(event):
     print(f"hey buddy, {event.src_path} has been modified")
 
def on_moved(event):
    print(f"ok ok ok, someone moved {event.src_path} to {event.dest_path}")

patterns = ["*"]
ignore_patterns = None
ignore_directories = False
case_sensitive = True
my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)

my_event_handler.on_created = on_created
my_event_handler.on_deleted = on_deleted
my_event_handler.on_modified = on_modified
my_event_handler.on_moved = on_moved


path = r"C:\Users\user10\Desktop\Hobby\Programming\EEEY3 Project\Web App\Elephant_Web_App_v2\static\image uploads"
go_recursively = True
my_observer = Observer()
my_observer.schedule(my_event_handler, path, recursive=go_recursively)

my_observer.start()
try:
    while True:
            time.sleep(1)
except KeyboardInterrupt:
    my_observer.stop()       
    my_observer.join()



    
