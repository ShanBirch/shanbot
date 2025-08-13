import json
import os
import datetime
import google.generativeai as genai
from pathlib import Path
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ANALYTICS_FILE = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"
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
        # Extract relevant data
        client_analysis = user_data.get(
            'metrics', {}).get('client_analysis', {})
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
        - Vegetarian/Vegan indicators (25 points): Plant-based food, vegan lifestyle, vegetarian mentions, animal rights
        - Fitness/Health interest (25 points): Gym, workouts, fitness goals, health consciousness, weight loss
        - Lifestyle alignment (20 points): Wellness focus, healthy living, mindfulness, sustainability
        - Engagement potential (15 points): Active social media presence, shares personal journey, asks questions
        - Demographic fit (15 points): Age indicators, lifestyle stage, disposable income indicators

        RESPOND IN THIS EXACT FORMAT:
        SCORE: [0-100]
        VEGETARIAN_VEGAN_INDICATORS: [List specific evidence of plant-based lifestyle]
        FITNESS_HEALTH_INDICATORS: [List specific evidence of fitness/health interest]
        LIFESTYLE_ALIGNMENT: [List evidence of wellness/healthy lifestyle]
        ENGAGEMENT_POTENTIAL: [Assessment of how likely they are to engage with coaching]
        DEMOGRAPHIC_FIT: [Assessment of demographic alignment]
        REASONING: [2-3 sentence explanation of the score]
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
            'lifestyle_alignment': r'LIFESTYLE_ALIGNMENT:\s*(.*?)(?=\n[A-Z_]+:|$)',
            'engagement_potential': r'ENGAGEMENT_POTENTIAL:\s*(.*?)(?=\n[A-Z_]+:|$)',
            'demographic_fit': r'DEMOGRAPHIC_FIT:\s*(.*?)(?=\n[A-Z_]+:|$)',
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


def analyze_all_followers_for_coaching():
    """
    Analyze all followers in the analytics file for coaching potential.
    Only analyzes users who don't already have coaching analysis.
    """
    try:
        # Load existing analytics data
        if not os.path.exists(ANALYTICS_FILE):
            logger.error(f"Analytics file not found: {ANALYTICS_FILE}")
            return False

        with open(ANALYTICS_FILE, 'r', encoding='utf-8') as f:
            analytics_data = json.load(f)

        conversations = analytics_data.get('conversations', {})
        total_users = len(conversations)
        analyzed_count = 0
        updated_count = 0

        logger.info(
            f"Starting coaching potential analysis for {total_users} users...")

        for username, user_data in conversations.items():
            try:
                # Check if user already has coaching analysis
                metrics = user_data.get('metrics', {})
                client_analysis = metrics.get('client_analysis', {})

                if client_analysis.get('coaching_potential'):
                    logger.info(
                        f"Skipping {username} - already has coaching analysis")
                    continue

                # Only analyze users who have Instagram analysis
                if not client_analysis.get('interests') and not client_analysis.get('post_summaries'):
                    logger.info(
                        f"Skipping {username} - no Instagram analysis available")
                    continue

                logger.info(f"Analyzing coaching potential for {username}...")

                # Perform coaching analysis
                coaching_analysis = analyze_for_coaching_potential(user_data)

                if coaching_analysis:
                    # Add coaching analysis to user data
                    if 'client_analysis' not in metrics:
                        metrics['client_analysis'] = {}

                    metrics['client_analysis']['coaching_potential'] = coaching_analysis
                    updated_count += 1

                    logger.info(
                        f"✅ Analyzed {username} - Score: {coaching_analysis.get('score', 0)}")
                else:
                    logger.warning(f"❌ Failed to analyze {username}")

                analyzed_count += 1

                # Save progress every 10 users
                if analyzed_count % 10 == 0:
                    logger.info(
                        f"Saving progress... ({analyzed_count}/{total_users})")
                    with open(ANALYTICS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(analytics_data, f, indent=2,
                                  ensure_ascii=False)

            except Exception as e:
                logger.error(f"Error analyzing {username}: {e}")
                continue

        # Final save
        with open(ANALYTICS_FILE, 'w', encoding='utf-8') as f:
            json.dump(analytics_data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"✅ Coaching analysis complete! Analyzed {analyzed_count} users, updated {updated_count} profiles")
        return True

    except Exception as e:
        logger.error(f"Error in analyze_all_followers_for_coaching: {e}")
        return False


def get_high_potential_clients(min_score=50):
    """
    Get all users with coaching potential score above the minimum threshold.
    Returns sorted list by score (highest first).
    """
    try:
        if not os.path.exists(ANALYTICS_FILE):
            logger.error(f"Analytics file not found: {ANALYTICS_FILE}")
            return []

        with open(ANALYTICS_FILE, 'r', encoding='utf-8') as f:
            analytics_data = json.load(f)

        high_potential_clients = []
        conversations = analytics_data.get('conversations', {})

        for username, user_data in conversations.items():
            try:
                metrics = user_data.get('metrics', {})
                client_analysis = metrics.get('client_analysis', {})
                coaching_potential = client_analysis.get(
                    'coaching_potential', {})

                score = coaching_potential.get('score', 0)

                if score >= min_score:
                    client_info = {
                        'username': username,
                        'score': score,
                        'category': get_coaching_potential_category(score),
                        'coaching_analysis': coaching_potential,
                        'profile_bio': client_analysis.get('profile_bio', {}),
                        'interests': client_analysis.get('interests', []),
                        'recent_activities': client_analysis.get('recent_activities', []),
                        'conversation_topics': client_analysis.get('conversation_topics', []),
                        'ig_username': metrics.get('ig_username', username),
                        'last_interaction': metrics.get('last_interaction_date'),
                        'journey_stage': metrics.get('journey_stage', {})
                    }
                    high_potential_clients.append(client_info)

            except Exception as e:
                logger.error(
                    f"Error processing {username} for high potential list: {e}")
                continue

        # Sort by score (highest first)
        high_potential_clients.sort(key=lambda x: x['score'], reverse=True)

        logger.info(
            f"Found {len(high_potential_clients)} high-potential clients (score >= {min_score})")
        return high_potential_clients

    except Exception as e:
        logger.error(f"Error in get_high_potential_clients: {e}")
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


if __name__ == "__main__":
    print("🌱 Starting Vegetarian/Vegan Fitness Coaching Potential Analysis...")

    # Run the analysis
    success = analyze_all_followers_for_coaching()

    if success:
        print("\n✅ Analysis complete!")

        # Show summary of high-potential clients
        high_potential = get_high_potential_clients(min_score=65)
        print(
            f"\n🌟 Found {len(high_potential)} high-potential clients (score >= 65):")

        for client in high_potential[:10]:  # Show top 10
            print(
                f"  • {client['username']}: {client['score']}/100 - {client['category']}")

        if len(high_potential) > 10:
            print(f"  ... and {len(high_potential) - 10} more")

    else:
        print("❌ Analysis failed. Check the logs for details.")
