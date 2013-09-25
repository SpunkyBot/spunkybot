### IMPORTS
import sqlite3
import time


### Main ###
# connect to database
connection = sqlite3.connect('../data.sqlite')
cursor = connection.cursor()

timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
values = (timestamp,)

# remove expired ban_points
cursor.execute("DELETE FROM `ban_points` WHERE `expires` < ?", values)
connection.commit()

# close database
connection.close()
