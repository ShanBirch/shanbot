#!/usr/bin/env python3
"""
Test Terminal Launch - Simple CMD version
"""

import subprocess
import os


def test_terminal_launch():
    """Test launching both modes"""
    print("🧪 Testing CMD terminal launch...")

    PROJECT_ROOT = r"C:\Users\Shannon\OneDrive\Desktop\shanbot"

    # Test Local Mode
    print("\n🏠 Testing Local Mode...")
    terminal_title = "Smart Lead Finder - LOCAL MODE (Bayside Gym Clients)"
    account_info = "cocos_pt_studio"
    mode = "local"

    cmd_command = f'''start "{terminal_title}" cmd /k "echo 🚀 {terminal_title} & echo 👤 Using account: {account_info} & echo 🔄 Browser in headless mode - no browser windows & echo 📊 Monitor progress here... & echo. & cd /d "{PROJECT_ROOT}" & echo 🧪 TEST MODE - Would run: python smart_lead_finder.py --mode {mode} & echo. & echo ✅ Test completed. Press any key to close... & pause"'''

    try:
        process = subprocess.Popen(
            cmd_command,
            cwd=PROJECT_ROOT,
            shell=True
        )
        print("✅ LOCAL MODE terminal launched!")
    except Exception as e:
        print(f"❌ LOCAL MODE failed: {e}")
        return False

    # Test Online Mode
    print("\n🌱 Testing Online Mode...")
    terminal_title = "Smart Lead Finder - ONLINE MODE (Vegan Clients)"
    account_info = "cocos_connected"
    mode = "online"

    cmd_command = f'''start "{terminal_title}" cmd /k "echo 🚀 {terminal_title} & echo 👤 Using account: {account_info} & echo 🔄 Browser in headless mode - no browser windows & echo 📊 Monitor progress here... & echo. & cd /d "{PROJECT_ROOT}" & echo 🧪 TEST MODE - Would run: python smart_lead_finder.py --mode {mode} & echo. & echo ✅ Test completed. Press any key to close... & pause"'''

    try:
        process = subprocess.Popen(
            cmd_command,
            cwd=PROJECT_ROOT,
            shell=True
        )
        print("✅ ONLINE MODE terminal launched!")
    except Exception as e:
        print(f"❌ ONLINE MODE failed: {e}")
        return False

    print("\n🎉 Both terminal windows should now be open!")
    print("💡 You should see 2 command prompt windows with different titles.")
    return True


if __name__ == "__main__":
    test_terminal_launch()
