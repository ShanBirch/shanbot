import sqlite3
from datetime import datetime

conn = sqlite3.connect('app/analytics_data_good.sqlite')
cursor = conn.cursor()

print("Current date:", datetime.now().strftime('%Y-%m-%d'))
print("Current week:", datetime.now().strftime('%Y-W%U'))
print()

cursor.execute('''
    SELECT workout_date, week_identifier, workout_name 
    FROM client_workout_sessions 
    WHERE ig_username = "Kristyleecoop" 
    ORDER BY workout_date DESC
''')

workouts = cursor.fetchall()
print(f"Kristy's workout data ({len(workouts)} sessions):")
for workout in workouts:
    print(f"  {workout[0]} | {workout[1]} | {workout[2]}")

conn.close()
