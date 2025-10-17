# Instagram Inbox Checker

Comprehensive tools to check your Instagram DMs for unread messages.

## 📋 Overview

This toolset provides multiple methods to check your Instagram inbox for unread messages:

1. **Database Method** - Query local analytics database
2. **Selenium Method** - Automated web scraping with browser automation
3. **Manual Method** - Step-by-step guide for manual checking

## 🚀 Quick Start

### Method 1: Simple Check (All Methods)

```bash
python3 check_unread_instagram_messages.py
```

This will run all available methods and provide a comprehensive report.

### Method 2: Advanced Automated Check

```bash
python3 instagram_inbox_checker.py
```

This uses Selenium to automatically log in and scan your Instagram inbox.

### Method 3: Manual Guide Only

```bash
python3 check_unread_instagram_messages.py --method manual
```

Displays step-by-step instructions for manually checking Instagram.

## 📦 Installation

### Prerequisites

1. **Python 3.7+**
   ```bash
   python3 --version
   ```

2. **Selenium** (for automated checking)
   ```bash
   pip install selenium
   ```

3. **ChromeDriver** (for Selenium)
   - Download from: https://chromedriver.chromium.org/
   - Or use package manager:
     ```bash
     # macOS
     brew install chromedriver
     
     # Ubuntu/Debian
     sudo apt-get install chromium-chromedriver
     
     # Windows - download and place in C:\SeleniumDrivers\
     ```

## 🔧 Usage

### Basic Command

```bash
# Check all methods
python3 check_unread_instagram_messages.py

# Database only
python3 check_unread_instagram_messages.py --method database

# Selenium automated check only
python3 check_unread_instagram_messages.py --method selenium

# Manual guide only
python3 check_unread_instagram_messages.py --method manual
```

### Advanced Automated Checker

```bash
# Run with browser visible
python3 instagram_inbox_checker.py

# Run in headless mode (no browser window)
python3 instagram_inbox_checker.py --headless

# Don't save results to file
python3 instagram_inbox_checker.py --no-save
```

## 📊 Output

### Example Output

```
============================================================
   📬 INSTAGRAM UNREAD MESSAGE CHECKER
============================================================

🔍 Checking for unread Instagram messages...
============================================================
📂 Using database: app/analytics_data_good.sqlite

✅ Found 5 messages using query method 1

📬 UNREAD MESSAGES:
------------------------------------------------------------

1. @aussiepotter
   Time: 2025-10-17 08:30:15
   Message: Hey Shannon, can you help me with my meal plan?

2. @kristyleecoop
   Time: 2025-10-17 09:15:42
   Message: Just sent you my progress pics!

...

============================================================
📊 Total unread messages: 5
💬 Active conversations (last 7 days): 12
```

### Saved Results

Results are automatically saved to `instagram_inbox_check.json`:

```json
{
  "unread_count": 5,
  "unread_conversations": [
    {
      "name": "aussiepotter",
      "detected_at": "2025-10-17T10:30:00"
    }
  ],
  "message_requests": 2,
  "timestamp": "2025-10-17T10:30:00"
}
```

## 🎯 Features

### Database Method
- ✅ Fast and reliable
- ✅ Works offline
- ✅ Accesses local conversation history
- ❌ Requires database to be present

### Selenium Method
- ✅ Real-time check against Instagram
- ✅ Detects notification badges
- ✅ Finds message requests
- ❌ Requires ChromeDriver
- ❌ Requires login

### Manual Method
- ✅ Always works
- ✅ No dependencies
- ✅ Comprehensive guide
- ❌ Requires manual effort

## 🔐 Authentication

### Using Saved Cookies

If you have Instagram cookies saved in `scripts/instagram_cookies.json`, the automated checker will use them to skip login.

### Manual Login

If cookies aren't available, you'll be prompted to log in manually:

1. Browser window will open
2. Log in to Instagram
3. Complete any 2FA
4. Press ENTER in terminal to continue

## 🛠️ Troubleshooting

### "ChromeDriver not found"

**Solution:**
- Download ChromeDriver from https://chromedriver.chromium.org/
- Place in one of these locations:
  - `C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe` (Windows)
  - `/usr/local/bin/chromedriver` (macOS/Linux)
  - Current directory

### "Database not found"

**Solution:**
- Ensure `app/analytics_data_good.sqlite` exists
- Or update the path in `check_unread_instagram_messages.py`
- Or use `--method selenium` or `--method manual` instead

### "Could not automatically detect unread messages"

**Solution:**
- Instagram's UI may have changed
- Use manual review when browser opens
- Submit an issue with Instagram's current UI structure

## 📝 Integration with Inbox Management

These tools integrate with the existing `inbox.md` workflow:

```python
# In your chat interface, use commands like:
"How many messages are in my inbox?"
"Show me message #1"
"Generate response for @username"
```

See `inbox.md` for full workflow documentation.

## 🔄 Automation

### Schedule Regular Checks

**Linux/macOS (crontab):**
```bash
# Check every hour
0 * * * * cd /path/to/workspace && python3 check_unread_instagram_messages.py --method database >> inbox_check.log
```

**Windows (Task Scheduler):**
- Create a scheduled task to run `instagram_inbox_checker.py`
- Set trigger: Every 1 hour
- Action: Run Python script

## 📁 Files

- `check_unread_instagram_messages.py` - Main multi-method checker
- `instagram_inbox_checker.py` - Advanced Selenium-based checker
- `instagram_inbox_check.json` - Results output file
- `inbox.md` - Inbox management workflow guide

## 🤝 Contributing

To improve Instagram selectors or add new features:

1. Update selectors in `instagram_inbox_checker.py`
2. Test with current Instagram UI
3. Submit changes

## 📄 License

Part of the Instagram automation suite.

## ⚠️ Disclaimer

These tools are for personal use. Use responsibly and in accordance with Instagram's Terms of Service.

---

**Last Updated:** October 2025
