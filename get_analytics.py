#!/usr/bin/env python3

import sqlite3
import json


def get_high_potential_clients():
    try:
        conn = sqlite3.connect('app/analytics_data_good.sqlite')
        cursor = conn.cursor()

        # Check for conversation_analytics or similar table with scoring data
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%analytic%';")
        analytics_tables = [row[0] for row in cursor.fetchall()]
        print("Analytics tables:", analytics_tables)

        # Look at conversation_analytics structure
        cursor.execute("PRAGMA table_info(conversation_analytics);")
        columns = cursor.fetchall()
        print("\nconversation_analytics columns:", [col[1] for col in columns])

        # Get sample of conversation analytics
        cursor.execute("SELECT * FROM conversation_analytics LIMIT 5;")
        sample_data = cursor.fetchall()
        print("\nSample conversation_analytics data:")
        for i, row in enumerate(sample_data, 1):
            print(f"  Row {i}: {row}")

        # Look for high coaching scores
        print("\n=== Looking for high coaching scores ===")
        cursor.execute("""
            SELECT ig_username, 
                   CASE 
                       WHEN prompt_input LIKE '%coaching_potential_category%' THEN 
                           substr(prompt_input, instr(prompt_input, 'coaching_potential_category')+27, 10)
                       ELSE 'unknown'
                   END as coaching_score,
                   COUNT(*) as message_count
            FROM conversation_analytics 
            WHERE ig_username IS NOT NULL 
            GROUP BY ig_username 
            ORDER BY message_count DESC
            LIMIT 20;
        """)

        results = cursor.fetchall()
        print("\nTop users by message count:")
        for row in results:
            print(f"  {row[0]}: score={row[1]}, messages={row[2]}")

        # Try to find actual scoring patterns
        cursor.execute("""
            SELECT DISTINCT prompt_input 
            FROM conversation_analytics 
            WHERE prompt_input LIKE '%coaching%' OR prompt_input LIKE '%score%' OR prompt_input LIKE '%potential%'
            LIMIT 5;
        """)

        scoring_examples = cursor.fetchall()
        print("\nScoring prompt examples:")
        for example in scoring_examples:
            print(f"  {example[0][:200]}...")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    get_high_potential_clients()
