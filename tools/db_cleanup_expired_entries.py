### IMPORTS
import sqlite3
import time


### Main ###
# connect to database
connnection = sqlite3.connect('../data.sqlite')
cursor = connnection.cursor()

timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
values = (timestamp,)

# remove expired bans
cursor.execute("DELETE FROM `ban_list` WHERE `expires` < ?", values)
connnection.commit()

# remove expired ban_points
cursor.execute("DELETE FROM `ban_points` WHERE `expires` < ?", values)
connnection.commit()

# close database
connnection.close()
