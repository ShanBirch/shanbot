import sqlite3
import json


def examine_analytics_database():
    try:
        conn = sqlite3.connect('analytics_data_good.sqlite')
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print("Tables in analytics_data_good.sqlite:")
        print("=" * 50)

        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("-" * 30)

            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print("Columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")

            # Show sample data if table has data
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                sample_rows = cursor.fetchall()
                print("Sample data:")
                for i, row in enumerate(sample_rows, 1):
                    print(f"  Row {i}: {row}")

        conn.close()

    except Exception as e:
        print(f"Error examining database: {e}")


if __name__ == "__main__":
    examine_analytics_database()
