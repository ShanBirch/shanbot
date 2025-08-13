import streamlit as st
from typing import Dict, Any, List, Tuple


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


def get_default_topics() -> List[str]:
    """Get the default list of conversation topics"""
    return [
        "Topic 1 - Discuss their favorite plant-based protein sources for muscle growth and any creative vegetarian recipes they've discovered recently.",
        "Topic 2 - Explore their approach to tracking progress with clients, specifically what metrics they prioritize beyond just weight loss and how they use fitness apps.",
        "Topic 3 - Talk about their experience adapting resistance training techniques for clients with different fitness levels and what common mistakes they see people make.",
        "Topic 4 - Share tips on incorporating high-protein vegetarian meals into a busy schedule and how they advise clients to make healthy eating more convenient in Melbourne.",
        "Topic 5 - Enquire about leads fitness journey - offer 1 month trial"
    ]


def get_user_topics(user_data: Dict[str, Any]) -> List[str]:
    """Get conversation topics from user's analytics data"""
    try:
        client_analysis = user_data.get(
            'metrics', {}).get('client_analysis', {})
        topics = client_analysis.get('conversation_topics', [])
        # Filter out empty or None topics
        filtered_topics = [
            topic for topic in topics if topic and not topic.startswith('**')]

        # Add Topic 5 if not already present
        topic_5 = "Topic 5 - Enquire about leads fitness journey - offer 1 month trial"
        if topic_5 not in filtered_topics:
            filtered_topics.append(topic_5)

        return filtered_topics
    except Exception:
        return ["Topic 5 - Enquire about leads fitness journey - offer 1 month trial"]


def display_user_profile(username: str, user_data: Dict[str, Any]):
    """Display user profile information"""
    try:
        # Get client analysis data
        client_analysis = user_data.get(
            'metrics', {}).get('client_analysis', {})

        # Create tabs for different sections of the profile
        profile_tab, analysis_tab, conversation_tab, history_tab = st.tabs([
            "📋 Profile", "📊 Analysis", "💭 Conversation Topics", "📝 History"
        ])

        with profile_tab:
            # Display profile bio if available
            if client_analysis and 'profile_bio' in client_analysis:
                bio = client_analysis['profile_bio']
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
            topics = get_user_topics(user_data)
            if topics:
                for topic in topics:
                    st.info(topic)
            else:
                st.warning("No conversation topics available yet.")

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
