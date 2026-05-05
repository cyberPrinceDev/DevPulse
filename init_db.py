import sqlite3

# Connect to (or create) the database
connection = sqlite3.connect('devpulse.db')

# Read the schema file
with open('schema.sql') as f:
    connection.executescript(f.read())

connection.commit()
connection.close()
print("Database initialized successfully!")