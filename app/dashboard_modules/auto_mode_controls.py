import streamlit as st
import os
import sys
from pathlib import Path

# Auto mode state helpers
from app.dashboard_modules.auto_mode_state import (
    is_auto_mode_active,
    is_vegan_auto_mode_active,
    set_auto_mode_status,
    set_vegan_auto_mode_status,
    is_vegan_ad_auto_mode_active,
    set_vegan_ad_auto_mode_status
)


def display_auto_mode_controls():
    """Render compact Auto Mode controls for the Webhook page.

    Notes:
    - No live auto-refresh or activity feed here (per requirements)
    - Launches auto_response_sender.py when enabling any mode
    """
    st.subheader("🤖 Auto Mode Controls")

    col_auto1, col_auto2, col_auto3 = st.columns([1, 1, 1])

    with col_auto1:
        is_currently_active = is_auto_mode_active()
        button_text = "🟢 Auto Mode ON" if is_currently_active else "⚫ Auto Mode OFF"
        button_type = "primary" if is_currently_active else "secondary"
        help_text = "Click to turn OFF auto mode" if is_currently_active else "Click to turn ON auto mode"
        if st.button(button_text, type=button_type, use_container_width=True, help=help_text, key="auto_general_toggle"):
            _toggle_mode(set_auto_mode_status, not is_currently_active)

    with col_auto2:
        is_vegan_active = is_vegan_auto_mode_active()
        button_text = "🟢 Vegan Mode ON" if is_vegan_active else "⚫ Vegan Mode OFF"
        button_type = "primary" if is_vegan_active else "secondary"
        help_text = "Click to turn OFF vegan auto mode" if is_vegan_active else "Click to turn ON vegan auto mode"
        if st.button(button_text, type=button_type, use_container_width=True, help=help_text, key="auto_vegan_toggle"):
            _toggle_mode(set_vegan_auto_mode_status, not is_vegan_active)

    with col_auto3:
        is_vegan_ad_active = is_vegan_ad_auto_mode_active()
        button_text = "🟢 Vegan Ad Mode ON" if is_vegan_ad_active else "⚫ Vegan Ad Mode OFF"
        button_type = "primary" if is_vegan_ad_active else "secondary"
        help_text = "Click to turn OFF vegan ad auto mode" if is_vegan_ad_active else "Click to turn ON vegan ad auto mode"
        if st.button(button_text, type=button_type, use_container_width=True, help=help_text, key="auto_vegan_ad_toggle"):
            _toggle_mode(set_vegan_ad_auto_mode_status, not is_vegan_ad_active)


def _toggle_mode(setter_fn, new_status: bool):
    try:
        success = setter_fn(new_status)
        if not success:
            st.error("Error updating mode status. Check logs.")
            return

        if new_status:
            st.success("✅ Mode ENABLED!")
            _launch_auto_sender()
            st.balloons()
        else:
            st.info("Mode DISABLED.")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to toggle mode: {e}")


def _launch_auto_sender():
    try:
        shanbot_dir = Path(__file__).parent.parent
        script_path = os.path.join(shanbot_dir, "auto_response_sender.py")
        if not os.path.exists(script_path):
            st.error(f"Auto-sender script not found at {script_path}")
            return
        import subprocess
        subprocess.Popen(
            [sys.executable, "-u", script_path],
            cwd=shanbot_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(
                subprocess, 'CREATE_NEW_CONSOLE') else 0
        )
        st.info("✅ Auto-sender started in a new window.")
    except Exception as e:
        st.error(f"Error starting auto-sender: {e}")
