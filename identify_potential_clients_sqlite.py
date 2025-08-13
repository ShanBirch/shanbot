import json
import os
import datetime
import google.generativeai as genai
from pathlib import Path
import re
import logging
import sqlite3
import sys

# Add the app directory to the path for imports
app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Import SQLite utilities
try:
    from dashboard_modules.dashboard_sqlite_utils import (
        get_db_connection,
        save_metrics_to_sqlite,
        load_conversations_from_sqlite
    )
except ImportError:
    print("Warning: Could not import SQLite utilities. Make sure dashboard_sqlite_utils.py is available.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SQLITE_DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"
GEMINI_API_KEY = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')


def analyze_for_coaching_potential(user_data):
    """
    Analyze a user's Instagram data to determine their potential as a vegetarian/vegan fitness coaching client.
    Returns a score from 0-100 and detailed reasoning.
    """
    try:
        # Handle both SQLite structure and direct analyze_followers.py output
        if 'metrics' in user_data:
            # SQLite structure
            metrics = user_data.get('metrics', {})
            client_analysis = metrics.get('client_analysis', {})
        else:
            # Direct analyze_followers.py output
            client_analysis = user_data

        if not client_analysis:
            return None

        interests = client_analysis.get('interests', [])
        lifestyle_indicators = client_analysis.get('lifestyle_indicators', [])
        recent_activities = client_analysis.get('recent_activities', [])
        post_summaries = client_analysis.get('post_summaries', [])
        conversation_topics = client_analysis.get('conversation_topics', [])
        profile_bio = client_analysis.get('profile_bio', {})

        # Create comprehensive prompt for analysis
        prompt = f"""
        Analyze this Instagram user's profile data to determine their potential as a client for a VEGETARIAN/VEGAN FITNESS COACHING program.

        USER DATA:
        Interests: {', '.join(interests) if interests else 'None listed'}
        Lifestyle Indicators: {', '.join(lifestyle_indicators) if lifestyle_indicators else 'None listed'}
        Recent Activities: {', '.join(recent_activities) if recent_activities else 'None listed'}
        Post Summaries: {' | '.join(post_summaries) if post_summaries else 'None available'}
        Profile Bio: {json.dumps(profile_bio) if profile_bio else 'None available'}

        SCORING CRITERIA (Rate 0-100):
        - Vegetarian/Vegan indicators (25 points): Plant-based food, vegan lifestyle, vegetarian mentions, animal rights, plant-based diet
        - Fitness/Health interest (25 points): Gym workouts, fitness goals, health consciousness, weight loss journey, already active in fitness
        - Target Demographics (30 points): MOTHERS/MUMS (15 pts), WEIGHT LOSS goals/journey (15 pts) - these are TOP priority clients
        - Lifestyle alignment (10 points): Wellness focus, healthy living, mindfulness, sustainability  
        - Engagement potential (10 points): Active social media presence, shares personal journey, asks questions, posts regularly

        RESPOND IN THIS EXACT FORMAT:
        SCORE: [0-100]
        VEGETARIAN_VEGAN_INDICATORS: [List specific evidence of plant-based lifestyle]
        FITNESS_HEALTH_INDICATORS: [List specific evidence of fitness/health interest]
        TARGET_DEMOGRAPHICS: [Evidence of being a MOTHER/MUM and/or having WEIGHT LOSS goals - these are priority clients]
        LIFESTYLE_ALIGNMENT: [List evidence of wellness/healthy lifestyle]
        ENGAGEMENT_POTENTIAL: [Assessment of how likely they are to engage with coaching]
        REASONING: [2-3 sentence explanation of the score, emphasizing mums and weight loss goals]
        CONVERSATION_STARTERS: [3 specific conversation starters tailored to this person]
        """

        response = model.generate_content(prompt)

        if response and response.text:
            return parse_coaching_analysis(response.text)
        else:
            logger.warning("No response from Gemini for coaching analysis")
            return None

    except Exception as e:
        logger.error(f"Error in analyze_for_coaching_potential: {e}")
        return None


def parse_coaching_analysis(response_text):
    """Parse the Gemini response into structured data"""
    try:
        analysis = {}

        # Extract score
        score_match = re.search(r'SCORE:\s*(\d+)', response_text)
        analysis['score'] = int(score_match.group(1)) if score_match else 0

        # Extract sections
        sections = {
            'vegetarian_vegan_indicators': r'VEGETARIAN_VEGAN_INDICATORS:\s*(.*?)(?=\n[A-Z_]+:|$)',
            'fitness_health_indicators': r'FITNESS_HEALTH_INDICATORS:\s*(.*?)(?=\n[A-Z_]+:|$)',
            'target_demographics': r'TARGET_DEMOGRAPHICS:\s*(.*?)(?=\n[A-Z_]+:|$)',
            'lifestyle_alignment': r'LIFESTYLE_ALIGNMENT:\s*(.*?)(?=\n[A-Z_]+:|$)',
            'engagement_potential': r'ENGAGEMENT_POTENTIAL:\s*(.*?)(?=\n[A-Z_]+:|$)',
            'reasoning': r'REASONING:\s*(.*?)(?=\n[A-Z_]+:|$)',
            'conversation_starters': r'CONVERSATION_STARTERS:\s*(.*?)(?=\n[A-Z_]+:|$)'
        }

        for key, pattern in sections.items():
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                content = match.group(1).strip()
                if key == 'conversation_starters':
                    # Split conversation starters into a list
                    starters = [s.strip()
                                for s in content.split('\n') if s.strip()]
                    analysis[key] = starters
                else:
                    analysis[key] = content
            else:
                analysis[key] = ""

        analysis['timestamp'] = datetime.datetime.now().isoformat()
        analysis['analysis_type'] = 'vegetarian_vegan_fitness_coaching'

        return analysis

    except Exception as e:
        logger.error(f"Error parsing coaching analysis: {e}")
        return None


def get_coaching_potential_category(score):
    """Categorize users based on their coaching potential score"""
    if score >= 80:
        return "🌟 Excellent Prospect"
    elif score >= 65:
        return "🔥 High Potential"
    elif score >= 50:
        return "⭐ Good Potential"
    elif score >= 35:
        return "💡 Some Potential"
    else:
        return "❌ Low Potential"


def analyze_all_followers_for_coaching_sqlite():
    """
    Analyze all followers in the SQLite database for coaching potential.
    Only analyzes users who don't already have coaching analysis.
    """
    try:
        # Load existing data from SQLite
        conversations = load_conversations_from_sqlite()

        if not conversations:
            logger.error("No conversations found in SQLite database")
            return False

        total_users = len(conversations)
        analyzed_count = 0
        updated_count = 0

        logger.info(
            f"Starting coaching potential analysis for {total_users} users...")

        for ig_username, user_data in conversations.items():
            try:
                metrics = user_data.get('metrics', {})
                client_analysis = metrics.get('client_analysis', {})

                # Check if user already has coaching analysis
                if client_analysis.get('coaching_potential'):
                    logger.info(
                        f"Skipping {ig_username} - already has coaching analysis")
                    continue

                # Only analyze users who have Instagram analysis
                if not client_analysis.get('interests') and not client_analysis.get('post_summaries'):
                    logger.info(
                        f"Skipping {ig_username} - no Instagram analysis available")
                    continue

                logger.info(
                    f"Analyzing coaching potential for {ig_username}...")

                # Perform coaching analysis
                coaching_analysis = analyze_for_coaching_potential(user_data)

                if coaching_analysis:
                    # Add coaching analysis to user data
                    if 'client_analysis' not in metrics:
                        metrics['client_analysis'] = {}

                    metrics['client_analysis']['coaching_potential'] = coaching_analysis

                    # Save updated metrics to SQLite
                    if save_metrics_to_sqlite(ig_username, metrics):
                        updated_count += 1
                        logger.info(
                            f"✅ Analyzed {ig_username} - Score: {coaching_analysis.get('score', 0)}")
                    else:
                        logger.error(
                            f"Failed to save coaching analysis for {ig_username}")
                else:
                    logger.warning(f"❌ Failed to analyze {ig_username}")

                analyzed_count += 1

                # Log progress every 10 users
                if analyzed_count % 10 == 0:
                    logger.info(
                        f"Progress: {analyzed_count}/{total_users} users processed")

            except Exception as e:
                logger.error(f"Error analyzing {ig_username}: {e}")
                continue

        logger.info(
            f"✅ Coaching analysis complete! Analyzed {analyzed_count} users, updated {updated_count} profiles")
        return True

    except Exception as e:
        logger.error(
            f"Error in analyze_all_followers_for_coaching_sqlite: {e}")
        return False


def get_high_potential_clients_sqlite(min_score=50):
    """
    Get all users with coaching potential score above the minimum threshold from SQLite.
    Returns sorted list by score (highest first).
    """
    try:
        conversations = load_conversations_from_sqlite()

        if not conversations:
            logger.error("No conversations found in SQLite database")
            return []

        high_potential_clients = []

        for ig_username, user_data in conversations.items():
            try:
                metrics = user_data.get('metrics', {})
                client_analysis = metrics.get('client_analysis', {})
                coaching_potential = client_analysis.get(
                    'coaching_potential', {})

                score = coaching_potential.get('score', 0)

                if score >= min_score:
                    client_info = {
                        'username': ig_username,
                        'score': score,
                        'category': get_coaching_potential_category(score),
                        'coaching_analysis': coaching_potential,
                        'profile_bio': client_analysis.get('profile_bio', {}),
                        'interests': client_analysis.get('interests', []),
                        'recent_activities': client_analysis.get('recent_activities', []),
                        'conversation_topics': client_analysis.get('conversation_topics', []),
                        'ig_username': ig_username,
                        'last_interaction': metrics.get('last_interaction_timestamp'),
                        'journey_stage': metrics.get('journey_stage', {}),
                        'subscriber_id': metrics.get('subscriber_id'),
                        'first_name': metrics.get('first_name'),
                        'last_name': metrics.get('last_name'),
                        'client_status': metrics.get('client_status')
                    }
                    high_potential_clients.append(client_info)

            except Exception as e:
                logger.error(
                    f"Error processing {ig_username} for high potential list: {e}")
                continue

        # Sort by score (highest first)
        high_potential_clients.sort(key=lambda x: x['score'], reverse=True)

        logger.info(
            f"Found {len(high_potential_clients)} high-potential clients (score >= {min_score})")
        return high_potential_clients

    except Exception as e:
        logger.error(f"Error in get_high_potential_clients_sqlite: {e}")
        return []


def generate_coaching_outreach_message(client_info):
    """Generate a personalized outreach message for a high-potential client"""
    try:
        coaching_analysis = client_info.get('coaching_analysis', {})
        interests = client_info.get('interests', [])

        prompt = f"""
        Create a personalized Instagram DM for reaching out to a potential vegetarian/vegan fitness coaching client.

        CLIENT INFO:
        Username: {client_info['username']}
        Coaching Score: {client_info['score']}/100
        Interests: {', '.join(interests)}
        Vegetarian/Vegan Indicators: {coaching_analysis.get('vegetarian_vegan_indicators', '')}
        Fitness Indicators: {coaching_analysis.get('fitness_health_indicators', '')}

        REQUIREMENTS:
        - Keep it under 150 words
        - Be genuine and personal, not salesy
        - Reference something specific from their profile
        - Mention your vegetarian fitness coaching
        - Include a soft call-to-action
        - Sound natural and friendly

        TONE: Friendly, supportive, authentic
        """

        response = model.generate_content(prompt)

        if response and response.text:
            return response.text.strip()
        else:
            return "Hi! I noticed your interest in plant-based living and fitness. I'm a vegetarian fitness coach and would love to connect with like-minded people. Would you be interested in chatting about your fitness journey?"

    except Exception as e:
        logger.error(f"Error generating outreach message: {e}")
        return "Hi! I noticed your interest in plant-based living and fitness. I'm a vegetarian fitness coach and would love to connect with like-minded people. Would you be interested in chatting about your fitness journey?"


def add_follower_to_database(ig_username, follower_data=None):
    """
    Add a follower to the SQLite database.
    follower_data should be the analysis result from analyze_followers.py
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute(
            "SELECT ig_username FROM users WHERE ig_username = ?", (ig_username,))
        if cursor.fetchone():
            logger.info(f"User {ig_username} already exists in database")
            return True

        # Prepare data
        if follower_data is None:
            follower_data = {}

        # Create metrics data with coaching analysis
        metrics_data = {
            'ig_username': ig_username,
            'client_analysis': follower_data,
            'last_updated': datetime.datetime.now().isoformat()
        }

        # Insert new follower using only existing columns
        cursor.execute("""
            INSERT INTO users (
                ig_username, 
                client_status,
                metrics_json
            ) VALUES (?, ?, ?)
        """, (
            ig_username,
            'follower',  # Default status for new followers
            json.dumps(metrics_data)
        ))

        conn.commit()
        conn.close()

        logger.info(
            f"Added follower {ig_username} to database with coaching analysis")
        return True

    except Exception as e:
        logger.error(f"Error adding follower {ig_username} to database: {e}")
        return False


def import_followers_from_file(file_path):
    """
    Import followers from a text file (like Instagram_followers.txt) into the SQLite database.
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"Followers file not found: {file_path}")
            return False

        with open(file_path, 'r', encoding='utf-8') as f:
            followers = [line.strip() for line in f if line.strip()]

        logger.info(f"Found {len(followers)} followers in file")

        added_count = 0
        for follower in followers:
            if add_follower_to_database(follower):
                added_count += 1

            # Log progress every 100 followers
            if added_count % 100 == 0:
                logger.info(f"Imported {added_count} followers...")

        logger.info(
            f"✅ Import complete! Added {added_count} new followers to database")
        return True

    except Exception as e:
        logger.error(f"Error importing followers from file: {e}")
        return False


def get_all_followers_from_database():
    """
    Get all followers from the SQLite database with their analysis status.
    """
    try:
        conversations = load_conversations_from_sqlite()

        followers = []
        for ig_username, user_data in conversations.items():
            metrics = user_data.get('metrics', {})
            client_analysis = metrics.get('client_analysis', {})

            follower_info = {
                'ig_username': ig_username,
                'first_name': metrics.get('first_name', ''),
                'last_name': metrics.get('last_name', ''),
                'client_status': metrics.get('client_status', 'unknown'),
                'has_instagram_analysis': bool(client_analysis.get('interests') or client_analysis.get('post_summaries')),
                'has_coaching_analysis': bool(client_analysis.get('coaching_potential')),
                'coaching_score': client_analysis.get('coaching_potential', {}).get('score', 0),
                'last_interaction': metrics.get('last_interaction_timestamp'),
                'joined_date': metrics.get('joined_date'),
                'total_messages': metrics.get('total_messages', 0)
            }
            followers.append(follower_info)

        # Sort by coaching score (highest first), then by username
        followers.sort(key=lambda x: (
            x['coaching_score'], x['ig_username']), reverse=True)

        return followers

    except Exception as e:
        logger.error(f"Error getting followers from database: {e}")
        return []


if __name__ == "__main__":
    print("🌱 Starting Vegetarian/Vegan Fitness Coaching Potential Analysis (SQLite)...")

    # Run the analysis
    success = analyze_all_followers_for_coaching_sqlite()

    if success:
        print("\n✅ Analysis complete!")

        # Show summary of high-potential clients
        high_potential = get_high_potential_clients_sqlite(min_score=65)
        print(
            f"\n🌟 Found {len(high_potential)} high-potential clients (score >= 65):")

        for client in high_potential[:10]:  # Show top 10
            print(
                f"  • {client['username']}: {client['score']}/100 - {client['category']}")

        if len(high_potential) > 10:
            print(f"  ... and {len(high_potential) - 10} more")

    else:
        print("❌ Analysis failed. Check the logs for details.")
