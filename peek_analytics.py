#!/usr/bin/env python3

import json


def peek_analytics():
    files_to_check = [
        'app/analytics_data_good_backup.json',
        'app/analytics_data.json',
        'app/anakytics_Data_backup2105.json'
    ]

    for filepath in files_to_check:
        try:
            print(f"\n=== Checking {filepath} ===")
            with open(filepath, 'r') as f:
                # Read first few lines to understand structure
                content = f.read(2000)  # First 2KB
                print(f"First 2000 characters:")
                print(content)
                print("\n" + "="*50)

                # Try to parse as JSON
                f.seek(0)
                try:
                    data = json.load(f)
                    print(f"JSON structure:")
                    if isinstance(data, dict):
                        print(f"Keys: {list(data.keys())}")
                        # Look for user data
                        for key, value in data.items():
                            if isinstance(value, dict) and len(value) < 10:
                                print(f"{key}: {value}")
                            elif isinstance(value, list) and len(value) > 0:
                                print(f"{key}: list with {len(value)} items")
                                if len(value) > 0:
                                    print(f"First item: {value[0]}")
                            break
                    elif isinstance(data, list):
                        print(f"List with {len(data)} items")
                        if len(data) > 0:
                            print(f"First item: {data[0]}")
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")

        except FileNotFoundError:
            print(f"File not found: {filepath}")
        except Exception as e:
            print(f"Error reading {filepath}: {e}")


if __name__ == "__main__":
    peek_analytics()
