import streamlit as st
import json
import os
from pathlib import Path
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_user_data():
    """Load all user data from individual JSON files"""
    users_data = {}
    by_user_dir = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'by_user')

    if not os.path.exists(by_user_dir):
        logger.error(f"Directory not found: {by_user_dir}")
        return users_data

    # List all JSON files in the directory
    try:
        for filename in os.listdir(by_user_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(by_user_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        user_data = json.load(f)
                        # Only include users with Instagram usernames
                        if user_data.get('ig_username'):
                            users_data[user_data['ig_username']] = user_data
                            logger.info(
                                f"Loaded user data for: {user_data['ig_username']}")
                except Exception as e:
                    logger.error(f"Error loading {filename}: {str(e)}")
                    continue

        logger.info(f"Total users loaded: {len(users_data)}")
        return users_data
    except Exception as e:
        logger.error(f"Error reading directory {by_user_dir}: {str(e)}")
        return users_data


def render_user_profile():
    """Display user profiles with detailed information"""
    st.title("👤 User Profiles")

    # Load user data if not in session state
    if 'users_data' not in st.session_state:
        st.session_state.users_data = load_user_data()

    # Debug information
    st.sidebar.expander("Debug Info", expanded=False).write(
        f"Total users loaded: {len(st.session_state.users_data)}\n"
        f"Loading from: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'by_user')}"
    )

    # User selection
    users = []
    for username, data in st.session_state.users_data.items():
        users.append({
            "username": username,
            "has_bio": data.get('has_bio', False),
            "has_conversations": data.get('has_conversations', False)
        })

    if not users:
        st.warning("No users with Instagram usernames found.")
        st.info(
            f"Looking for data in: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'by_user')}")
        return

    # Sort users by username
    users.sort(key=lambda x: x["username"].lower())

    # Create a format function that shows bio/conversation status
    def format_user_option(user):
        status = []
        if user["has_bio"]:
            status.append("📝")
        if user["has_conversations"]:
            status.append("💬")
        status_str = " ".join(status)
        return f"@{user['username']} {status_str}"

    selected_user = st.selectbox(
        "Select User",
        users,
        format_func=format_user_option
    )

    if selected_user:
        user_data = st.session_state.users_data[selected_user["username"]]

        # Display user info
        st.header(f"@{selected_user['username']}")

        # Display bio and profile info
        with st.expander("📝 Bio & Profile Info", expanded=True):
            if user_data.get('bio'):
                st.write(user_data['bio'])
            else:
                st.info("No bio available for this user")

            # Display additional profile information
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Interests")
                interests = user_data.get('interests', [])
                if interests:
                    for interest in interests:
                        st.write(f"• {interest}")
                else:
                    st.info("No interests listed")

            with col2:
                st.subheader("Personality Traits")
                traits = user_data.get('personality_traits', [])
                if traits:
                    for trait in traits:
                        st.write(f"• {trait}")
                else:
                    st.info("No personality traits listed")

        # Display metrics
        st.subheader("📊 Engagement Metrics")
        metrics = user_data.get('metrics', {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Messages", metrics.get('total_messages', 0))
        with col2:
            st.metric("Questions Asked", metrics.get('ai_questions', 0))
        with col3:
            st.metric("User Responses", metrics.get(
                'user_responses_to_ai_question', 0))

        # Display conversation history
        st.subheader("💬 Conversation History")
        conversation_history = user_data.get('conversation_history', [])

        if not conversation_history:
            st.info("No conversation history available for this user")
        else:
            # Add date filter
            all_dates = []
            for msg in conversation_history:
                try:
                    date = datetime.fromisoformat(
                        msg.get('timestamp', '')).date()
                    all_dates.append(date)
                except (ValueError, TypeError):
                    continue

            if all_dates:
                min_date = min(all_dates)
                max_date = max(all_dates)
                selected_date = st.date_input(
                    "Filter by date",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date
                )

                # Filter conversations by selected date
                filtered_conversations = [
                    msg for msg in conversation_history
                    if datetime.fromisoformat(msg.get('timestamp', '')).date() == selected_date
                ]
            else:
                filtered_conversations = conversation_history

            # Display messages
            for msg in filtered_conversations:
                is_ai = msg.get('type', '') == 'ai' or msg.get('is_ai', False)
                timestamp = msg.get('timestamp', '')
                message = msg.get('text', '') or msg.get('message', '')

                # Format timestamp
                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    pass

                st.markdown(
                    f"""<div style='padding:10px;border-radius:10px;margin:5px 0;
                    background-color:{"#DCF8C6" if is_ai else "#FFFFFF"};
                    border:1px solid {"#c5eeb4" if is_ai else "#e0e0e0"};'>
                    <small style='color:#888;'>{timestamp}</small><br>
                    {message}
                    </div>""",
                    unsafe_allow_html=True
                )
