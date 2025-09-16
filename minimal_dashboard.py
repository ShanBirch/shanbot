import streamlit as st
import os
import sys

# Simple bootstrap for Render
st.set_page_config(
    page_title="Shannon Bot Dashboard",
    layout="wide"
)

st.title("🤖 Shannon Bot Dashboard")
st.success("✅ Dashboard is running on Render!")

# Add basic tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Response Review", "Settings"])

with tab1:
    st.header("📊 Overview")
    st.info("Dashboard successfully deployed to Render")

with tab2:
    st.header("📝 Response Review Queue")
    st.info("Review queue will be connected once webhook integration is complete")

with tab3:
    st.header("⚙️ Settings")
    st.info("Settings panel coming soon")

st.sidebar.success("🎉 Render deployment successful!")
st.sidebar.info("Next: Configure webhook integration")

