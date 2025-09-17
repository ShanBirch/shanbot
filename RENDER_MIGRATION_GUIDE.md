# SQLite to Render PostgreSQL Migration Guide

This guide will help you migrate your entire SQLite database to PostgreSQL on Render so everything continues to work seamlessly.

## 🎯 Overview

Your current setup:
- **Local**: SQLite database at `app/analytics_data_good.sqlite`
- **Production**: PostgreSQL on Render
- **Issue**: Need to migrate all your existing data

## 📋 Prerequisites

1. **Render PostgreSQL Service**: Make sure you have a PostgreSQL service running on Render
2. **Database URL**: Get your PostgreSQL connection string from Render
3. **Python Environment**: Ensure you have the required packages

## 🚀 Step-by-Step Migration

### Step 1: Install Required Packages

```bash
pip install psycopg2-binary
```

### Step 2: Get Your Render PostgreSQL URL

1. Go to your [Render Dashboard](https://dashboard.render.com/)
2. Click on your PostgreSQL service
3. Copy the **External Database URL** (it looks like: `postgresql://user:password@host:port/database`)

### Step 3: Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:DATABASE_URL="postgresql://your-connection-string-here"
```

**Windows (Command Prompt):**
```cmd
set DATABASE_URL=postgresql://your-connection-string-here
```

**Mac/Linux:**
```bash
export DATABASE_URL="postgresql://your-connection-string-here"
```

### Step 4: Run the Migration

```bash
python migrate_to_render.py
```

The script will:
- ✅ Analyze your SQLite database structure
- ✅ Create matching tables in PostgreSQL
- ✅ Migrate all your data
- ✅ Verify the migration was successful

### Step 5: Update Your Render Environment

1. Go to your Render Web Service dashboard
2. Go to **Environment** tab
3. Make sure `DATABASE_URL` is set to your PostgreSQL URL
4. Deploy your latest code

## 🔍 What Gets Migrated

The migration tool will transfer:

### Core Tables:
- **users** - All your user data, analytics, and client information
- **messages** - Complete conversation history
- **pending_reviews** - All queued responses and reviews
- **learning_feedback_log** - Your AI training examples
- **conversation_history** - Message history and analytics
- **scheduled_responses** - Any scheduled messages

### Additional Tables:
- **user_nutrition_profiles** - Nutrition tracking data
- **meal_logs** - Calorie and meal tracking
- **workout_sessions** - Trainerize integration data
- **auto_mode_tracking** - Automation settings
- **conversation_strategy_log** - Vegan flow tracking
- **processing_queue** - Lead processing data
- **paid_challenge_bookings** - Challenge signup data

## 🛠️ Troubleshooting

### Common Issues:

#### 1. Connection Error
```
Error: could not connect to server
```
**Solution**: Check your DATABASE_URL is correct and accessible

#### 2. Permission Denied
```
Error: permission denied for database
```
**Solution**: Make sure your PostgreSQL user has CREATE/INSERT permissions

#### 3. Table Already Exists
```
Error: relation "table_name" already exists
```
**Solution**: The script handles this with `CREATE TABLE IF NOT EXISTS`

#### 4. Data Type Mismatch
```
Error: column "column_name" is of type boolean but expression is of type text
```
**Solution**: The migration script handles type conversions automatically

### Manual Verification:

Connect to your PostgreSQL database and check:

```sql
-- List all tables
\dt

-- Check user count
SELECT COUNT(*) FROM users;

-- Check recent messages
SELECT * FROM messages ORDER BY timestamp DESC LIMIT 5;

-- Verify data integrity
SELECT 
    (SELECT COUNT(*) FROM users) as user_count,
    (SELECT COUNT(*) FROM messages) as message_count,
    (SELECT COUNT(*) FROM pending_reviews) as review_count;
```

## 🔄 Testing the Migration

After migration, test your webhook:

1. **Deploy to Render** with the updated code
2. **Send a test message** through your Instagram/ManyChat bot
3. **Check the logs** to ensure no database errors
4. **Verify responses** are being generated correctly

## 📊 Migration Report

The migration script provides a detailed report:

```
🗄️ SQLite to PostgreSQL Migration Tool
==================================================
📂 SQLite database: app/analytics_data_good.sqlite
🔗 PostgreSQL URL: postgresql://user:pass@host...

🔄 Migrating table: users
✅ Created table users in PostgreSQL
✅ Inserted 150 records into users

🔄 Migrating table: messages
✅ Created table messages in PostgreSQL
✅ Inserted 2,847 records into messages

🔍 Verifying migration...
✅ users: 150 records (matches)
✅ messages: 2,847 records (matches)

🎉 Migration completed! Migrated 8 tables with 3,456 total records
```

## ⚡ Quick Migration (One Command)

If you're confident in your setup:

```bash
# Set your database URL and run migration in one go
DATABASE_URL="your-postgresql-url" python migrate_to_render.py
```

## 🔒 Data Security Notes

- ✅ **No data loss**: Original SQLite file remains untouched
- ✅ **Upsert logic**: Handles conflicts if you re-run migration
- ✅ **Type safety**: Automatic data type conversion
- ✅ **Verification**: Counts and validates all transferred data

## 🚨 Important Notes

1. **Backup First**: Always backup your SQLite database before migration
2. **Test Environment**: Consider testing on a staging database first
3. **Downtime**: Plan for brief downtime during the switch
4. **Environment Variables**: Make sure all Render env vars are correct

## 🎯 After Migration

Once migration is complete:

1. **Update Render Environment**: Ensure `DATABASE_URL` is set
2. **Deploy Updated Code**: Push your database-aware code
3. **Monitor Logs**: Watch for any remaining compatibility issues
4. **Test All Features**: Verify webhook, analytics, and dashboard work

## 📞 Support

If you encounter issues:

1. Check the migration logs for specific error messages
2. Verify your PostgreSQL connection string
3. Ensure all required Python packages are installed
4. Test the connection manually with a PostgreSQL client

Your SQLite database will now be fully replicated in PostgreSQL on Render! 🎉

