import streamlit as st


def display_overview():
    """Display the overview page with global metrics"""
    # Global Metrics Header with icon
    st.header("📊 Global Metrics")

    # Create three columns for the metrics sections
    col1, col2, col3 = st.columns(3)

    # Conversation Stats
    with col1:
        st.subheader("Conversation Stats")
        st.metric("Total Conversations", "188")
        st.metric("Total Messages", "911")
        st.metric("User Messages", "491")
        st.metric("Bot Messages", "419")

    # Response Metrics
    with col2:
        st.subheader("Response Metrics")
        st.metric("Total Responses", "170")
        st.metric("Response Rate", "40.6%")

    # Engagement Overview
    with col3:
        st.subheader("Engagement Overview")
        st.metric("Total Messages", "911")
        st.metric("User Messages", "491")
        st.metric("Response Rate", "53.8%")
