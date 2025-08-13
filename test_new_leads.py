#!/usr/bin/env python3
"""
Test script for the new leads database integration
"""

import sqlite3
import json
import datetime
import os

# Database path
SQLITE_DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def create_test_leads():
    """Create some test leads data"""

    # Sample test leads
    test_leads = [
        {
            'username': 'plantbasedmama123',
            'hashtag_found': 'plantbasedmum',
            'coaching_score': 85,
            'coaching_reasons': [
                'Parenting indicator: mother with toddler',
                'Plant-based interest: vegan meal prep',
                'Fitness activity: home workouts'
            ],
            'analysis': {
                'posts_analyzed': 3,
                'interests': ['vegan cooking', 'toddler activities', 'home fitness'],
                'lifestyle_indicators': ['mother', 'plant-based eater', 'health-conscious'],
                'recent_activities': ['meal prep', 'playground visits', 'yoga'],
                'conversation_topics': [
                    'Topic 1 - Discuss balancing healthy eating with toddler meals',
                    'Topic 2 - Share tips for quick vegan meal prep',
                    'Topic 3 - Talk about fitting workouts into busy mum life',
                    'Topic 4 - Explore plant-based nutrition for growing families'
                ],
                'post_summaries': [
                    'Photo of colorful vegan lunch boxes for family',
                    'Video of toddler helping with meal prep',
                    'Mirror selfie after home workout session'
                ]
            },
            'timestamp': datetime.datetime.now().isoformat()
        },
        {
            'username': 'veganfitmum',
            'hashtag_found': 'veganmomlife',
            'coaching_score': 78,
            'coaching_reasons': [
                'Parenting indicator: mentions kids in bio',
                'Plant-based interest: vegan lifestyle',
                'Weight loss interest: transformation journey'
            ],
            'analysis': {
                'posts_analyzed': 3,
                'interests': ['vegan recipes', 'strength training', 'family time'],
                'lifestyle_indicators': ['mother of two', 'vegan', 'fitness enthusiast'],
                'recent_activities': ['gym sessions', 'meal planning', 'school runs'],
                'conversation_topics': [
                    'Topic 1 - Discuss vegan protein sources for active mums',
                    'Topic 2 - Share strength training routines for busy schedules',
                    'Topic 3 - Talk about maintaining energy levels on plant-based diet',
                    'Topic 4 - Explore family-friendly vegan meal ideas'
                ],
                'post_summaries': [
                    'Before and after transformation photo',
                    'Family dinner with colorful vegan dishes',
                    'Gym selfie showing strength training progress'
                ]
            },
            'timestamp': datetime.datetime.now().isoformat()
        },
        {
            'username': 'healthymumjourney',
            'hashtag_found': 'mumlife',
            'coaching_score': 65,
            'coaching_reasons': [
                'Parenting indicator: mum life content',
                'Health indicator: wellness journey',
                'Fitness activity: morning walks'
            ],
            'analysis': {
                'posts_analyzed': 3,
                'interests': ['wellness', 'mindful eating', 'walking'],
                'lifestyle_indicators': ['busy mum', 'health-focused', 'self-care advocate'],
                'recent_activities': ['morning walks', 'meditation', 'healthy cooking'],
                'conversation_topics': [
                    'Topic 1 - Discuss finding time for self-care as a mum',
                    'Topic 2 - Share tips for mindful eating with kids around',
                    'Topic 3 - Talk about building sustainable wellness habits',
                    'Topic 4 - Explore stress management techniques for parents'
                ],
                'post_summaries': [
                    'Sunrise walk with coffee and gratitude caption',
                    'Healthy breakfast spread with family',
                    'Evening meditation setup in bedroom'
                ]
            },
            'timestamp': datetime.datetime.now().isoformat()
        }
    ]

    return test_leads


def create_leads_table():
    """Create the new_leads table if it doesn't exist"""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS new_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashtag_found TEXT,
                coaching_score INTEGER,
                coaching_reasons TEXT,
                posts_analyzed INTEGER,
                interests TEXT,
                lifestyle_indicators TEXT,
                recent_activities TEXT,
                conversation_topics TEXT,
                post_summaries TEXT,
                analysis_data TEXT,
                timestamp TEXT,
                status TEXT DEFAULT 'new',
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ Created new_leads table")
        return True

    except Exception as e:
        print(f"❌ Error creating leads table: {e}")
        return False


def save_test_lead(client_data):
    """Save a test lead to the database"""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Extract data
        username = client_data['username']
        hashtag = client_data['hashtag_found']
        score = client_data['coaching_score']
        reasons = json.dumps(client_data['coaching_reasons'])
        analysis = client_data['analysis']

        # Insert or update the lead
        cursor.execute('''
            INSERT OR REPLACE INTO new_leads 
            (username, hashtag_found, coaching_score, coaching_reasons,
             posts_analyzed, interests, lifestyle_indicators, recent_activities,
             conversation_topics, post_summaries, analysis_data, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            username,
            hashtag,
            score,
            reasons,
            analysis.get('posts_analyzed', 0),
            json.dumps(analysis.get('interests', [])),
            json.dumps(analysis.get('lifestyle_indicators', [])),
            json.dumps(analysis.get('recent_activities', [])),
            json.dumps(analysis.get('conversation_topics', [])),
            json.dumps(analysis.get('post_summaries', [])),
            json.dumps(analysis),
            client_data['timestamp']
        ))

        conn.commit()
        conn.close()
        print(f"✅ Saved test lead: {username}")
        return True

    except Exception as e:
        print(f"❌ Error saving test lead {username}: {e}")
        return False


def test_database_connection():
    """Test if we can connect to the database"""
    try:
        if not os.path.exists(SQLITE_DB_PATH):
            print(f"❌ Database file not found: {SQLITE_DB_PATH}")
            return False

        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()

        print(f"✅ Database connection successful")
        print(f"📊 Found {len(tables)} tables in database")
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def main():
    """Main test function"""
    print("🧪 Testing New Leads Database Integration")
    print("=" * 50)

    # Test database connection
    print("\n1. Testing database connection...")
    if not test_database_connection():
        return

    # Create table
    print("\n2. Creating leads table...")
    if not create_leads_table():
        return

    # Create and save test leads
    print("\n3. Creating test leads...")
    test_leads = create_test_leads()

    print(f"\n4. Saving {len(test_leads)} test leads...")
    saved_count = 0
    for lead in test_leads:
        if save_test_lead(lead):
            saved_count += 1

    print(f"\n✅ Successfully saved {saved_count}/{len(test_leads)} test leads")

    # Verify data was saved
    print("\n5. Verifying saved data...")
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM new_leads")
        count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT username, coaching_score FROM new_leads ORDER BY coaching_score DESC")
        leads = cursor.fetchall()

        conn.close()

        print(f"📊 Total leads in database: {count}")
        print("🏆 Top leads:")
        for username, score in leads:
            print(f"   • @{username} - {score}/100")

    except Exception as e:
        print(f"❌ Error verifying data: {e}")

    print("\n🎉 Test complete! You can now view the leads in the dashboard.")
    print("💡 Go to the 'New Leads' tab in your Streamlit dashboard to see the results.")


if __name__ == "__main__":
    main()
