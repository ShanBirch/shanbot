import sqlite3
import json
from datetime import datetime, timedelta


def analyze_sqlite_database():
    """Analyze the SQLite database to find workout data structure"""

    db_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🗄️ SQLite Database Analysis")
        print("=" * 60)

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print("📋 Available Tables:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   📊 {table_name}: {count} records")

        print("\n" + "=" * 60)

        # Look for workout-related tables
        workout_tables = []
        for table in tables:
            table_name = table[0].lower()
            if any(keyword in table_name for keyword in ['workout', 'exercise', 'set', 'training', 'lift']):
                workout_tables.append(table[0])

        print(f"🏋️ Potential Workout Tables: {workout_tables}")

        # Analyze each workout table
        for table_name in workout_tables:
            print(f"\n📋 Table: {table_name}")
            print("-" * 40)

            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            print("Columns:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                print(f"   📝 {col_name}: {col_type}")

            # Get sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample_data = cursor.fetchall()

            if sample_data:
                print("\nSample Data:")
                for i, row in enumerate(sample_data):
                    print(f"   Row {i+1}: {row}")
            else:
                print("   No data in table")

        # Look for any table with weight/reps data
        print(f"\n🔍 Searching all tables for weight/reps data...")

        found_workout_data = False
        for table in tables:
            table_name = table[0]
            try:
                # Check if table has weight/reps columns
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                column_names = [col[1].lower() for col in columns]

                has_weight = any('weight' in col for col in column_names)
                has_reps = any('rep' in col for col in column_names)
                has_exercise = any('exercise' in col for col in column_names)

                if has_weight and has_reps:
                    print(f"\n💪 Found workout data in table: {table_name}")
                    print(f"   Columns: {[col[1] for col in columns]}")

                    # Get recent data
                    cursor.execute(
                        f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 5")
                    recent_data = cursor.fetchall()

                    print("   Recent data:")
                    for i, row in enumerate(recent_data):
                        print(f"      {i+1}: {row}")

                    found_workout_data = True

                    # Try to find users with workout data
                    if has_exercise:
                        cursor.execute(
                            f"SELECT DISTINCT client_name FROM {table_name} WHERE client_name IS NOT NULL LIMIT 10")
                        users = cursor.fetchall()
                        if users:
                            print(f"   Users with workout data:")
                            for user in users:
                                print(f"      👤 {user[0]}")

            except Exception as e:
                # Skip tables that cause errors
                continue

        if not found_workout_data:
            print("❌ No tables found with weight/reps data")

            # Let's check all table schemas anyway
            print("\n📋 All Table Schemas:")
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                # Look for any potentially relevant columns
                relevant_cols = []
                for col in columns:
                    col_name = col[1].lower()
                    if any(keyword in col_name for keyword in ['workout', 'exercise', 'weight', 'rep', 'set', 'data', 'performance']):
                        relevant_cols.append(col[1])

                if relevant_cols:
                    print(f"   {table_name}: {relevant_cols}")

        conn.close()

    except Exception as e:
        print(f"Error analyzing SQLite database: {e}")
        import traceback
        traceback.print_exc()


def find_test_user_with_workouts():
    """Find a specific user with good workout data for testing"""

    db_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Look for workout data tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]

        workout_table = None
        for table_name in tables:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1].lower() for col in columns]

            has_weight = any('weight' in col for col in column_names)
            has_reps = any('rep' in col for col in column_names)

            if has_weight and has_reps:
                workout_table = table_name
                break

        if workout_table:
            print(f"\n🎯 Found workout data in table: {workout_table}")

            # Find users with most recent workout data
            cursor.execute(f"""
                SELECT client_name, COUNT(*) as workout_count, MAX(date) as last_workout
                FROM {workout_table} 
                WHERE client_name IS NOT NULL 
                GROUP BY client_name 
                ORDER BY workout_count DESC, last_workout DESC 
                LIMIT 5
            """)

            users = cursor.fetchall()
            print("🏆 Top users for testing:")
            for user in users:
                print(f"   👤 {user[0]}: {user[1]} workouts, last: {user[2]}")

            if users:
                test_user = users[0][0]
                print(f"\n🧪 RECOMMENDED TEST USER: {test_user}")

                # Get sample workout data for this user
                cursor.execute(f"""
                    SELECT * FROM {workout_table} 
                    WHERE client_name = ? 
                    ORDER BY date DESC 
                    LIMIT 10
                """, (test_user,))

                recent_workouts = cursor.fetchall()
                print(f"Recent workout data for {test_user}:")
                for workout in recent_workouts:
                    print(f"   📊 {workout}")

                return test_user, workout_table

        conn.close()
        return None, None

    except Exception as e:
        print(f"Error finding test user: {e}")
        return None, None


if __name__ == "__main__":
    print("🔍 Analyzing SQLite database structure...")
    analyze_sqlite_database()

    print("\n" + "=" * 60)
    print("🧪 Finding test user for Progressive Overload AI...")
    test_user, workout_table = find_test_user_with_workouts()

    if test_user and workout_table:
        print(f"\n✅ Ready to test Progressive Overload AI!")
        print(f"   👤 User: {test_user}")
        print(f"   📊 Table: {workout_table}")
    else:
        print(f"\n❌ No suitable test user found")
