#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Tool
===================================
Migrates all data from your local SQLite database to PostgreSQL on Render.
"""

import sqlite3
import psycopg2
import psycopg2.extras
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database paths
SQLITE_DB_PATH = r"app\analytics_data_good.sqlite"
# Set this to your Render PostgreSQL URL
POSTGRES_URL = os.getenv('DATABASE_URL')


class DatabaseMigrator:
    """Handles migration from SQLite to PostgreSQL."""

    def __init__(self, sqlite_path: str, postgres_url: str):
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url
        self.tables_migrated = []
        self.total_records = 0

    def get_sqlite_tables(self) -> List[str]:
        """Get list of all tables in SQLite database."""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        conn.close()
        return tables

    def get_table_schema(self, table_name: str) -> List[Dict]:
        """Get schema information for a table."""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'name': row[1],
                'type': row[2],
                'notnull': row[3],
                'default': row[4],
                'pk': row[5]
            })

        conn.close()
        return columns

    def sqlite_to_postgres_type(self, sqlite_type: str) -> str:
        """Convert SQLite data types to PostgreSQL equivalents."""
        type_mapping = {
            'INTEGER': 'INTEGER',
            'TEXT': 'TEXT',
            'REAL': 'REAL',
            'BOOLEAN': 'BOOLEAN',
            'BLOB': 'BYTEA',
            'DATETIME': 'TIMESTAMP',
            'VARCHAR': 'VARCHAR',
            'CHAR': 'CHAR'
        }

        sqlite_type = sqlite_type.upper()

        # Handle complex types
        if 'PRIMARY KEY AUTOINCREMENT' in sqlite_type or sqlite_type == 'INTEGER' and 'pk' in str(sqlite_type):
            return 'SERIAL PRIMARY KEY'
        elif 'VARCHAR(' in sqlite_type:
            return sqlite_type
        elif sqlite_type in type_mapping:
            return type_mapping[sqlite_type]
        else:
            # Default to TEXT for unknown types
            return 'TEXT'

    def create_postgres_table(self, table_name: str, columns: List[Dict]) -> str:
        """Generate CREATE TABLE statement for PostgreSQL."""
        column_defs = []

        for col in columns:
            col_def = f'"{col["name"]}" '

            if col['pk'] and col['type'].upper() == 'INTEGER':
                col_def += 'SERIAL PRIMARY KEY'
            else:
                col_def += self.sqlite_to_postgres_type(col['type'])

                if col['notnull'] and not col['pk']:
                    col_def += ' NOT NULL'

                if col['default'] and not col['pk']:
                    if col['default'].upper() in ['TRUE', 'FALSE']:
                        col_def += f' DEFAULT {col["default"]}'
                    elif col['default'].upper() == 'CURRENT_TIMESTAMP':
                        col_def += ' DEFAULT CURRENT_TIMESTAMP'
                    elif col['default'] != 'NULL':
                        col_def += f' DEFAULT {col["default"]}'

            column_defs.append(col_def)

        return f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(column_defs)})'

    def get_table_data(self, table_name: str) -> List[Dict]:
        """Get all data from a SQLite table."""
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        cursor = conn.cursor()

        cursor.execute(f'SELECT * FROM "{table_name}"')
        rows = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return rows

    def insert_postgres_data(self, table_name: str, data: List[Dict], columns: List[Dict]):
        """Insert data into PostgreSQL table."""
        if not data:
            logger.info(f"No data to insert for table {table_name}")
            return

        conn = psycopg2.connect(self.postgres_url)
        cursor = conn.cursor()

        # Get non-primary key columns for INSERT
        insert_columns = [col['name']
                          for col in columns if not col['pk'] or col['name'] != 'id']

        # Handle cases where we need to include the primary key
        sample_row = data[0]
        if 'id' in sample_row and sample_row['id'] is not None:
            insert_columns = [col['name'] for col in columns]

        # Prepare INSERT statement
        placeholders = ', '.join(['%s'] * len(insert_columns))
        column_names = ', '.join([f'"{col}"' for col in insert_columns])

        insert_sql = f'INSERT INTO "{table_name}" ({column_names}) VALUES ({placeholders})'

        # Handle ON CONFLICT for tables with unique constraints
        if any(col['name'] == 'subscriber_id' for col in columns):
            insert_sql += ' ON CONFLICT (subscriber_id) DO UPDATE SET '
            update_clauses = [
                f'"{col}" = EXCLUDED."{col}"' for col in insert_columns if col != 'subscriber_id']
            insert_sql += ', '.join(update_clauses)
        elif any(col['name'] == 'id' for col in columns):
            insert_sql += ' ON CONFLICT (id) DO UPDATE SET '
            update_clauses = [
                f'"{col}" = EXCLUDED."{col}"' for col in insert_columns if col != 'id']
            if update_clauses:
                insert_sql += ', '.join(update_clauses)
            else:
                insert_sql = insert_sql.replace(
                    ' ON CONFLICT (id) DO UPDATE SET ', ' ON CONFLICT (id) DO NOTHING')

        # Prepare data for insertion
        insert_data = []
        for row in data:
            row_data = []
            for col in insert_columns:
                value = row.get(col)
                # Handle JSON strings
                if value and isinstance(value, str) and col.endswith('_json'):
                    try:
                        # Validate JSON
                        json.loads(value)
                        row_data.append(value)
                    except json.JSONDecodeError:
                        row_data.append(None)
                # Handle encoding issues
                elif value and isinstance(value, str):
                    try:
                        # Ensure proper UTF-8 encoding
                        value.encode('utf-8')
                        row_data.append(value)
                    except UnicodeEncodeError:
                        # Replace problematic characters
                        cleaned_value = value.encode(
                            'utf-8', errors='replace').decode('utf-8')
                        row_data.append(cleaned_value)
                else:
                    row_data.append(value)
            insert_data.append(tuple(row_data))

        # Execute batch insert
        try:
            cursor.executemany(insert_sql, insert_data)
            conn.commit()
            logger.info(
                f"✅ Inserted {len(insert_data)} records into {table_name}")
            self.total_records += len(insert_data)
        except Exception as e:
            logger.error(f"❌ Error inserting data into {table_name}: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def migrate_table(self, table_name: str):
        """Migrate a single table from SQLite to PostgreSQL."""
        logger.info(f"🔄 Migrating table: {table_name}")

        # Get table schema
        columns = self.get_table_schema(table_name)
        if not columns:
            logger.warning(
                f"⚠️ No columns found for table {table_name}, skipping")
            return

        # Create table in PostgreSQL
        create_sql = self.create_postgres_table(table_name, columns)

        conn = psycopg2.connect(self.postgres_url)
        cursor = conn.cursor()

        try:
            cursor.execute(create_sql)
            conn.commit()
            logger.info(f"✅ Created table {table_name} in PostgreSQL")
        except Exception as e:
            logger.error(f"❌ Error creating table {table_name}: {e}")
            conn.rollback()
            cursor.close()
            conn.close()
            return

        cursor.close()
        conn.close()

        # Get and insert data
        data = self.get_table_data(table_name)
        if data:
            self.insert_postgres_data(table_name, data, columns)

        self.tables_migrated.append(table_name)

    def verify_migration(self):
        """Verify the migration was successful."""
        logger.info("🔍 Verifying migration...")

        sqlite_conn = sqlite3.connect(self.sqlite_path)
        postgres_conn = psycopg2.connect(self.postgres_url)

        for table_name in self.tables_migrated:
            # Count records in SQLite
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            sqlite_count = sqlite_cursor.fetchone()[0]

            # Count records in PostgreSQL
            postgres_cursor = postgres_conn.cursor()
            postgres_cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            postgres_count = postgres_cursor.fetchone()[0]

            if sqlite_count == postgres_count:
                logger.info(
                    f"✅ {table_name}: {sqlite_count} records (matches)")
            else:
                logger.warning(
                    f"⚠️ {table_name}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")

            postgres_cursor.close()

        sqlite_conn.close()
        postgres_conn.close()

    def run_migration(self):
        """Run the complete migration process."""
        logger.info("🚀 Starting SQLite to PostgreSQL migration...")

        # Check if files exist
        if not os.path.exists(self.sqlite_path):
            logger.error(f"❌ SQLite database not found: {self.sqlite_path}")
            return False

        if not self.postgres_url:
            logger.error("❌ PostgreSQL URL not provided")
            return False

        # Get all tables
        tables = self.get_sqlite_tables()
        logger.info(
            f"📋 Found {len(tables)} tables to migrate: {', '.join(tables)}")

        # Migrate each table
        for table in tables:
            try:
                self.migrate_table(table)
            except Exception as e:
                logger.error(f"❌ Failed to migrate table {table}: {e}")
                continue

        # Verify migration
        self.verify_migration()

        logger.info(
            f"🎉 Migration completed! Migrated {len(self.tables_migrated)} tables with {self.total_records} total records")
        return True


def main():
    """Main migration function."""
    print("🗄️ SQLite to PostgreSQL Migration Tool")
    print("=" * 50)

    # Check requirements
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"❌ SQLite database not found: {SQLITE_DB_PATH}")
        print("Make sure you're running this from the correct directory")
        return

    if not POSTGRES_URL:
        print("❌ PostgreSQL URL not found!")
        print("Set the DATABASE_URL environment variable:")
        print(
            "Example: export DATABASE_URL='postgresql://user:password@host:port/database'")
        print("\nFor Render, get this from your dashboard:")
        print("1. Go to your PostgreSQL service on Render")
        print("2. Copy the 'External Database URL'")
        print("3. Set it as DATABASE_URL environment variable")
        return

    print(f"📂 SQLite database: {SQLITE_DB_PATH}")
    print(f"🔗 PostgreSQL URL: {POSTGRES_URL[:30]}...")
    print()

    # Confirm before proceeding
    confirm = input("Do you want to proceed with the migration? (y/N): ")
    if confirm.lower() != 'y':
        print("Migration cancelled.")
        return

    # Run migration
    migrator = DatabaseMigrator(SQLITE_DB_PATH, POSTGRES_URL)
    success = migrator.run_migration()

    if success:
        print("\n🎉 Migration completed successfully!")
        print("Your SQLite data is now available in PostgreSQL on Render.")
        print("\nNext steps:")
        print("1. Test your webhook with the migrated data")
        print("2. Update your Render environment variables if needed")
        print("3. Deploy your updated code to Render")
    else:
        print("\n❌ Migration failed. Check the logs above for details.")


if __name__ == "__main__":
    main()
