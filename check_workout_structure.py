#!/usr/bin/env python3
import sqlite3

# Connect to database
conn = sqlite3.connect('comprehensive_workout_storage.db')
cursor = conn.cursor()

# First check what tables exist
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = [row[0] for row in cursor.fetchall()]
print(f"Available tables: {tables}")

# Check the structure of client_workout_sessions table
if 'client_workout_sessions' in tables:
    cursor.execute('PRAGMA table_info(client_workout_sessions)')
    columns = cursor.fetchall()
    print(f"\nclient_workout_sessions columns: {[col[1] for col in columns]}")

    # Get Alice's workout structure
    cursor.execute('''
        SELECT workout_name, exercise_name, date 
        FROM client_workout_sessions 
        WHERE client_name = "alice_forster" 
        ORDER BY date DESC
        LIMIT 10
    ''')

    results = cursor.fetchall()
    print("\nAlice's recent workout data:")
    for row in results:
        workout_name, exercise_name, date = row
        print(f"  {date}: {workout_name} - {exercise_name}")

    # Get distinct workout names for Alice
    cursor.execute('''
        SELECT DISTINCT workout_name 
        FROM client_workout_sessions 
        WHERE client_name = "alice_forster"
    ''')

    workout_names = [row[0] for row in cursor.fetchall()]
    print(f"\nAlice's workout names: {workout_names}")
else:
    print("client_workout_sessions table not found")

conn.close()
