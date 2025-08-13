#!/usr/bin/env python3
"""
Script to extract and analyze conversation history from Shanbot database.
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime
from pathlib import Path


def connect_to_database(db_path):
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect(db_path)
        print(f"Connected to database: {db_path}")
        return conn
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return None


def explore_database_structure(conn):
    """Explore and display database structure"""
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("=== DATABASE STRUCTURE ===")
    db_structure = {}

    for table in tables:
        table_name = table[0]

        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]

        db_structure[table_name] = {
            'columns': [{'name': col[1], 'type': col[2]} for col in columns],
            'row_count': row_count
        }

        print(f"\nTable: {table_name} ({row_count} rows)")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

    return db_structure


def extract_conversation_data(conn):
    """Extract conversation data from relevant tables"""
    conversation_data = {}

    # Tables that likely contain conversation data
    conversation_tables = [
        'response_review_queue',
        'scheduled_responses',
        'auto_mode_activity',
        'conversation_history',
        'messages',
        'chat_history',
        'user_conversations'
    ]

    cursor = conn.cursor()

    for table_name in conversation_tables:
        try:
            # Check if table exists
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            if cursor.fetchone():
                # Extract data
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                if not df.empty:
                    conversation_data[table_name] = df
                    print(f"Extracted {len(df)} records from {table_name}")
                else:
                    print(f"Table {table_name} is empty")
        except Exception as e:
            print(f"Error with table {table_name}: {e}")

    return conversation_data


def analyze_conversations(conversation_data):
    """Analyze conversation data"""
    analysis = {}

    for table_name, df in conversation_data.items():
        print(f"\n=== ANALYZING {table_name.upper()} ===")
        print(f"Total records: {len(df)}")
        print(f"Columns: {list(df.columns)}")

        # Show sample data
        if len(df) > 0:
            print("\nSample records:")
            print(df.head(3))

        # Try to find date columns
        date_columns = [col for col in df.columns if any(
            word in col.lower() for word in ['date', 'time', 'created', 'updated'])]
        if date_columns:
            print(f"\nDate columns found: {date_columns}")

        analysis[table_name] = {
            'total_records': len(df),
            'columns': list(df.columns),
            'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
        }

    return analysis


def save_data(conversation_data, analysis, output_dir="conversation_analysis"):
    """Save extracted data and analysis"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save conversation data as CSV
    for table_name, df in conversation_data.items():
        output_file = output_path / f"{table_name}_data_{timestamp}.csv"
        df.to_csv(output_file, index=False)
        print(f"Saved {table_name} data to {output_file}")

    # Save analysis as JSON
    analysis_file = output_path / f"conversation_analysis_{timestamp}.json"
    with open(analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    print(f"Saved analysis to {analysis_file}")

    return output_path


def main():
    """Main function"""
    # Database path
    db_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

    # Connect to database
    conn = connect_to_database(db_path)
    if not conn:
        return

    try:
        # Explore database structure
        db_structure = explore_database_structure(conn)

        # Extract conversation data
        conversation_data = extract_conversation_data(conn)

        if conversation_data:
            # Analyze conversations
            analysis = analyze_conversations(conversation_data)

            # Save data
            output_path = save_data(conversation_data, analysis)
            print(f"\n=== DATA SAVED TO: {output_path} ===")
        else:
            print("No conversation data found")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
