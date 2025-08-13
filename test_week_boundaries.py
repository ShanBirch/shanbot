from datetime import datetime, timedelta
import sqlite3

# Test the week boundary calculations
current_date = datetime.now()
print(
    f"Current date: {current_date.strftime('%Y-%m-%d')} (weekday: {current_date.weekday()})")
print(f"Current week: {current_date.strftime('%Y-W%U')}")

# Calculate the start of the current week (Sunday)
days_since_sunday = (current_date.weekday() + 1) % 7
week_start = current_date - timedelta(days=days_since_sunday)
week_end = week_start + timedelta(days=6)  # Saturday

week_start_str = week_start.strftime('%Y-%m-%d')
week_end_str = week_end.strftime('%Y-%m-%d')

print(f"\nCurrent week boundaries:")
print(f"Week start (Sunday): {week_start_str}")
print(f"Week end (Saturday): {week_end_str}")

# Calculate previous week boundaries
prev_week_start = week_start - timedelta(days=7)
prev_week_end = week_start - timedelta(days=1)
prev_week_start_str = prev_week_start.strftime('%Y-%m-%d')
prev_week_end_str = prev_week_end.strftime('%Y-%m-%d')

print(f"\nPrevious week boundaries:")
print(f"Previous week start: {prev_week_start_str}")
print(f"Previous week end: {prev_week_end_str}")

# Check what workout dates we have
SQLITE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"
conn = sqlite3.connect(SQLITE_PATH)
cursor = conn.cursor()

cursor.execute('''
    SELECT workout_date, week_identifier, workout_name 
    FROM client_workout_sessions 
    WHERE ig_username = "Kristyleecoop" 
    ORDER BY workout_date DESC
''')

workouts = cursor.fetchall()
print(f"\nKristy's workout dates:")
for workout in workouts:
    workout_date = workout[0]
    week_id = workout[1]
    workout_name = workout[2]

    # Check which week this falls into
    if prev_week_start_str <= workout_date <= prev_week_end_str:
        week_category = "PREVIOUS WEEK"
    elif week_start_str <= workout_date <= week_end_str:
        week_category = "CURRENT WEEK"
    else:
        week_category = "OTHER"

    print(f"  {workout_date} | {week_id} | {workout_name} | {week_category}")

conn.close()
