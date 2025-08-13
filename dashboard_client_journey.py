import streamlit as st
from typing import Dict, Any


def get_stage_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
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

            if client_analysis and client_analysis.get('posts_analyzed', 0) > 0:
                analyzed_users += 1
                total_analyzed_posts += client_analysis.get(
                    'posts_analyzed', 0)

            if user_metrics.get('user_messages', 0) > 0:
                metrics['engaged_users'] += 1
                metrics['total_messages'] += user_metrics.get(
                    'total_messages', 0)

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
        st.error(f"Error calculating stage metrics: {e}")
        return metrics


def display_client_journey(analytics_data: Dict[str, Any]):
    """Display the client journey page with multiple tabs"""
    st.header("🚂 Client Journey")

    # Calculate overall metrics
    metrics = get_stage_metrics(analytics_data)

    # Create tabs for different journey stages
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Topic 1", "Topic 2", "Topic 3", "Topic 4",
        "Topic 5 (Health/Fitness + Trial Offer)",
        "Trial Period Week 1-3",
        "Trial Period Week 4 Offer",
        "Paying Client"
    ])

    with tab1:
        st.subheader("Instagram Analysis Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Profiles", metrics['total_users'])
            st.metric("Analyzed Profiles", metrics['analyzed_profiles'])
        with col2:
            st.metric("Engagement Rate", f"{metrics['response_rate']:.1f}%")
            st.metric("Average Posts Analyzed",
                      f"{metrics['avg_posts_per_profile']:.1f}")
        with col3:
            st.metric("Total Messages", metrics['total_messages'])
            st.metric("Average Messages/User",
                      f"{metrics['avg_messages']:.1f}")

    with tab2:
        st.subheader("Topic 2")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Users in Stage", "0")
            st.metric("Engagement Rate", "0%")
        with col2:
            st.metric("Average Response Time", "0 mins")
            st.metric("Conversion Rate", "0%")

    # Similar structure for other tabs (3-8)
    # Add placeholder metrics for now
