import sqlite3
import bcrypt  # Make sure to install this with: pip install bcrypt

# Connect to your SQLite3 database
con = sqlite3.connect("database.db")
cursor = con.cursor()

# Read and execute the SQL schema from the file
with open('database.sql', 'r') as sql_file:
    con.executescript(sql_file.read())

# Add an admin user
admin_name = 'admin'
admin_password = 'mypassword123'

# Hash the password
hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())

# Insert admin user
cursor.execute("INSERT INTO brukere (navn, passord, reward) VALUES (?, ?, ?)", (admin_name, hashed_password, 0))

# Add scooters

import random

scooters = [
    (1, 63.41535, 10.40657, True),
    (2, 63.41969, 10.40276, False),
    (3 ,63.421977, 10.408439, True)
]


for i in range(4,100):
    scooters.append((i,scooters[0][1]+random.randint(-100,100)/10000,scooters[0][2]+random.randint(-100,100)/10000,True))

cursor.executemany("INSERT INTO scootere (id, latitude, longitude, available) VALUES (?, ?, ?, ?)", scooters)

# Commit changes and close the connection
con.commit()

# Display inserted data for confirmation
cursor.execute("SELECT * FROM brukere")
print("Users:", cursor.fetchall())

cursor.execute("SELECT * FROM scootere")
print("Scooters:", cursor.fetchall())

con.close()
