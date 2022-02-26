import datetime
import time
import pytz

#obtain date time in UTC 
UTC_datetime = datetime.datetime.utcnow()
print("current UTC time")
print(UTC_datetime)

#current date time in local timezone
local_datetime = datetime.datetime.now()
print("current Local time")
print(local_datetime)

#convert datetime from local to UTC
def Local2UTC_time(LocalTime):
    EpochSecond = time.mktime(LocalTime.timetuple())
    utcTime = datetime.datetime.utcfromtimestamp(EpochSecond)
    return utcTime

UTC_datetime = Local2UTC_time(local_datetime)
print("current UTC time")
print(UTC_datetime)


#convert naive datetime string to UTC
status = "26/02/2022, 18:10:47"
datetime_object = datetime.datetime.strptime(status, '%d/%m/%Y, %H:%M:%S')
timezone = pytz.timezone("Asia/Kuala_Lumpur")
datetime_object_timezone = timezone.localize(datetime_object, is_dst=None)
utc_datetime = datetime_object_timezone.astimezone(pytz.utc)
print("method 1")
print(Local2UTC_time(datetime_object_timezone))
print("method 2")
print(utc_datetime)
