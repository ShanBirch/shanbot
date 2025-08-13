from datetime import datetime, timedelta

current_date = datetime.now()
print(
    f"Current date: {current_date.strftime('%Y-%m-%d')} (weekday: {current_date.weekday()})")
print(f"Current week: {current_date.strftime('%Y-W%U')}")

# Calculate the start of the current week (Sunday)
# Monday=0, so Sunday=6, adjust to Sunday=0
days_since_sunday = current_date.weekday() + 1
if days_since_sunday == 7:  # If today is Sunday
    days_since_sunday = 0
week_start = current_date - timedelta(days=days_since_sunday)
week_start_str = week_start.strftime('%Y-%m-%d')

print(f"Days since Sunday: {days_since_sunday}")
print(f"Week start (calculated): {week_start_str}")

# Let's also check what dates should be in this week
print("\nDates that should be in current week:")
for i in range(7):
    date = week_start + timedelta(days=i)
    print(f"  {date.strftime('%Y-%m-%d')} ({date.strftime('%A')})")

print(f"\nWorkout dates from Kristy:")
workout_dates = ['2025-05-23', '2025-05-22', '2025-05-19']
for date_str in workout_dates:
    date = datetime.strptime(date_str, '%Y-%m-%d')
    print(f"  {date_str} >= {week_start_str}? {date_str >= week_start_str}")
