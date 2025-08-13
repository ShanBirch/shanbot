# Shannon Bot - Instagram Automation & Analytics Suite

## Overview
Shannon Bot is a comprehensive Instagram automation and analytics suite designed to manage Instagram interactions, track conversations, analyze engagement, and provide detailed analytics through a dashboard interface. The system combines automated messaging, conversation analysis, and data visualization to create an efficient social media management tool.

## Core Components

### 1. Instagram Automation Bot (`followersbot.py`)
The main Instagram automation script that handles:
- Automated Instagram login and session management
- Message sending and interaction with followers
- Profile analysis using Gemini AI
- Multi-photo analysis with conversation topic extraction
- Smart follow-up system
- Integration with Google Sheets for data tracking
- Error handling and recovery mechanisms

Key Features:
- Intelligent message composition based on profile analysis
- Comprehensive profile analysis examining multiple photos
- Conversation topic extraction for better engagement
- Rate limiting and daily message caps
- Automated error recovery
- Session persistence
- Screenshot-based debugging
- Progress tracking

### 2. Analytics Dashboard (`analytics_dashboard.py`)
A Streamlit-based dashboard that provides:
- Real-time conversation metrics
- User engagement analysis
- Conversation topic analysis and frequency
- Conversion tracking
- Message pattern analysis
- Follow-up management
- Data export capabilities

Key Features:
- Interactive data visualization
- User categorization
- Conversion funnel analysis
- Message milestone tracking
- Pattern recognition for successful conversions
- Topic analysis for better engagement strategies

### 3. Conversation Analytics Integration (`conversation_analytics_integration.py`)
Backend analytics system that:
- Tracks conversation metrics
- Analyzes message patterns
- Categorizes user engagement
- Manages data persistence
- Tracks conversation topics from profile analysis
- Provides API endpoints for analytics

### 4. ManyChat Webhook Integration (`manychat_webhook_fullprompt.py`)
Handles integration with ManyChat for:
- Webhook processing
- Conversation management
- User data handling
- Analytics tracking
- Conversation topics utilization in AI prompts
- Custom field management

## New Features

### Multi-Photo Analysis
The Instagram bot now analyzes multiple photos from a user's profile instead of just the most recent one:
- Captures up to 6 photos from a user's profile
- Uses different analysis prompts for the primary (most recent) photo vs. older photos
- Extracts potential conversation topics from all photos
- Creates a comprehensive profile understanding

### Conversation Topics Extraction
The system now extracts and utilizes conversation topics:
- Identifies up to 5 unique topics from analyzing multiple profile photos
- Stores topics in analytics for future reference
- Integrates topics into ManyChat AI prompts for more personalized messaging
- Tracks topic frequency for identifying common interests among your audience

### Enhanced Analytics
- Topic frequency tracking shows the most common interests among your audience
- Topics are stored with user data for personalized follow-ups
- Dashboard displays popular topics for better content strategy

## Setup Instructions

### Prerequisites
```bash
# Required Python version
Python 3.8+

# Required packages
selenium
streamlit
pandas
matplotlib
google-generativeai
fastapi
pydantic
```

### Environment Setup
1. Install Chrome and ChromeDriver:
   ```bash
   # Windows (using chocolatey)
   choco install chromedriver
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure API Keys:
   - Set up Gemini API key
   - Configure Google Sheets credentials
   - Set up ManyChat webhook credentials

### Configuration Files
1. Create necessary credential files:
   - `sheets_credentials.json` for Google Sheets
   - Update API keys in respective scripts

2. Configure paths in scripts:
   - Update ChromeDriver path in `followersbot.py`
   - Set analytics file path in `analytics_dashboard.py`
   - Configure webhook URLs in ManyChat integration

## Usage Instructions

### Running the Instagram Bot
```bash
# Basic usage
python followersbot.py

# With custom settings
python followersbot.py --reset --daily-limit 300 --followers-list custom_list.txt
```

### Starting the Analytics Dashboard
```bash
streamlit run analytics_dashboard.py
```

### Managing Webhooks
1. Configure webhook endpoints in ManyChat
2. Start the FastAPI server:
   ```bash
   uvicorn manychat_webhook_fullprompt:app --host 0.0.0.0 --port 8000
   ```

## Features

### Instagram Bot Features
- Automated login and session management
- Smart message composition
- Multi-photo profile analysis
- Conversation topics extraction
- Follow-up system
- Error recovery
- Progress tracking
- Screenshot-based debugging
- Google Sheets integration

### Analytics Dashboard Features
- Real-time metrics
- User categorization
- Conversation analysis
- Topic frequency analysis
- Pattern recognition
- Follow-up management
- Data visualization
- Export capabilities

### Analytics Integration Features
- Message pattern analysis
- Engagement tracking
- Conversion analysis
- Topic tracking and analysis
- API endpoints
- Data persistence

## Security Considerations
- API keys and credentials are stored securely
- Rate limiting implemented
- Error handling for sensitive operations
- Session management security
- Data persistence security

## Maintenance

### Daily Operations
1. Monitor the bot's operation
2. Check analytics dashboard
3. Review error logs
4. Manage follow-ups
5. Export data regularly

### Troubleshooting
- Check screenshot directory for visual debugging
- Review log files
- Monitor analytics for anomalies
- Verify API credentials
- Check ChromeDriver compatibility

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License
Proprietary - All rights reserved

## Support
For support, please contact the development team.

## Changelog
- Initial release: Basic bot functionality
- Added analytics dashboard
- Integrated ManyChat webhooks
- Added conversation analytics
- Implemented follow-up system
- Added multi-photo analysis and conversation topics
- Enhanced webhook integration with topics

## Future Enhancements
- Enhanced AI analysis
- Advanced pattern recognition
- Expanded analytics capabilities
- Improved conversion tracking
- Additional integration options
- Topic-based engagement strategies

## Notes
- Regular updates recommended
- Monitor Instagram's terms of service
- Keep API keys updated
- Backup data regularly
- Review analytics periodically

ANTHROPIC_API_KEY=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

# Shanbot Dashboard

A comprehensive dashboard for managing user interactions and analytics.

## Components

### 1. Main Dashboard (`dashboard.py`)
The main entry point with navigation to different sections:
- Overview
- User Profiles
- Analytics
- Daily Report

### 2. User Profiles (`user_profile.py`)
Focused on user understanding and profiling:
- Personality traits
- Interests
- Lifestyle information
- Conversation starters
- Message history

### 3. Analytics Dashboard (`app/analytics_dashboard.py`)
Detailed analytics and interaction management:
- Conversation metrics
- Message sending functionality
- Engagement tracking
- Follow-up management

## How to Use

1. **View User Profiles**:
   ```bash
   streamlit run dashboard.py
   ```
   Then select "User Profiles" from the navigation menu.

2. **Access Full Analytics**:
   ```bash
   streamlit run app/analytics_dashboard.py
   ```
   This provides access to all analytics features.

3. **Process Analytics Data**:
   ```bash
   python app/split_analytics_inclusive.py
   ```
   Run this first to process user data into individual files.

## File Structure
```
shanbot/
├── dashboard.py           # Main dashboard entry point
├── user_profile.py       # User profile display module
├── app/
│   ├── analytics_dashboard.py     # Analytics functionality
│   ├── split_analytics_inclusive.py # Data processing
│   └── by_user/         # Individual user data files
```

## Notes
- The analytics functionality is currently being integrated into the main dashboard
- For full analytics features, use `analytics_dashboard.py` directly
- User profiles show processed data from individual JSON files in `by_user/`


