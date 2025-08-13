# Background Bio Fetcher for ShanBot

## Overview

The Background Bio Fetcher automatically retrieves and analyzes Instagram bios for new followers/leads when they're added to your database. This gives you instant conversation topics and insights about each person you're chatting with.

## How It Works

### 1. Background Monitoring
- **Automatic Detection**: Runs every 30 seconds to check for new users without bio data
- **Silent Operation**: Runs in the background - you won't even notice it's working
- **Rate Limiting**: Processes only 5 users per cycle to avoid Instagram rate limits

### 2. Bio Analysis Process
For each new user, the system:
1. **Fetches Instagram Profile**: Gets bio text, follower count, verification status, etc.
2. **AI Analysis**: Uses Gemini to extract:
   - Conversation topics (3-5 specific conversation starters)
   - Interests and hobbies
   - Personality traits
   - Lifestyle indicators
   - Fitness relevance score (1-10)
   - Coaching potential assessment
   - Suggested conversation style

### 3. Integration with ShanBot
- **Database Storage**: All bio data is saved to your SQLite database
- **Prompt Enhancement**: Bio insights are automatically included in Gemini prompts
- **Dashboard Access**: Bio data appears in your dashboard for each user

## Features

### ✅ What It Does
- **Auto-fetches** Instagram bios for new users
- **Analyzes** bio content with AI to extract conversation topics
- **Integrates** with your existing chat system
- **Provides** personalized conversation starters
- **Runs** continuously in the background
- **Handles** rate limiting and errors gracefully

### 🎯 Benefits
- **Instant Context**: Know what to talk about with new followers immediately
- **Better Conversations**: AI suggests personalized topics based on their interests
- **Increased Engagement**: More relevant, targeted conversations
- **Time Saving**: No manual research needed for new contacts
- **Scalable**: Works automatically for all new followers

## Usage

### Automatic Operation
The bio fetcher starts automatically when you run the webhook server:

```bash
python webhook0605.py
```

You'll see these startup messages:
```
=== INITIALIZING BACKGROUND SERVICES ===
✅ Background Bio Fetcher started successfully
=== BACKGROUND SERVICES INITIALIZATION COMPLETE ===
```

### Manual Testing
To test the bio fetcher manually:

```bash
# Test with users from database
python test_bio_fetcher.py

# Test with a specific username
python test_bio_fetcher.py specific_username
```

### Checking Results
Bio data is stored in your SQLite database and will automatically appear in:
1. **Dashboard**: User profiles will show bio insights
2. **Chat Prompts**: Gemini will have bio context for better responses
3. **Database**: Raw data is stored in the `metrics_json` field

## Configuration

### Instagram Credentials
The system uses your existing Instagram credentials:
- Username: `cocos_connected`
- Password: `Shannonb3`

### Processing Limits
- **Cycle Interval**: 30 seconds between checks
- **Users Per Cycle**: 5 users max (to avoid rate limiting)
- **Delay Between Users**: 10 seconds

### Browser Requirements
- **ChromeDriver**: Must be installed at `C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe`
- **Chrome Browser**: Latest version recommended

## Technical Details

### Database Integration
Bio data is stored in the `users` table under `metrics_json` with this structure:
```json
{
  "bio_data": {
    "ig_username": "username",
    "bio_text": "Their Instagram bio",
    "conversation_topics": ["topic1", "topic2"],
    "interests": ["interest1", "interest2"],
    "personality_traits": ["trait1", "trait2"],
    "lifestyle_indicators": ["indicator1"],
    "coaching_potential": "Assessment text",
    "conversation_style": "casual/professional/etc",
    "fitness_relevance": 7
  },
  "bio_fetch_timestamp": "2024-01-01T12:00:00",
  "bio_analysis_source": "background_bio_fetcher"
}
```

### Prompt Integration
Bio data is automatically added to Gemini prompts in this format:
```
--- PROFILE INSIGHTS (Use this to personalize your responses) ---
Instagram Bio: Their actual bio text
Conversation Topics: topic1, topic2, topic3
Interests: interest1, interest2
Personality Traits: trait1, trait2
Lifestyle: lifestyle_indicator1
Coaching Potential: Assessment of their potential as a client
Suggested Conversation Style: casual
Fitness Relevance Score: 7/10
--- END PROFILE INSIGHTS ---
```

## Monitoring & Logs

### Log Messages to Watch For
```
# Successful operation
Found 3 users needing bio fetch: ['user1', 'user2', 'user3']...
Successfully processed and saved bio for username

# Rate limiting detection
⚠️ RATE LIMITING DETECTED for username!

# Errors
❌ Failed to fetch bio for username
```

### Performance Monitoring
- Check logs for successful bio fetches
- Monitor database growth in `users` table
- Watch for rate limiting warnings

## Troubleshooting

### Common Issues

**1. "ChromeDriver not found"**
- Install ChromeDriver to `C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe`
- Download from: https://chromedriver.chromium.org/

**2. "Failed to login to Instagram"**
- Check Instagram credentials are correct
- Instagram may require verification - check manually
- Consider using app passwords if 2FA is enabled

**3. "No users found without bio data"**
- All users already have bios - system is working!
- Add new users to test functionality

**4. Rate Limiting**
- Normal behavior - system will wait and retry
- Reduce processing frequency if needed
- Instagram may block temporarily - this is expected

### Manual Intervention
If the background service stops:
1. Check logs for errors
2. Restart the webhook server
3. Test manually with `python test_bio_fetcher.py`

## Security Notes

- Instagram credentials are stored in plain text (consider environment variables)
- Browser runs in visible mode (can be changed to headless)
- Rate limiting is built-in to avoid Instagram blocks
- System respects Instagram's terms of service

## Future Enhancements

Potential improvements:
- Environment variable for credentials
- Headless browser mode
- Retry logic for failed fetches
- Bio update detection for existing users
- Analytics on bio fetch success rates

---

**Need Help?** Check the logs for detailed error messages and processing status. 