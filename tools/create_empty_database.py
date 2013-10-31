### IMPORTS
import sqlite3


### Main ###
# connect to database
connection = sqlite3.connect('data.sqlite')
cursor = connection.cursor()

# create the database
cursor.execute('CREATE TABLE xlrstats ("id" INTEGER PRIMARY KEY NOT NULL, "guid" TEXT NOT NULL, "name" TEXT NOT NULL, "ip_address" TEXT NOT NULL, "first_seen" DATETIME, "last_played" DATETIME, "num_played" INTEGER DEFAULT 1, "kills" INTEGER DEFAULT 0, "deaths" INTEGER DEFAULT 0, "headshots" INTEGER DEFAULT 0, "team_kills" INTEGER DEFAULT 0, "team_death" INTEGER DEFAULT 0, "max_kill_streak" INTEGER DEFAULT 0, "suicides" INTEGER DEFAULT 0, "ratio" REAL DEFAULT 0, "rounds" INTEGER DEFAULT 0, "admin_role" INTEGER DEFAULT 1)')
cursor.execute('CREATE TABLE player ("id" INTEGER PRIMARY KEY NOT NULL, "guid" TEXT NOT NULL, "name" TEXT NOT NULL, "ip_address" TEXT NOT NULL, "time_joined" DATETIME, "aliases" TEXT)')
cursor.execute('CREATE TABLE ban_list ("id" INTEGER PRIMARY KEY NOT NULL, "guid" TEXT NOT NULL, "name" TEXT, "ip_address" TEXT, "expires" DATETIME DEFAULT 259200, "timestamp" DATETIME, "reason" TEXT)')
cursor.execute('CREATE TABLE ban_points ("id" INTEGER PRIMARY KEY NOT NULL, "guid" TEXT NOT NULL, "point_type" TEXT, "expires" DATETIME)')

# close database
connection.close()
