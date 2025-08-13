#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('app/analytics_data_good.sqlite')
c = conn.cursor()

print("Follow-back status breakdown (last 7 days):")
c.execute("""
    SELECT follow_back_status, COUNT(*) 
    FROM processing_queue 
    WHERE DATE(followed_at) >= DATE('now', '-7 days') 
    GROUP BY follow_back_status
""")

results = c.fetchall()
for r in results:
    status = r[0] if r[0] else "NULL/Unchecked"
    print(f'{status}: {r[1]} users')

print("\nDM status breakdown (last 7 days):")
c.execute("""
    SELECT dm_status, COUNT(*) 
    FROM processing_queue 
    WHERE DATE(followed_at) >= DATE('now', '-7 days') 
    GROUP BY dm_status
""")

dm_results = c.fetchall()
for r in dm_results:
    status = r[0] if r[0] else "NULL/No DM"
    print(f'{status}: {r[1]} users')

# Check specifically for users marked as "no" but who might have actually followed back
print("\nUsers marked as 'no follow back' (sample):")
c.execute("""
    SELECT username, followed_at, follow_back_status, dm_status 
    FROM processing_queue 
    WHERE follow_back_status = 'no' 
    AND DATE(followed_at) >= DATE('now', '-7 days')
    LIMIT 10
""")

no_followback = c.fetchall()
for r in no_followback:
    print(f'{r[0]} | {r[1]} | {r[2]} | {r[3]}')

conn.close()
