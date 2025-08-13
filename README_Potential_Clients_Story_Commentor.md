# Potential Clients Story Commentor - FULLY INTEGRATED

A sophisticated Instagram automation tool for targeting high-potential fitness clients by analyzing their stories and sending personalized messages. **Now fully integrated with story1.py pause-analyze-send functionality.**

## 🎯 Purpose

This script helps Shannon's Coco's Connected fitness business reach potential clients by:
- Reading high-potential clients from Shannon's dashboard analytics (coaching score >= 70)
- Automatically navigating to target user profiles
- Viewing and analyzing their Instagram stories with AI
- Pausing stories and taking verified screenshots
- Manual message confirmation workflow
- Sending contextual, fitness-related messages based on story content
- Tracking engagement analytics and response rates

## ✅ **INTEGRATION COMPLETE** 

**Successfully Integrated from story1.py:**
- ✅ `PauseMonitor` class for automatic story pause maintenance
- ✅ `ConversationAnalytics` class with SQLite database integration
- ✅ `process_single_story()` workflow with manual confirmation
- ✅ Enhanced pause/screenshot/analyze workflow
- ✅ Username extraction and duplicate prevention
- ✅ Session tracking with `processed_usernames.json`
- ✅ Manual message confirmation with edit capabilities
- ✅ Robust error handling and cleanup

## 🔧 Features

### Smart Story Analysis
- **Visual Profile Analysis**: Uses Gemini AI to analyze profile screenshots and detect story rings or highlights
- **Story Detection**: Automatically identifies active stories (colored ring around profile picture)
- **Highlight Detection**: Recognizes saved story highlights for engagement opportunities
- **AI-Powered Content Analysis**: Uses Google Gemini to analyze story/highlight content
- **Robust API Retry System**: 3-attempt retry logic with exponential backoff for Gemini API failures
- **Multiple Fallback Options**: 8 different fallback comments when AI analysis fails
- **Screenshot Verification**: Retry logic ensures quality screenshots with size validation
- **Context-Aware Messaging**: Generates personalized messages based on story content
- **Manual Confirmation**: User reviews and can edit every message before sending

### Intelligent Engagement
- **Visual Story Detection**: Screenshots profiles and uses AI to detect story availability
- **Story Replies**: Comments directly on active stories when available
- **Highlight Engagement**: Engages with story highlights when no active stories exist
- **Smart Filtering**: Only engages with users who have visual content (stories/highlights)
- **Human-like Behavior**: Random delays and natural interaction patterns
- **Duplicate Prevention**: Tracks users across sessions to avoid re-messaging

### Analytics & Tracking
- **SQLite Database Integration**: Uses Shannon's main analytics database
- **User Interaction History**: Tracks all engagements per user
- **Success Metrics**: Monitors message delivery and response rates
- **Story Type Analytics**: Identifies most engaging content types
- **Performance Insights**: Correction tracking and bot improvement metrics

## 📋 Prerequisites

### Required Software
- Python 3.8+
- Chrome browser
- ChromeDriver (download from https://chromedriver.chromium.org/)

### Required Accounts & API Keys
- Instagram business account
- Google Gemini API key (get from https://makersuite.google.com/app/apikey)

### Python Dependencies
```bash
pip install selenium google-generativeai
```

## ⚙️ Setup

### 1. Environment Variables
Set the following environment variables:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password

# Optional (will use defaults if not set)
INSTAGRAM_USERNAME=cocos_connected  # Shannon's account
```

### 2. ChromeDriver Setup
- Download ChromeDriver matching your Chrome version
- Update the `chromedriver_path` in the CONFIG section of the script
- Current path: `C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe`

### 3. Analytics Database
The script automatically reads from Shannon's dashboard analytics:
- File: `app\analytics_data_good.json`
- Filters users with coaching scores >= threshold (default 70)
- No manual user list needed - pulls from existing analytics

## 🚀 Usage

### Basic Execution
```bash
python potential_clients_story_commentor.py
```

### Interactive Setup:
```
Enter minimum coaching score (default 70): 75
Enter max users per day (default 20): 15

🎯 Configuration:
   Minimum Coaching Score: 75
   Max Users Per Day: 15

🚀 Starting campaign...
```

### Example Workflow:
```
🎯 Processing user: fitness_girl_23 (Priority: high, Score: 85)
📱 Navigating to profile: fitness_girl_23
🎥 Found fitness_girl_23's story in stories bar
⏸️  Story paused successfully
📱 Taking screenshot and analyzing...
🤖 Analyzing story with Gemini AI...

📊 Analysis results for fitness_girl_23:
   Fitness Relevance: 9/10
   Client Potential: 8/10

🔍 MESSAGE CONFIRMATION REQUIRED
================================================================================
👤 Username: fitness_girl_23
📖 Story Description: User doing deadlifts in gym
💬 Proposed Comment: 'Nice form on those deads! How long have you been lifting?'
📊 Bot Stats: 15 comments, 12.5% correction rate
================================================================================

📋 Options:
  1. Press ENTER to send the message as-is
  2. Type 'edit' or 'e' to modify the message
  3. Type 'skip' or 's' to skip this story
  4. Type 'quit' or 'q' to stop the bot

➤ Your choice: [USER INPUT]

✅ Sending message as-is...
💬 Story reply sent: "Nice form on those deads! How long have you been lifting?"
✅ Successfully engaged with fitness_girl_23
```

## 🧠 AI Analysis System

### Analysis Criteria
The Gemini AI evaluates each story on:

1. **Description**: What's happening in the story
2. **Fitness Relevance** (1-10): How related to fitness/health/wellness
3. **Client Potential** (1-10): Likelihood they'd be interested in personal training
4. **Engagement Approach**: Best method to reach out
5. **Message**: Personalized message based on content

### Manual Confirmation System
- **Every message reviewed**: User sees analysis and proposed message
- **Edit capability**: Can modify messages before sending
- **Learning system**: Tracks corrections to improve AI prompts
- **Skip/quit options**: Full control over each interaction

### Message Examples by Content Type:

**Gym/Workout Stories:**
- "Nice session! What's your favorite exercise at the moment?"
- "Crushing it! How long have you been training?"

**Food/Nutrition Stories:**
- "That looks amazing! Do you cook much healthy food yourself?"
- "Meal prep king! Any favorite healthy recipes?"

**Travel Stories:**
- "Beautiful spot! Do you manage to stay active when you're traveling?"
- "Amazing views! Find any good local gyms there?"

## 📊 Analytics & Monitoring

### Database Integration:
- **SQLite Database**: `app\analytics_data_good.sqlite`
- **JSON Analytics**: `app\analytics_data_good.json`
- **Session Tracking**: `processed_usernames.json`
- **Daily Users**: `processed_users_YYYY-MM-DD.json`

### Analytics Include:
- Total stories analyzed
- Messages sent successfully  
- User interaction history
- Response rates and correction tracking
- Top performing message types
- Story content that drives engagement

## 🛡️ Robust Fallback Systems

### Gemini API Resilience (Like story1.py)
- **3-Retry System**: Each analysis attempt gets 3 tries with exponential backoff
- **Response Validation**: Checks for valid candidates and non-empty responses
- **Error Classification**: Different handling for empty responses vs. API errors
- **Progressive Delays**: 3-5 second waits between retry attempts
- **Graceful Degradation**: Never fails completely, always provides usable fallbacks

### Screenshot Reliability
- **2-Attempt Verification**: Each screenshot gets 2 tries with content validation
- **Size Verification**: Ensures screenshots are >1KB (valid content)
- **Fallback Screenshot**: Basic capture without verification as last resort
- **Error Recovery**: Continues operation even if screenshots fail

### Multiple Comment Fallbacks
```python
fallback_comments = [
    "Love this! 🔥", "Looking good!", "Nice!", "Awesome!",
    "Love it!", "Great shot!", "Amazing!", "So cool!"
]
```

### Error Handling Hierarchy
1. **Primary**: Full Gemini analysis with retry logic
2. **Secondary**: Fallback analysis with random comment selection
3. **Tertiary**: Manual confirmation allows user override
4. **Final**: Skip/quit options prevent forced interactions

## 🔒 Safety Features

### Instagram Guidelines Compliance
- **Human-like Delays**: Random intervals between actions
- **Rate Limiting**: Breaks after every 5 users
- **Natural Behavior**: Mimics human scrolling and interaction patterns
- **Error Handling**: Graceful recovery from connection issues
- **Anti-Detection**: Unique Chrome profiles and CDP commands

### User Protection
- **Duplicate Prevention**: Won't message the same user twice (session + persistent tracking)
- **Content Filtering**: Skips inappropriate or negative content
- **Manual Confirmation**: Every message reviewed before sending
- **Screenshot Logging**: Visual confirmation of all interactions

## 🛠️ Configuration Options

### Modify CONFIG dictionary in the script:

```python
CONFIG = {
    "instagram_url": "https://www.instagram.com",
    "chromedriver_path": "C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe",
    "results_dir": "potential_clients_results",
    "analytics_file": "app\analytics_data_good.json"
}
```

## 🔍 Key Improvements from Integration

### Enhanced Story Processing:
- **Pause Monitoring**: Background thread maintains story pause state
- **Verified Screenshots**: Takes screenshots only when story is properly paused
- **Username Extraction**: Multiple methods to extract usernames from stories
- **Comment Box Detection**: Fast detection of reply capability

### Improved User Experience:
- **Manual Confirmation**: Review every message before sending
- **Edit Capability**: Modify AI-generated messages
- **Learning System**: Bot improves based on user corrections
- **Performance Stats**: Track correction rates and success metrics

### Better Analytics:
- **SQLite Integration**: Stores conversation history in main database
- **Session Persistence**: Tracks users across multiple runs
- **Correction Tracking**: Learns from user edits to improve prompts

## 🔄 Workflow Summary

1. **Initialize**: Load processed users, setup Chrome, login to Instagram
2. **Get Targets**: Read high-potential clients from analytics database
3. **Process Each User**:
   - Navigate to profile
   - Look for active stories
   - If story found: pause → screenshot → analyze → confirm → send
   - If no story: generate fallback DM and send
   - Track interaction in analytics
4. **Cleanup**: Save processed users, close browser, cleanup resources

---

**Created for Shannon's Coco's Connected Fitness Business**
*Fully integrated story analysis and client targeting system* 