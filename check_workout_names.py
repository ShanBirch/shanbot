#!/usr/bin/env python3
import sqlite3

# Connect to database
conn = sqlite3.connect('comprehensive_workout_storage.db')
cursor = conn.cursor()

# Get Alice's workout names
cursor.execute(
    'SELECT DISTINCT workout_name FROM workout_goals WHERE client_name LIKE "Alice%"')
alice_workouts = [row[0] for row in cursor.fetchall()]
print("Alice's workout names:", alice_workouts)

# Get all distinct workout names
cursor.execute('SELECT DISTINCT workout_name FROM workout_goals')
all_workouts = [row[0] for row in cursor.fetchall()]
print("All workout names:", all_workouts)

conn.close()
