# Instagram Story Bot

An automated Instagram bot that interacts with stories, analyzes content using Gemini AI, and saves data to Google Sheets.

## Features

- Automated Instagram story browsing
- AI-powered content analysis using Gemini
- Automatic story interaction and commenting
- Google Sheets integration for data storage
- Anti-detection measures for safe automation
- Human-like behavior simulation
- Error handling and retry mechanisms

## Prerequisites

- Python 3.x
- Chrome browser
- ChromeDriver
- Google Cloud Project with Sheets API enabled
- Instagram account
- Gemini API key

## Required Python Packages

```bash
pip install selenium
pip install openai
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install google-generativeai
```

## Configuration

### Instagram Credentials
Located in `story1.py`:
```python
self.username = "cocos_connected"
self.password = "Shannonb3"
```

### Google Sheets Setup
1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create service account and download credentials
4. Place credentials file at: `C:\Users\Shannon\OneDrive\Desktop\shanbot\sheets_credentials.json`
5. Share your Google Sheet with the service account email

### Gemini API
Located in `story1.py`:
```python
self.gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
```

## Google Sheet Structure

The bot interacts with a Google Sheet named "Lead Chat":
- Column A: Instagram Usernames
- Column B: Story Descriptions and Comments

## Usage

1. Ensure all prerequisites are installed
2. Configure credentials and API keys
3. Run the script:
```bash
python story1.py
```

## Functionality

### Story Processing
1. Logs into Instagram
2. Finds non-live stories
3. Takes screenshots of stories
4. Analyzes content using Gemini AI
5. Generates appropriate comments
6. Saves data to Google Sheets

### Data Storage
- Checks for existing usernames in column A
- Updates column B with new descriptions and comments
- Creates new rows for new usernames

### Safety Features
- Random delays between actions
- Anti-detection measures
- Error handling and retries
- Session management
- Rate limiting

## Error Handling

The script includes comprehensive error handling for:
- Network issues
- Instagram API changes
- Browser crashes
- Invalid sessions
- API rate limits

## Logging

Logs are saved to `instagram_bot_debug.log` with:
- Timestamps
- Error messages
- Success confirmations
- Processing statistics

## Limitations

- Maximum stories processed before restart: 50
- Maximum consecutive failures: 5
- Maximum stories without success: 30
- Maximum tracked usernames: 1000

## File Structure

```
shanbot/
├── scripts/
│   ├── story1.py              # Main bot script
│   └── sheets_integration.py  # Google Sheets handler
├── sheets_credentials.json    # Google API credentials
└── instagram_bot_debug.log    # Debug log file
```

## Notes

- The bot uses human-like behavior to avoid detection
- Screenshots are automatically deleted after processing
- Processed usernames are tracked to avoid duplicates
- The script can be safely interrupted with Ctrl+C

## Troubleshooting

If you encounter issues:
1. Check the debug log file
2. Verify all credentials are correct
3. Ensure ChromeDriver is up to date
4. Check Google Sheets permissions
5. Verify API keys are valid

## Security

- Credentials are stored in the script
- API keys are stored in the script
- Service account credentials are stored in a separate file
- No sensitive data is logged

## Support

For issues or questions, please refer to the debug log file or contact the developer. 