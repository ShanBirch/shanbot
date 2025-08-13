import sqlite3

conn = sqlite3.connect('app/analytics_data_good.sqlite')
cursor = conn.cursor()

# Check table structure
try:
    cursor.execute("PRAGMA table_info(new_leads)")
    columns = cursor.fetchall()
    print('new_leads table structure:')
    for col in columns:
        print(f'  - {col[1]} ({col[2]})')

    cursor.execute('SELECT COUNT(*) FROM new_leads')
    count = cursor.fetchone()[0]
    print(f'\nTotal leads in new_leads table: {count}')

    if count > 0:
        # Get first few rows to see the data
        cursor.execute('SELECT * FROM new_leads LIMIT 3')
        users = cursor.fetchall()
        print('\nSample leads:')
        for i, row in enumerate(users):
            print(f'Lead {i+1}: {row}')

except sqlite3.OperationalError as e:
    print(f'Error: {e}')

conn.close()
