import sqlite3
import bcrypt  # Make sure to install this with: pip install bcrypt

# Connect to your database
con = sqlite3.connect("database.db")
cursor = con.cursor()

# Optional: Create tables from your .sql schema
with open('database.sql', 'r') as sql_file:
    con.executescript(sql_file.read())

# User info
navn = 'admin'
plain_password = 'mypassword123'

# Hash the password
hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())

# Insert user — make sure to include NULL for auto-increment id
cursor.execute("INSERT INTO brukere VALUES (?, ?, ?)", (None, navn, hashed_password))

# Save and close
con.commit()
a = cursor.execute("SELECT * FROM brukere")
print(a.fetchone())
con.close()
