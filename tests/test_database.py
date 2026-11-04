import sqlite3

connection = sqlite3.connect("database/learnable.db")
cursor = connection.cursor()

cursor.execute("SELECT * FROM student_profiles")
profiles = cursor.fetchall()

print("Saved Student Profiles:")
for profile in profiles:
    print(profile)

connection.close()