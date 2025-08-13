#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('app/analytics_data_good.sqlite')
c = conn.cursor()

print("Unchecked users by date (last 7 days):")
c.execute("""
    SELECT DATE(followed_at) as date, COUNT(*) as count 
    FROM processing_queue 
    WHERE (follow_back_status IS NULL OR follow_back_status = 'pending') 
    AND (dm_status IS NULL OR dm_status != 'sent') 
    AND followed_at >= DATE('now', '-7 days') 
    AND followed_at < DATE('now', 'start of day') 
    GROUP BY DATE(followed_at) 
    ORDER BY date DESC
""")

results = c.fetchall()
for r in results:
    print(f'{r[0]}: {r[1]} users')

print(f"\nTotal unchecked: {sum(r[1] for r in results)} users")
conn.close()
