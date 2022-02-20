
import sqlite3
import os

#need to set base dir to prevent path issue in pythonanywhere
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database.sqlite")

#=======================================================
#===========List out tables in db================
#=======================================================
#https://www.kite.com/python/answers/how-to-list-tables-using-sqlite3-in-python
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())

