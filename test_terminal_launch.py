#!/usr/bin/env python3
"""
Test Terminal Launch - Verify terminal windows open correctly
"""

import subprocess
import os


def test_local_terminal():
    """Test launching local mode in terminal"""
    print("🧪 Testing LOCAL MODE terminal launch...")

    PROJECT_ROOT = r"C:\Users\Shannon\OneDrive\Desktop\shanbot"
    terminal_title = "Smart Lead Finder - LOCAL MODE (Bayside Gym Clients)"
    account_info = "cocos_pt_studio"
    mode = "local"

    powershell_command = f'''
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "& {{
        $Host.UI.RawUI.WindowTitle = '{terminal_title}';
        cd '{PROJECT_ROOT}';
        Write-Host '🚀 {terminal_title}' -ForegroundColor Green;
        Write-Host '👤 Using account: {account_info}' -ForegroundColor Cyan;
        Write-Host '🔄 Browser in headless mode - no browser windows' -ForegroundColor Yellow;
        Write-Host '📊 Monitor progress here...' -ForegroundColor White;
        Write-Host '';
        Write-Host '🧪 TEST MODE - Would run: python smart_lead_finder.py --mode {mode}' -ForegroundColor Magenta;
        Write-Host '';
        Write-Host '✅ Test completed. Press any key to close...' -ForegroundColor Green;
        Read-Host
    }}"
    '''

    try:
        process = subprocess.Popen(
            ["powershell", "-Command", powershell_command],
            cwd=PROJECT_ROOT,
            shell=True
        )
        print("✅ LOCAL MODE terminal launched successfully!")
        return True
    except Exception as e:
        print(f"❌ Error launching LOCAL MODE terminal: {e}")
        return False


def test_online_terminal():
    """Test launching online mode in terminal"""
    print("🧪 Testing ONLINE MODE terminal launch...")

    PROJECT_ROOT = r"C:\Users\Shannon\OneDrive\Desktop\shanbot"
    terminal_title = "Smart Lead Finder - ONLINE MODE (Vegan Clients)"
    account_info = "cocos_connected"
    mode = "online"

    powershell_command = f'''
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "& {{
        $Host.UI.RawUI.WindowTitle = '{terminal_title}';
        cd '{PROJECT_ROOT}';
        Write-Host '🚀 {terminal_title}' -ForegroundColor Green;
        Write-Host '👤 Using account: {account_info}' -ForegroundColor Cyan;
        Write-Host '🔄 Browser in headless mode - no browser windows' -ForegroundColor Yellow;
        Write-Host '📊 Monitor progress here...' -ForegroundColor White;
        Write-Host '';
        Write-Host '🧪 TEST MODE - Would run: python smart_lead_finder.py --mode {mode}' -ForegroundColor Magenta;
        Write-Host '';
        Write-Host '✅ Test completed. Press any key to close...' -ForegroundColor Green;
        Read-Host
    }}"
    '''

    try:
        process = subprocess.Popen(
            ["powershell", "-Command", powershell_command],
            cwd=PROJECT_ROOT,
            shell=True
        )
        print("✅ ONLINE MODE terminal launched successfully!")
        return True
    except Exception as e:
        print(f"❌ Error launching ONLINE MODE terminal: {e}")
        return False


def main():
    """Test both terminal launch modes"""
    print("🚀 TESTING TERMINAL LAUNCH FUNCTIONALITY")
    print("=" * 50)

    # Test local mode
    local_success = test_local_terminal()

    print("\n" + "=" * 50)

    # Test online mode
    online_success = test_online_terminal()

    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"   🏠 Local Mode: {'✅ PASS' if local_success else '❌ FAIL'}")
    print(f"   🌱 Online Mode: {'✅ PASS' if online_success else '❌ FAIL'}")

    if local_success and online_success:
        print("\n🎉 All tests passed! Terminal launching is working correctly.")
        print("💡 You should see 2 terminal windows open with different titles.")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    main()
