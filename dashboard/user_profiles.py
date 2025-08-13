from typing import Dict, Any, List, Tuple
import streamlit as st
from app.dashboard_modules.scheduled_followups import get_user_sheet_details
import datetime


def get_response_category_color(num_responses: int) -> str:
    """Return color and emoji indicator based on number of responses"""
    if num_responses >= 20:
        return "🟢"  # Green circle for high responders
    elif num_responses >= 11:
        return "🟡"  # Yellow circle for medium responders
    elif num_responses >= 1:
        return "🟠"  # Orange circle for low responders
    else:
        return "🔴"  # Red circle for no response


def get_usernames(data: Dict[str, Any]) -> List[Tuple[str, str, int]]:
    """Extract unique usernames from analytics data with response categorization"""
    try:
        conversations = data.get('conversations', {})
        categorized_users = []

        for username, user_data in conversations.items():
            num_responses = user_data.get(
                'metrics', {}).get('user_messages', 0)
            category_color = get_response_category_color(num_responses)
            categorized_users.append((username, category_color, num_responses))

        # Sort by number of responses in descending order
        categorized_users.sort(key=lambda x: (-x[2]))
        return categorized_users
    except Exception as e:
        st.error(f"Error extracting usernames: {e}")
        return []


def get_user_topics(user_data: Dict[str, Any]) -> List[str]:
    """Get conversation topics from user's analytics data"""
    try:
        client_analysis = user_data.get(
            'metrics', {}).get('client_analysis', {})
        topics = client_analysis.get('conversation_topics', [])
        metrics = user_data.get('metrics', {})

        # Filter out empty or None topics
        filtered_topics = [
            topic for topic in topics if topic and not topic.startswith('**')]

        # Add Topic 5 if not already present
        topic_5 = "Topic 5 - Enquire about leads fitness journey - offer 1 month trial"
        if topic_5 not in filtered_topics:
            filtered_topics.append(topic_5)

        # Add appropriate trial week or paying client messages based on metrics
        current_time = datetime.datetime.now().time()
        morning_message = "Monday Morning: Goooooood Morning! Ready for the week?"
        evening_message = "Wednesday Night: Heya! Hows your week going?"

        if metrics.get('is_paying_client'):
            filtered_topics.extend([
                f"Paying Client - {morning_message}",
                f"Paying Client - {evening_message}"
            ])
        elif metrics.get('trial_week_4'):
            filtered_topics.extend([
                f"Trial Week 4 - {morning_message}",
                f"Trial Week 4 - {evening_message}"
            ])
        elif metrics.get('trial_week_3'):
            filtered_topics.extend([
                f"Trial Week 3 - {morning_message}",
                f"Trial Week 3 - {evening_message}"
            ])
        elif metrics.get('trial_week_2'):
            filtered_topics.extend([
                f"Trial Week 2 - {morning_message}",
                f"Trial Week 2 - {evening_message}"
            ])
        elif metrics.get('trial_week_1'):
            filtered_topics.extend([
                f"Trial Week 1 - {morning_message}",
                f"Trial Week 1 - {evening_message}"
            ])

        return filtered_topics
    except Exception:
        return ["Topic 5 - Enquire about leads fitness journey - offer 1 month trial"]


def display_user_profile(username: str, user_data: Dict[str, Any]):
    """Display user profile information"""
    try:
        # Get client analysis data
        client_analysis = user_data.get(
            'metrics', {}).get('client_analysis', {})
        metrics = user_data.get('metrics', {})

        # Get Instagram username from metrics
        ig_username = metrics.get('ig_username', '')

        # Get additional details from Google Sheet
        sheet_details = get_user_sheet_details(
            ig_username) if ig_username else {}

        # Determine current stage
        current_stage = "Topic 1"
        if metrics.get('is_paying_client'):
            current_stage = "Paying Client"
        elif metrics.get('trial_week_4'):
            current_stage = "Trial Week 4"
        elif metrics.get('trial_week_3'):
            current_stage = "Trial Week 3"
        elif metrics.get('trial_week_2'):
            current_stage = "Trial Week 2"
        elif metrics.get('trial_week_1'):
            current_stage = "Trial Week 1"
        elif metrics.get('trial_offer_made'):
            current_stage = "Topic 5"
        elif metrics.get('topic4_completed'):
            current_stage = "Topic 4"
        elif metrics.get('topic3_completed'):
            current_stage = "Topic 3"
        elif metrics.get('topic2_completed'):
            current_stage = "Topic 2"

        # Create tabs for different sections of the profile
        profile_tab, analysis_tab, conversation_tab, meal_plan_tab, workout_tab, checkin_tab, history_tab = st.tabs([
            "📋 Profile", "📊 Analysis", "💭 Conversation Topics", "🍽️ Meal Plan", "💪 Workout Program", "📝 Weekly Check-in", "📝 History"
        ])

        with profile_tab:
            # Display current stage prominently
            st.info(f"**Current Stage:** {current_stage}")

            # Create three columns for profile information
            col1, col2, col3 = st.columns(3)

            with col1:
                st.subheader("📱 Contact Info")
                if sheet_details.get('first_name') or sheet_details.get('last_name'):
                    full_name = f"{sheet_details.get('first_name', '')} {sheet_details.get('last_name', '')}".strip(
                    )
                    st.write(f"**Name:** {full_name}")
                if sheet_details.get('email'):
                    st.write(f"**Email:** {sheet_details.get('email')}")
                if sheet_details.get('phone'):
                    st.write(f"**Phone:** {sheet_details.get('phone')}")
                if ig_username:
                    st.write(f"**Instagram:** {ig_username}")

            with col2:
                st.subheader("💪 Physical Info")
                if sheet_details.get('sex'):
                    st.write(f"**Sex:** {sheet_details.get('sex')}")
                if sheet_details.get('dob'):
                    st.write(f"**DOB:** {sheet_details.get('dob')}")
                if sheet_details.get('weight'):
                    st.write(f"**Weight:** {sheet_details.get('weight')}")
                if sheet_details.get('height'):
                    st.write(f"**Height:** {sheet_details.get('height')}")

            with col3:
                st.subheader("🎯 Training Info")
                if sheet_details.get('gym_access'):
                    st.write(
                        f"**Gym Access:** {sheet_details.get('gym_access')}")
                if sheet_details.get('training_frequency'):
                    st.write(
                        f"**Training Frequency:** {sheet_details.get('training_frequency')}")
                if sheet_details.get('daily_calories'):
                    st.write(
                        f"**Daily Calories:** {sheet_details.get('daily_calories')}")
                if sheet_details.get('macro_split'):
                    st.write(
                        f"**Macro Split:** {sheet_details.get('macro_split')}")

            # Create expandable sections for detailed information
            with st.expander("🎯 Goals and Requirements"):
                if sheet_details.get('fitness_goals'):
                    st.write("**Long Term Fitness Goals:**")
                    st.info(sheet_details.get('fitness_goals'))
                if sheet_details.get('specific_goal'):
                    st.write("**Specific Goal:**")
                    st.info(sheet_details.get('specific_goal'))
                if sheet_details.get('dietary_requirements'):
                    st.write("**Dietary Requirements:**")
                    st.info(sheet_details.get('dietary_requirements'))
                if sheet_details.get('excluded_foods'):
                    st.write("**Excluded Foods:**")
                    st.info(sheet_details.get('excluded_foods'))

            with st.expander("💪 Exercise Preferences"):
                if sheet_details.get('preferred_exercises'):
                    st.write("**Preferred Exercises:**")
                    st.info(sheet_details.get('preferred_exercises'))
                if sheet_details.get('excluded_exercises'):
                    st.write("**Exercises to Avoid:**")
                    st.info(sheet_details.get('excluded_exercises'))

            # Display Instagram-derived profile bio if available
            if client_analysis and 'profile_bio' in client_analysis:
                with st.expander("📸 Instagram Profile Analysis"):
                    bio = client_analysis['profile_bio']
                    if 'INTERESTS' in bio and bio['INTERESTS']:
                        st.write("**🎯 Key Interests:**")
                        for interest in bio['INTERESTS']:
                            st.write(f"- {interest}")
                    if 'PERSONALITY TRAITS' in bio and bio['PERSONALITY TRAITS']:
                        st.write("**👤 Personality Traits:**")
                        for trait in bio['PERSONALITY TRAITS']:
                            st.write(f"- {trait}")
                    if 'LIFESTYLE' in bio and bio['LIFESTYLE']:
                        st.write("**🌟 Lifestyle:**")
                        st.info(bio['LIFESTYLE'])

        with analysis_tab:
            st.subheader("📸 Instagram Analysis")
            insta_col1, insta_col2 = st.columns(2)

            with insta_col1:
                if 'posts_analyzed' in client_analysis:
                    st.metric("Posts Analyzed", client_analysis.get(
                        'posts_analyzed', 0))
                if 'interests' in client_analysis:
                    st.write("**Detected Interests:**")
                    interests = [i for i in client_analysis.get('interests', [])
                                 if i and not i.startswith('**')]
                    for interest in interests:
                        st.write(f"- {interest}")

            with insta_col2:
                if 'recent_activities' in client_analysis:
                    st.write("**Recent Activities:**")
                    activities = [a for a in client_analysis.get('recent_activities', [])
                                  if a and not a.startswith('**')]
                    for activity in activities:
                        st.write(f"- {activity}")

        with conversation_tab:
            st.subheader("🗣️ Conversation Topics")

            # Display current stage prominently
            st.info(f"**Current Stage:** {current_stage}")

            # Initial Topics (1-4)
            st.subheader("Initial Engagement Topics")
            topics = [
                "Topic 1 - Discuss their favorite plant-based protein sources for muscle growth and any creative vegetarian recipes they've discovered recently.",
                "Topic 2 - Explore their approach to tracking progress with clients, specifically what metrics they prioritize beyond just weight loss and how they use fitness apps.",
                "Topic 3 - Talk about their experience adapting resistance training techniques for clients with different fitness levels and what common mistakes they see people make.",
                "Topic 4 - Share tips on incorporating high-protein vegetarian meals into a busy schedule and how they advise clients to make healthy eating more convenient in Melbourne."
            ]

            for topic in topics:
                if topic.startswith(current_stage):
                    st.success(topic)  # Highlight current topic
                else:
                    st.info(topic)

            # Trial Offer (Topic 5)
            st.subheader("Trial Offer Stage")
            topic_5 = "Topic 5 - Enquire about leads fitness journey - offer 1 month trial"
            if current_stage == "Topic 5":
                st.success(topic_5)
            else:
                st.info(topic_5)

            # Trial Weeks
            st.subheader("Trial Period Topics")
            trial_weeks = {
                "Trial Week 1": [
                    "Trial Week 1 - Monday Morning: Goooooood Morning! Ready for the week?",
                    "Trial Week 1 - Wednesday Night: Heya! Hows your week going?"
                ],
                "Trial Week 2": [
                    "Trial Week 2 - Monday Morning: Goooooood Morning! Ready for the week?",
                    "Trial Week 2 - Wednesday Night: Heya! Hows your week going?"
                ],
                "Trial Week 3": [
                    "Trial Week 3 - Monday Morning: Goooooood Morning! Ready for the week?",
                    "Trial Week 3 - Wednesday Night: Heya! Hows your week going?"
                ],
                "Trial Week 4": [
                    "Trial Week 4 - Monday Morning: Goooooood Morning! Ready for the week?",
                    "Trial Week 4 - Wednesday Night: Heya! Hows your week going?"
                ]
            }

            for week, messages in trial_weeks.items():
                if week == current_stage:
                    for msg in messages:
                        st.success(msg)
                else:
                    for msg in messages:
                        st.info(msg)

            # Paying Client
            st.subheader("Paying Client Topics")
            paying_client_messages = [
                "Paying Client - Monday Morning: Goooooood Morning! Ready for the week?",
                "Paying Client - Wednesday Night: Heya! Hows your week going?"
            ]

            if current_stage == "Paying Client":
                for msg in paying_client_messages:
                    st.success(msg)
            else:
                for msg in paying_client_messages:
                    st.info(msg)

        with meal_plan_tab:
            st.subheader("🍽️ Meal Plan")
            st.info("Meal plan feature coming soon!")

        with workout_tab:
            st.subheader("💪 Workout Program")
            st.info("Workout program feature coming soon!")

        with checkin_tab:
            st.subheader("📝 Weekly Check-in Review")
            st.info("Weekly check-in review feature coming soon!")

        with history_tab:
            st.subheader("💬 Conversation History")
            conversation_history = user_data.get(
                'metrics', {}).get('conversation_history', [])

            if conversation_history:
                for message in conversation_history:
                    with st.container():
                        timestamp = message.get('timestamp', '').split('T')[0]
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
        st.error(f"Error displaying user profile: {e}")


def display_user_profiles(analytics_data: Dict[str, Any]):
    """Display the user profiles page"""
    st.header("👥 User Profiles")

    # Get list of categorized usernames
    categorized_users = get_usernames(analytics_data)

    if categorized_users:
        # Create formatted options for the dropdown
        options = [f"{color} {username} ({responses} messages)"
                   for username, color, responses in categorized_users]

        # Create dropdown for username selection
        selected_option = st.selectbox(
            "Select a user to view their profile",
            options,
            index=None,
            placeholder="Choose a username..."
        )

        # Display user profile when selected
        if selected_option:
            selected_user = selected_option.split(
                " ")[1]  # Get username after the emoji
            user_data = analytics_data.get(
                'conversations', {}).get(selected_user)
            if user_data:
                display_user_profile(selected_user, user_data)
            else:
                st.warning(f"No data found for user: {selected_user}")
    else:
        st.warning(
            "No usernames found in the analytics data. Please check the data format or refresh the data.")
