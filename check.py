import sqlite3; conn=sqlite3.connect('app/analytics_data_good.sqlite'); c=conn.cursor(); c.execute('SELECT COUNT(*) FROM new_leads WHERE created_at >= date(\
now\, \-1
day\)'); print('Today:', c.fetchone()[0]); c.execute('SELECT COUNT(*) FROM new_leads'); print('Total:', c.fetchone()[0]); conn.close()
