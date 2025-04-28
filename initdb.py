import sqlite3
import bcrypt  # Make sure to install this with: pip install bcrypt
import random

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
scooters = [
    (0, 63.41536, 10.40658, False, 50),
    (1, 63.41720, 10.40640, False, 70),
    (2, 63.41969, 10.40276, True, 60),
    (3, 63.421977, 10.408439, True, 80)
]


# Insert scooters into the database
cursor.executemany("INSERT INTO scootere (id, latitude, longitude, available, battery) VALUES (?, ?, ?, ?, ?)", scooters)

# Add tasks (10 tasks, each connected to a different scooter)
tasks = []
for i in range(1, 4):  # Creating 10 tasks
    tasks.append((
        i,  # scooterid (connected to scooters created above)
        0,  # brukerid (unassigned at the moment)
        63.41535 + random.uniform(-0.005, 0.005),  # latitude
        10.40657 + random.uniform(-0.005, 0.005),  # longitude
        random.uniform(5.0, 20.0),  # radius in meters
        random.randint(10, 50)  # reward points
    ))

# Insert tasks into the database
cursor.executemany("INSERT INTO oppgaver (scooterid, brukerid, latitude, longitude, radius, reward) VALUES (?, ?, ?, ?, ?, ?)", tasks)

# Commit changes and close the connection
con.commit()

# Display inserted data for confirmation
cursor.execute("SELECT * FROM brukere")
print("Users:", cursor.fetchall())

cursor.execute("SELECT * FROM scootere LIMIT 10")
print("Scooters (first 10):", cursor.fetchall())

cursor.execute("SELECT * FROM oppgaver")
print("Tasks:", cursor.fetchall())

con.close()
