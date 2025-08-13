import sqlite3
import json


def fix_rebecca_username():
    """Find and update Rebecca's Instagram username in the database"""
    db_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find Rebecca's current record
    print("🔍 Searching for Rebecca's record...")
    cursor.execute(
        "SELECT ig_username, first_name, last_name FROM users WHERE ig_username LIKE '%rebecca%' OR first_name LIKE '%rebecca%'")
    results = cursor.fetchall()

    print(f"Found {len(results)} matching records:")
    for row in results:
        print(f"  IG: {row[0]}, First: {row[1]}, Last: {row[2]}")

    # Update rebecca_dangelo to rebeccadangelo01
    print("\n🔧 Updating rebecca_dangelo to rebeccadangelo01...")
    cursor.execute(
        "UPDATE users SET ig_username = 'rebeccadangelo01' WHERE ig_username = 'rebecca_dangelo'")
    rows_updated = cursor.rowcount

    print(f"✅ Updated {rows_updated} records")

    # Verify the update
    print("\n✔️ Verifying update...")
    cursor.execute(
        "SELECT ig_username, first_name, last_name FROM users WHERE ig_username = 'rebeccadangelo01'")
    updated_record = cursor.fetchone()

    if updated_record:
        print(
            f"  New record: IG: {updated_record[0]}, First: {updated_record[1]}, Last: {updated_record[2]}")
    else:
        print("  ❌ No record found with new username")

    conn.commit()
    conn.close()

    print("\n🎉 Database update complete!")
    return updated_record is not None


if __name__ == "__main__":
    success = fix_rebecca_username()
    if success:
        print("\n📝 Ready to send Monday morning check-in to @rebeccadangelo01")
    else:
        print("\n❌ Update failed - check database manually")
