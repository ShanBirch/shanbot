import streamlit as st
import json
import logging
import os
from pathlib import Path
import datetime
import google.generativeai as genai
import random
import google.oauth2.service_account
import googleapiclient.discovery

# Use absolute imports
from app.dashboard_modules.overview import display_overview
from app.dashboard_modules.client_journey import display_client_journey
from app.dashboard_modules.user_profiles import display_user_profiles
from app.dashboard_modules.scheduled_followups import (
    display_scheduled_followups,
    display_bulk_review_and_send,
    bulk_generate_followups,
    get_user_category,
    get_topic_for_category,
    verify_trial_signup,
    check_sheet_for_signups,
)

# Update file paths to be relative to this file
ANALYTICS_FILE = os.path.join(os.path.dirname(
    __file__), "analytics_data_good.json")
SHEETS_CREDENTIALS_PATH = os.path.join(
    os.path.dirname(__file__), "sheets_credentials.json")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Sheets configuration
ONBOARDING_SPREADSHEET_ID = "1038Ep0lYGEtpipNAIzH7RB67-KOAfXA-TcUTKBKqIfo"
ONBOARDING_RANGE_NAME = "Sheet1!A:AAF"


def check_and_update_signups(data: dict) -> dict:
    """Check for new signups and update user stages accordingly."""
    data_updated = False

    for username, user_data in data.get('conversations', {}).items():
        metrics = user_data.get('metrics', {})
        ig_username = metrics.get('ig_username')

        # Skip if already in trial or paying stage
        if metrics.get('is_paying_client') or any(metrics.get(f'trial_week_{i}') for i in range(1, 5)):
            continue

        # Check if user has signed up
        if ig_username and verify_trial_signup(ig_username):
            logger.info(
                f"Found signup for {ig_username}, updating to Trial Week 1")
            metrics['trial_week_1'] = True
            data['conversations'][username]['metrics'] = metrics
            data_updated = True

    return data, data_updated


def load_analytics_data():
    """Load analytics data"""
    try:
        # Use the full absolute path
        analytics_file = ANALYTICS_FILE
        logger.info(f"Attempting to load from: {analytics_file}")

        with open(analytics_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info("Data loaded successfully")

        return data, analytics_file
    except Exception as e:
        logger.error(f"Error loading analytics data: {e}")
        st.error(f"Error loading analytics data: {e}")
        return {}, None


# Configure Gemini
GEMINI_API_KEY = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# Add a session state for message queue
if 'message_queue' not in st.session_state:
    st.session_state.message_queue = []

# Add session state for last signup check
if 'last_signup_check' not in st.session_state:
    st.session_state.last_signup_check = None


def get_response_category_color(num_responses):
    """Return color and emoji indicator based on number of responses"""
    if num_responses >= 20:
        return "🟢"  # Green circle for high responders
    elif num_responses >= 11:
        return "🟡"  # Yellow circle for medium responders
    elif num_responses >= 1:
        return "🟠"  # Orange circle for low responders
    else:
        return "🔴"  # Red circle for no response


def get_usernames(data):
    """Extract unique usernames from analytics data with response categorization"""
    try:
        # Get the conversations dictionary
        conversations = data.get('conversations', {})

        # Create a list of tuples with (username, category)
        categorized_users = []

        for username, user_data in conversations.items():
            # Get number of user messages
            num_responses = user_data.get(
                'metrics', {}).get('user_messages', 0)
            category_color = get_response_category_color(num_responses)
            categorized_users.append((username, category_color, num_responses))

        # Sort by number of responses in descending order
        categorized_users.sort(key=lambda x: (-x[2]))

        logger.info(f"Found {len(categorized_users)} categorized users")
        return categorized_users
    except Exception as e:
        logger.error(f"Error extracting usernames: {e}")
        st.error(f"Error extracting usernames: {e}")
        return []


def generate_follow_up_message(conversation_history, topic):
    """Generate a follow-up message using Gemini"""
    try:
        # Format conversation history
        formatted_history = ""
        for msg in conversation_history:
            sender = "User" if msg.get('type') == 'user' else "Shannon"
            formatted_history += f"{sender}: {msg.get('text', '')}\n"

        prompt = f"""
        Previous conversation history:
        {formatted_history}

        Current conversation topic to discuss:
        {topic}

        Create a casual, friendly opener message to restart the conversation about this topic.
        Keep it simple and engaging, like this example:
        Topic: Discuss their favorite plant-based protein sources
        Message: "yo dam im running dry on protein sources for a veggie diet, whats your diet looking like? any high protein secrets for me? :)"

        Rules:
        - Don't use their Instagram username
        - Keep it casual and conversational
        - Make it feel natural and not scripted
        - Include a question to encourage response
        - Keep it short (1-2 sentences max)
        - Don't reference previous conversations directly

        Generate ONLY the message, no other text:
        """

        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error generating message: {e}")
        return None


def get_stage_topics(stage_number):
    """Get conversation topics for a specific stage"""
    stage_topics = {
        1: ["Topic 1 - Discuss their favorite plant-based protein sources for muscle growth and any creative vegetarian recipes they've discovered recently."],
        2: ["Topic 2 - Explore their approach to tracking progress with clients, specifically what metrics they prioritize beyond just weight loss and how they use fitness apps."],
        3: ["Topic 3 - Talk about their experience adapting resistance training techniques for clients with different fitness levels and what common mistakes they see people make."],
        4: ["Topic 4 - Share tips on incorporating high-protein vegetarian meals into a busy schedule and how they advise clients to make healthy eating more convenient in Melbourne."],
        5: ["Topic 5 - Enquire about leads fitness journey - offer 1 month trial"],
        6: ["Trial Week 1 - Monday Morning: Goooooood Morning! Ready for the week?",
            "Trial Week 1 - Wednesday Night: Heya! Hows your week going?"],
        7: ["Trial Week 2 - Monday Morning: Goooooood Morning! Ready for the week?",
            "Trial Week 2 - Wednesday Night: Heya! Hows your week going?"],
        8: ["Trial Week 3 - Monday Morning: Goooooood Morning! Ready for the week?",
            "Trial Week 3 - Wednesday Night: Heya! Hows your week going?"],
        9: ["Trial Week 4 - Monday Morning: Goooooood Morning! Ready for the week?",
            "Trial Week 4 - Wednesday Night: Heya! Hows your week going?"],
        10: ["Paying Client - Monday Morning: Goooooood Morning! Ready for the week?",
             "Paying Client - Wednesday Night: Heya! Hows your week going?"]
    }
    return stage_topics.get(stage_number, [])


def display_user_profile(username, user_data):
    """Display user profile information"""
    try:
        # Get client analysis data
        client_analysis = user_data.get(
            'metrics', {}).get('client_analysis', {})

        # Determine client journey stage
        journey_stage = "Topic 1"  # Default stage
        stage_number = 1
        metrics = user_data.get('metrics', {})

        # Check for journey stage indicators
        if metrics.get('is_paying_client'):
            journey_stage = "Paying Client"
            stage_number = 10
        elif metrics.get('trial_week_4'):
            journey_stage = "Trial Week 4"
            stage_number = 9
        elif metrics.get('trial_week_3'):
            journey_stage = "Trial Week 3"
            stage_number = 8
        elif metrics.get('trial_week_2'):
            journey_stage = "Trial Week 2"
            stage_number = 7
        elif metrics.get('trial_week_1'):
            journey_stage = "Trial Week 1"
            stage_number = 6
        elif metrics.get('trial_offer_made'):
            journey_stage = "Topic 5 (Health/Fitness + Trial Offer)"
            stage_number = 5
        elif metrics.get('topic4_completed'):
            journey_stage = "Topic 4"
            stage_number = 4
        elif metrics.get('topic3_completed'):
            journey_stage = "Topic 3"
            stage_number = 3
        elif metrics.get('topic2_completed'):
            journey_stage = "Topic 2"
            stage_number = 2

        # Create tabs for different sections of the profile
        profile_tab, analysis_tab, conversation_tab, history_tab = st.tabs([
            "📋 Profile", "📊 Analysis", "💭 Conversation Topics", "📝 History"
        ])

        with profile_tab:
            # Display client journey stage prominently
            st.info(f"**Current Journey Stage:** {journey_stage}")

            # Display profile bio if available
            if client_analysis and 'profile_bio' in client_analysis:
                bio = client_analysis['profile_bio']

                # Create columns for bio information
                bio_col1, bio_col2 = st.columns(2)

                with bio_col1:
                    if 'PERSON NAME' in bio:
                        st.info(f"**Name:** {bio['PERSON NAME']}")

                    if 'INTERESTS' in bio and bio['INTERESTS']:
                        st.write("**🎯 Key Interests:**")
                        for interest in bio['INTERESTS']:
                            st.write(f"- {interest}")

                with bio_col2:
                    if 'PERSONALITY TRAITS' in bio and bio['PERSONALITY TRAITS']:
                        st.write("**👤 Personality Traits:**")
                        for trait in bio['PERSONALITY TRAITS']:
                            st.write(f"- {trait}")

                if 'LIFESTYLE' in bio and bio['LIFESTYLE']:
                    st.write("**🌟 Lifestyle:**")
                    st.info(bio['LIFESTYLE'])

        with conversation_tab:
            st.subheader("🗣️ Conversation Topics")

            # Display current stage
            st.write(f"**Current Stage:** {journey_stage}")

            # Display conversation topics
            if 'conversation_topics' in client_analysis:
                topics = client_analysis['conversation_topics']
                if topics:
                    for topic in topics:
                        if topic and not topic.startswith('**'):
                            st.info(topic)
                else:
                    st.warning("No conversation topics available yet.")

        with analysis_tab:
            st.subheader("📸 Instagram Analysis")

            # Create columns for Instagram metrics
            insta_col1, insta_col2 = st.columns(2)

            with insta_col1:
                if 'posts_analyzed' in client_analysis:
                    st.metric("Posts Analyzed", client_analysis.get(
                        'posts_analyzed', 0))

                if 'interests' in client_analysis:
                    st.write("**Detected Interests:**")
                    interests = [i for i in client_analysis.get(
                        'interests', []) if i and not i.startswith('**')]
                    for interest in interests:
                        st.write(f"- {interest}")

            with insta_col2:
                if 'recent_activities' in client_analysis:
                    st.write("**Recent Activities:**")
                    activities = [a for a in client_analysis.get(
                        'recent_activities', []) if a and not a.startswith('**')]
                    for activity in activities:
                        st.write(f"- {activity}")

            # Display Post Summaries if available
            if 'post_summaries' in client_analysis and client_analysis['post_summaries']:
                with st.expander("📝 Post Summaries"):
                    for i, summary in enumerate(client_analysis['post_summaries'], 1):
                        if summary and not summary.startswith('**'):
                            st.write(f"**Post {i}:**")
                            st.write(summary)
                            st.write("---")

        with history_tab:
            st.subheader("💬 Conversation History")
            conversation_history = user_data.get(
                'metrics', {}).get('conversation_history', [])

            if conversation_history:
                for message in conversation_history:
                    with st.container():
                        # Format timestamp
                        timestamp = message.get('timestamp', '').split('T')[
                            0]  # Just get the date part

                        # Different styling for user vs AI messages
                        if message.get('type') == 'user':
                            st.markdown(f"**User** ({timestamp}):")
                            st.markdown(f">{message.get('text', '')}")
                        else:
                            st.markdown(f"**Shannon** ({timestamp}):")
                            st.markdown(f">{message.get('text', '')}")
                        st.markdown("---")
            else:
                st.write("No conversation history available.")

    except Exception as e:
        logger.error(f"Error displaying user profile: {e}")
        st.error(f"Error displaying user profile: {e}")


def get_stage_metrics(data):
    """Calculate metrics for each stage of the client journey"""
    try:
        conversations = data.get('conversations', {})
        metrics = {
            'total_users': len(conversations),
            'engaged_users': 0,
            'analyzed_profiles': 0,
            'total_messages': 0,
            'response_rate': 0,
            'avg_messages': 0
        }

        analyzed_users = 0
        total_analyzed_posts = 0

        for username, user_data in conversations.items():
            user_metrics = user_data.get('metrics', {})
            client_analysis = user_metrics.get('client_analysis', {})

            # Count analyzed profiles
            if client_analysis and client_analysis.get('posts_analyzed', 0) > 0:
                analyzed_users += 1
                total_analyzed_posts += client_analysis.get(
                    'posts_analyzed', 0)

            # Count engaged users (those with responses)
            if user_metrics.get('user_messages', 0) > 0:
                metrics['engaged_users'] += 1
                metrics['total_messages'] += user_metrics.get(
                    'total_messages', 0)

        # Calculate averages
        if metrics['engaged_users'] > 0:
            metrics['avg_messages'] = metrics['total_messages'] / \
                metrics['engaged_users']
            metrics['response_rate'] = (
                metrics['engaged_users'] / metrics['total_users']) * 100

        metrics['analyzed_profiles'] = analyzed_users
        metrics['avg_posts_per_profile'] = total_analyzed_posts / \
            analyzed_users if analyzed_users > 0 else 0

        return metrics
    except Exception as e:
        logger.error(f"Error calculating stage metrics: {e}")
        return metrics


def get_response_level_wait_time(num_responses):
    """Return wait time in days based on response level"""
    if num_responses >= 20:  # High responder (green)
        return 2  # 48 hours
    elif num_responses >= 11:  # Medium responder (yellow)
        return 5  # 5 days
    else:  # Low responder (orange/red)
        return 7  # 7 days


def get_users_ready_for_followup(analytics_data):
    """Determine which users are ready for follow-up based on their response level"""
    ready_for_followup = {
        'high_responders': [],
        'medium_responders': [],
        'low_responders': [],
        'total_count': 0
    }

    current_time = datetime.datetime.now()

    conversations = analytics_data.get('conversations', {})
    for username, user_data in conversations.items():
        metrics = user_data.get('metrics', {})

        # Get last message timestamp
        conversation_history = metrics.get('conversation_history', [])
        last_message_time = None
        if conversation_history:
            try:
                last_message = conversation_history[-1]
                last_message_time = datetime.datetime.fromisoformat(
                    last_message.get('timestamp', '').split('+')[0])
            except (IndexError, ValueError, AttributeError):
                continue

        # If no message history, use profile analysis time
        if not last_message_time and 'client_analysis' in metrics:
            try:
                last_message_time = datetime.datetime.fromisoformat(
                    metrics['client_analysis'].get('timestamp', '').split('+')[0])
            except (ValueError, AttributeError):
                continue

        if not last_message_time:
            continue

        # Get number of user messages
        num_responses = metrics.get('user_messages', 0)
        wait_days = get_response_level_wait_time(num_responses)

        # Calculate if enough time has passed
        time_since_last_message = current_time - last_message_time
        if time_since_last_message.days >= wait_days:
            user_info = {
                'username': username,
                'days_since_last_message': time_since_last_message.days,
                'response_count': num_responses,
                'last_message_time': last_message_time
            }

            if num_responses >= 20:
                ready_for_followup['high_responders'].append(user_info)
            elif num_responses >= 11:
                ready_for_followup['medium_responders'].append(user_info)
            else:
                ready_for_followup['low_responders'].append(user_info)

            ready_for_followup['total_count'] += 1

    return ready_for_followup


def get_user_topics(user_data):
    """Get conversation topics from user's analytics data"""
    try:
        client_analysis = user_data.get(
            'metrics', {}).get('client_analysis', {})
        topics = client_analysis.get('conversation_topics', [])
        # Filter out any empty or None topics
        return [topic for topic in topics if topic and not topic.startswith('**')]
    except Exception:
        return []


def queue_message_for_followup(username, message, topic):
    """Add a message to the follow-up queue"""
    st.session_state.message_queue.append({
        'username': username,
        'message': message,
        'topic': topic,
        'queued_time': datetime.datetime.now().isoformat()
    })


def save_followup_queue():
    """Save the follow-up queue to a file for the follow-up manager"""
    queue_file = os.path.join(os.path.dirname(
        ANALYTICS_FILE), "followup_queue.json")
    try:
        with open(queue_file, 'w') as f:
            json.dump({
                'messages': st.session_state.message_queue,
                'created_at': datetime.datetime.now().isoformat()
            }, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving follow-up queue: {e}")
        return False


def display_user_followup(user):
    """Display user follow-up information with message generation and sending capabilities"""
    username = user['username']
    user_data = st.session_state.analytics_data['conversations'][username]
    metrics = user_data.get('metrics', {})

    with st.expander(f"{user['username']} - {user['days_since_last_message']} days since last message"):
        # Create columns for layout
        info_col, history_col = st.columns([1, 1])

        with info_col:
            # Basic Information
            st.write("### User Information")
            st.write(f"**Response count:** {user['response_count']}")
            st.write(
                f"**Last message:** {user['last_message_time'].strftime('%Y-%m-%d %H:%M')}")

            # Get user's conversation topics
            available_topics = get_user_topics(user_data)

            if not available_topics:
                st.warning("No conversation topics available for this user")
            else:
                # Get user's category and appropriate topic
                user_category = get_user_category(user_data)
                current_topic = get_topic_for_category(
                    user_category, user_data)

                # Show current topic
                st.write("### Current Topic")
                st.info(current_topic)

                if st.button(f"Generate Message", key=f"gen_{username}"):
                    with st.spinner("Generating message..."):
                        conversation_history = metrics.get(
                            'conversation_history', [])
                        topic = current_topic
                        message = generate_follow_up_message(
                            conversation_history, topic)
                        user['generated_message'] = message
                        user['selected_topic'] = topic
                        st.success("Message generated!")

        with history_col:
            # Conversation History
            st.write("### Conversation History")
            conversation_history = metrics.get('conversation_history', [])
            if conversation_history:
                st.write("Last 5 messages:")
                history_container = st.container()
                with history_container:
                    for msg in conversation_history[-5:]:
                        sender = "User" if msg.get(
                            'type') == 'user' else "Shannon"
                        st.write(f"**{sender}:** {msg.get('text', '')}")
            else:
                st.info("No conversation history available")

        # Message editing section - full width below columns
        st.write("### Follow-up Message")
        if 'generated_message' in user:
            # Create a text area for editing the message
            edited_message = st.text_area(
                "Edit message if needed:",
                value=user['generated_message'],
                key=f"edit_{username}",
                height=100
            )

            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                # Add a regenerate button
                if st.button("Regenerate", key=f"regen_{username}"):
                    with st.spinner("Regenerating message..."):
                        conversation_history = metrics.get(
                            'conversation_history', [])
                        message = generate_follow_up_message(
                            conversation_history, current_topic)
                        user['generated_message'] = message
                        user['selected_topic'] = current_topic
                        st.success("Message regenerated!")

            with col2:
                # Add queue message button
                if st.button("Queue Message", key=f"queue_{username}"):
                    queue_message_for_followup(
                        username, edited_message, current_topic)
                    st.success(f"Message queued for {username}")

            # Update the stored message if edited
            if edited_message != user['generated_message']:
                user['generated_message'] = edited_message
                st.success("Message updated!")
        else:
            st.warning("Click 'Generate Message' to create a message")


def display_scheduled_followups(analytics_data, analytics_file):
    """Display the scheduled follow-ups section"""
    st.header("📅 Scheduled Follow-ups")

    # Get users ready for follow-up
    followup_data = get_users_ready_for_followup(analytics_data)

    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Ready for Follow-up", followup_data['total_count'])

    with col2:
        high_count = len(followup_data['high_responders'])
        st.metric("High Responders Ready (48h)", high_count)

    with col3:
        medium_count = len(followup_data['medium_responders'])
        st.metric("Medium Responders Ready (5d)", medium_count)

    with col4:
        low_count = len(followup_data['low_responders'])
        st.metric("Low Responders Ready (7d)", low_count)

    # Display queued messages if any exist
    if st.session_state.message_queue:
        st.subheader("📬 Queued Messages")
        st.write(
            f"{len(st.session_state.message_queue)} messages queued for sending")

        # Show queued messages in an expander
        with st.expander("View Queued Messages"):
            for msg in st.session_state.message_queue:
                st.write(f"**To:** {msg['username']}")
                st.write(f"**Topic:** {msg['topic']}")
                st.write(f"**Message:** {msg['message']}")
                st.write("---")

        # Add send button
        if st.button("🚀 Send All Queued Messages", type="primary"):
            if save_followup_queue():
                st.success(
                    "Messages queued for sending! Follow-up manager will process these messages.")
                # Clear the queue after successful save
                st.session_state.message_queue = []
            else:
                st.error("Failed to queue messages for sending")

    # Create tabs for different response levels
    high_tab, medium_tab, low_tab = st.tabs([
        "🟢 High Responders",
        "🟡 Medium Responders",
        "🟠 Low Responders"
    ])

    # Display users with their generated messages
    with high_tab:
        if followup_data['high_responders']:
            for user in followup_data['high_responders']:
                display_user_followup(user)
        else:
            st.info("No high responders ready for follow-up")

    with medium_tab:
        if followup_data['medium_responders']:
            for user in followup_data['medium_responders']:
                display_user_followup(user)
        else:
            st.info("No medium responders ready for follow-up")

    with low_tab:
        if followup_data['low_responders']:
            for user in followup_data['low_responders']:
                display_user_followup(user)
        else:
            st.info("No low responders ready for follow-up")


def display_overview():
    """Display the overview page"""
    st.header("📊 Overview")

    # Add signup check button and last check time
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🔍 Check New Signups", type="primary"):
            with st.spinner("Checking for new signups..."):
                updated_data, signups_found = check_sheet_for_signups(
                    st.session_state.analytics_data)
                if signups_found:
                    if save_analytics_data(updated_data, st.session_state.analytics_file):
                        st.success("Found and updated new trial signups!")
                        st.session_state.analytics_data = updated_data
                    else:
                        st.error("Failed to save signup updates")
                else:
                    st.info("No new signups found")
                st.session_state.last_signup_check = datetime.datetime.now()

    with col2:
        if st.session_state.last_signup_check:
            st.info(
                f"Last signup check: {st.session_state.last_signup_check.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.info("No recent signup checks")

    # Display metrics and other overview content
    metrics = get_stage_metrics(st.session_state.analytics_data)

    # Create columns for metrics display
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Users", metrics['total_users'])
        st.metric("Engaged Users", metrics['engaged_users'])

    with col2:
        st.metric("Total Messages", metrics['total_messages'])
        st.metric("Avg Messages per User", f"{metrics['avg_messages']:.1f}")

    with col3:
        st.metric("Response Rate", f"{metrics['response_rate']:.1f}%")
        st.metric("Analyzed Profiles", metrics['analyzed_profiles'])


def bulk_update_user_profiles(data: dict) -> tuple[dict, int]:
    """
    Bulk update all user profiles in analytics_data_good.json
    Returns: (updated_data, number_of_users_updated)
    """
    try:
        updated_count = 0
        conversations = data.get('conversations', {})

        for username, user_data in conversations.items():
            metrics = user_data.get('metrics', {})

            # Skip if user already has complete profile data
            if metrics.get('profile_complete'):
                continue

            # Get Instagram username
            ig_username = metrics.get('ig_username')
            if not ig_username:
                continue

            try:
                # Get user data from sheets
                sheet_data = get_checkin_data(ig_username)
                if sheet_data:
                    # Update metrics with sheet data
                    metrics.update({
                        'first_name': sheet_data.get('First Name', ''),
                        'last_name': sheet_data.get('Last Name', ''),
                        'gender': sheet_data.get('Gender', ''),
                        'weight': sheet_data.get('Weight', ''),
                        'height': sheet_data.get('Height', ''),
                        'goals': sheet_data.get('Long Term Goals', ''),
                        'dietary_requirements': sheet_data.get('Dietary Requirements', ''),
                        'dob': sheet_data.get('Date of Birth', ''),
                        'gym_access': sheet_data.get('Gym Access', ''),
                        'training_frequency': sheet_data.get('Training Frequency', ''),
                        'exercises_enjoyed': sheet_data.get('Exercises Enjoyed', ''),
                        'daily_calories': sheet_data.get('Daily Calories', ''),
                        'profile_complete': True,
                        'last_updated': datetime.datetime.now().isoformat()
                    })

                    # Update the user data in the main structure
                    data['conversations'][username]['metrics'] = metrics
                    updated_count += 1

            except Exception as e:
                logger.error(f"Error updating user {ig_username}: {e}")
                continue

        return data, updated_count

    except Exception as e:
        logger.error(f"Error in bulk update: {e}")
        return data, 0


def save_analytics_data(data: dict, file_path: str) -> bool:
    """Save analytics data to file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving analytics data: {e}")
        return False


def display_user_profiles(analytics_data):
    """Display user profiles section with bulk update button"""
    st.header("👥 User Profiles")

    # Add bulk update button at the top
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Bulk Update All Profiles", type="primary"):
            with st.spinner("Updating all user profiles..."):
                updated_data, update_count = bulk_update_user_profiles(
                    analytics_data)
                if update_count > 0:
                    if save_analytics_data(updated_data, st.session_state.analytics_file):
                        st.success(
                            f"Successfully updated {update_count} user profiles!")
                        st.session_state.analytics_data = updated_data
                    else:
                        st.error("Failed to save updates to analytics file")
                else:
                    st.info("No profiles needed updating")

    with col2:
        st.info(
            "This will update all user profiles with the latest data from the Google Sheet")

    # Continue with existing user profile display code...
    st.subheader("Select a user to view their profile")
    users = get_usernames(analytics_data)

    if not users:
        st.warning("No users found in analytics data")
        return

    # Create the username selector
    selected_username = st.selectbox(
        "Choose a username...",
        options=[user[0] for user in users],
        format_func=lambda x: f"{x} {get_response_category_color(analytics_data['conversations'][x].get('metrics', {}).get('user_messages', 0))}"
    )

    if selected_username:
        user_data = analytics_data['conversations'].get(selected_username)
        if user_data:
            display_user_profile(selected_username, user_data)
        else:
            st.error(f"No data found for user {selected_username}")


# Configure the page
st.set_page_config(
    page_title="Shannon Bot Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data
if 'analytics_data' not in st.session_state:
    st.session_state.analytics_data, st.session_state.analytics_file = load_analytics_data()

# Sidebar
st.sidebar.title("Analytics Dashboard")

# Add refresh button to sidebar
if st.sidebar.button("🔄 Refresh Data"):
    st.session_state.analytics_data, st.session_state.analytics_file = load_analytics_data()
    st.success("Data refreshed successfully!")

# Navigation
selected_page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Client Journey", "User Profiles",
        "Scheduled Follow-ups", "Bulk Review & Send", "Daily Report", "AI Data Assistant", "New Leads"]
)

# Main content area
st.title("Shannon Bot Analytics Dashboard")

if selected_page == "Overview":
    display_overview()

elif selected_page == "Client Journey":
    display_client_journey(st.session_state.analytics_data)

elif selected_page == "User Profiles":
    display_user_profiles(st.session_state.analytics_data)

elif selected_page == "Scheduled Follow-ups":
    # Add Bulk Generate button
    st.button(
        "Bulk Generate Follow-ups",
        on_click=lambda: bulk_generate_followups(
            st.session_state.analytics_data,
            get_users_ready_for_followup(st.session_state.analytics_data)
        ),
        type="primary"
    )
    display_scheduled_followups(
        st.session_state.analytics_data, st.session_state.analytics_file)

elif selected_page == "Bulk Review & Send":
    display_bulk_review_and_send()

elif selected_page == "Daily Report":
    st.header("📊 Daily Report")
    st.info("Daily Report feature coming soon!")

elif selected_page == "AI Data Assistant":
    st.header("🤖 AI Data Assistant")
    st.info("AI Data Assistant feature coming soon!")

elif selected_page == "New Leads":
    # Import and display the new leads dashboard
    try:
        from app.new_leads import main as display_new_leads
        display_new_leads()
    except ImportError as e:
        st.error(f"Could not load New Leads module: {e}")
        st.info("Make sure the new_leads.py file is in the app directory.")
