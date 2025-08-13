# Shanbot Complete System Architecture
*Last Updated: January 2025*

## 🎯 Business Context & Goals (AI Assistant Priority Section)

### Shannon's Fitness Coaching Business
- **Primary Goal**: Scale 1-on-1 fitness coaching through AI automation
- **Target Audience**: Plant-based fitness enthusiasts, particularly women 25-40
- **Business Model**: 
  - Free 28-day challenges → Trial members → Paying clients ($200-400/month)
  - Current: 11 paying clients, targeting 20-30 clients
  - Weekly check-ins (Mon encouragement, Wed full analysis, Sat reports)

### Shannon's Communication Style (Critical for AI Responses)
- **Tone**: Casual, friendly Australian ("Heya!", "How's things?", "Been training much?")
- **Personality**: Authentic, supportive, knowledgeable but not preachy
- **Message Length**: Typically 1-15 words for initial responses
- **Examples**: 
  - Monday: "Goooooood Morning! Ready for the week?"
  - Wednesday: "Heya! How's your week going?"
  - Follow-ups: "hey! been thinking about [topic]..."

### Key User Journey Stages
1. **Fresh Lead** (0-5 messages): Building rapport, plant-based connection
2. **Engaged Prospect** (5-15 messages): Qualifying fitness goals
3. **Trial Member** (28 days): Structured program with check-ins
4. **Paying Client** (ongoing): Advanced coaching with progress tracking

## 🏗️ System Architecture

### Core Entry Points

#### A. Main Webhook Handler (`webhook0605.py`)
- **Primary Function**: Central message processing hub
- **Responsibilities**:
  - Receives Instagram messages via ManyChat webhook
  - Processes audio/video/image content
  - Routes messages to appropriate handlers
  - Manages response timing and buffering
  - Handles conversation flow detection
- **Key Features**:
  - Message buffering (15-second window for grouping)
  - Intelligent delay calculation based on user response time
  - Form check video analysis integration
  - Calorie tracking integration
  - Program modification requests

#### B. Application Main (`app/main.py`)
- **Primary Function**: Streamlined FastAPI application entry
- **Responsibilities**:
  - Message buffer management
  - Response scheduling
  - Analytics updates
  - ManyChat field updates

## 💻 Development Context for AI Assistants

### Critical Code Patterns & Conventions

#### Database Interaction Pattern
```python
# Standard SQLite connection pattern used throughout
def get_user_data(ig_username: str):
    conn = sqlite3.connect("app/analytics_data_good.sqlite")
    try:
        cursor = conn.cursor()
        # Always use parameterized queries
        cursor.execute("SELECT * FROM table WHERE ig_username = ?", (ig_username,))
        return cursor.fetchone()
    except Exception as e:
        logger.error(f"Database error: {e}", exc_info=True)
        return None
    finally:
        conn.close()
```

#### AI Response Generation Pattern
```python
# 3-tier fallback system for Gemini API
GEMINI_MODEL_PRO = "gemini-2.5-pro-exp-03-25"           # Primary
GEMINI_MODEL_FLASH = "gemini-2.0-flash-thinking-exp-01-21"  # Fallback 1
GEMINI_MODEL_FLASH_STANDARD = "gemini-2.0-flash"        # Fallback 2

async def call_gemini_with_retry(model_name: str, prompt: str, retry_count: int = 0):
    # Always include retry logic with model fallbacks
    # Rate limit = 429 error triggers fallback to next model
    # Max retries = 3 with exponential backoff
```

#### Message Response Pattern
```python
# ALL responses must be 1-15 words (Shannon's style)
# Use enhanced context from user bio when available
def generate_response(user_message: str, user_context: dict):
    # 1. Get user bio/interests for personalization
    # 2. Check conversation history for context
    # 3. Apply appropriate prompt template
    # 4. Ensure response fits Shannon's voice (1-15 words)
```

### Key File Dependencies & Relationships

#### Core Processing Chain
```
Instagram DM → ManyChat → webhook0605.py → 
webhook_handlers.py → prompts.py → 
Gemini API → dashboard_sqlite_utils.py → Response
```

#### Dashboard Module Dependencies
```
dashboard.py (main hub)
├── user_profiles.py (user management)
├── followup_manager.py (message queuing)
├── checkins_manager.py (automated check-ins)
├── response_review.py (AI response review)
├── dashboard_sqlite_utils.py (data layer)
└── shared_utils.py (common functions)
```

#### Instagram Automation Chain
```
get_high_potential_clients.py → follow_users.py → 
dm_strategy.py → followup_manager.py → 
conversation flows back to webhook system
```

### Database Schema (SQLite: `app/analytics_data_good.sqlite`)

#### Core Tables
```sql
-- Main user conversations and metrics
conversation_history (
    ig_username TEXT,
    message_type TEXT,  -- 'user' or 'ai'
    message_text TEXT,
    timestamp TEXT
)

-- Response review queue for AI oversight
response_review_queue (
    ig_username TEXT,
    user_message TEXT,
    ai_response TEXT,
    status TEXT,  -- 'pending', 'approved', 'discarded'
    context_data TEXT
)

-- Lead generation and outreach tracking
new_leads (
    username TEXT,
    hashtag_found TEXT,
    followed_at TEXT,
    dm_sent_at TEXT,
    status TEXT
)

-- A/B testing for conversation strategies
conversation_strategy_log (
    username TEXT,
    strategy TEXT,  -- 'rapport_first' or 'direct'
    is_fresh_vegan INTEGER,
    timestamp TEXT
)
```

### Configuration Management

#### Environment Variables (Required)
```bash
# AI Processing
GEMINI_API_KEY=your_gemini_api_key_here

# Instagram Automation  
INSTAGRAM_USERNAME=cocos_connected
INSTAGRAM_PASSWORD=your_instagram_password

# ManyChat Integration
MANYCHAT_API_KEY=your_manychat_api_key

# Trainerize Integration
TRAINERIZE_USERNAME=shannonbirch@cocospersonaltraining.com
TRAINERIZE_PASSWORD=cyywp7nyk2

# Optional: External Services
PERPLEXITY_API_KEY=your_perplexity_key  # For research features
```

#### Critical File Paths
```python
# Database
DB_PATH = "app/analytics_data_good.sqlite"

# Followup queue (for Instagram automation)
FOLLOWUP_QUEUE_PATH = "followup_queue.json"

# Chrome profiles (for Instagram automation)
CHROME_PROFILE_BASE = "chrome_profile_"

# Analytics data backup
ANALYTICS_JSON_PATH = "app/analytics_data_good.json"
```

## 🚀 Development Workflow & Common Tasks

### Setting Up Development Environment
```bash
# 1. Install Python dependencies
pip install streamlit selenium fastapi uvicorn google-generativeai

# 2. Set environment variables
# Create .env file with keys above

# 3. Start dashboard for development
cd app/dashboard_modules
python -m streamlit run dashboard.py --server.headless true

# 4. Start webhook for testing (separate terminal)
cd ../../
python webhook0605.py

# 5. Start ngrok tunnel for ManyChat webhook
ngrok http 8000
```

### Common Development Scenarios

#### Adding New Conversation Prompts
1. **Location**: Add to `app/prompts.py`
2. **Pattern**: Follow existing template structure
3. **Integration**: Reference in `webhook_handlers.py`
4. **Testing**: Use Response Review Queue in dashboard

#### Modifying AI Response Logic
1. **File**: `webhook_handlers.py` → `build_*_prompt()` functions
2. **Pattern**: Always maintain 1-15 word response limit
3. **Context**: Use `regenerate_with_enhanced_context()` for personalization
4. **Fallback**: Implement 3-tier Gemini model fallback

#### Adding Dashboard Features
1. **Structure**: Create new module in `app/dashboard_modules/`
2. **Import**: Add to `dashboard.py` main navigation
3. **Data**: Use `dashboard_sqlite_utils.py` for database operations
4. **UI**: Follow Streamlit patterns with tabs/columns/expanders

#### Instagram Automation Changes
1. **Core**: Modify `followup_manager.py` for DM sending
2. **Strategy**: Update `dm_strategy.py` for outreach messages
3. **Safety**: Always respect Instagram rate limits (50 DMs/day)
4. **Testing**: Use preview functions before live deployment

### Error Handling Patterns

#### Database Errors
```python
# Always wrap database operations
try:
    conn = sqlite3.connect(DB_PATH)
    # operations here
except Exception as e:
    logger.error(f"Database error in {function_name}: {e}", exc_info=True)
    return None  # or appropriate fallback
finally:
    if conn:
        conn.close()
```

#### Instagram Automation Errors
```python
# Selenium operations need robust error handling
try:
    element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    element.click()
except TimeoutException:
    logger.error(f"Element not found: {selector}")
    return False
except Exception as e:
    logger.error(f"Instagram automation error: {e}", exc_info=True)
    return False
```

#### AI API Errors
```python
# Use the 3-tier fallback system
async def call_gemini_with_retry(model_name: str, prompt: str, retry_count: int = 0):
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        if "429" in str(e) and retry_count < MAX_RETRIES:
            # Rate limit → fallback to next model
            if model_name == GEMINI_MODEL_PRO:
                return await call_gemini_with_retry(GEMINI_MODEL_FLASH, prompt, retry_count + 1)
        # Handle other fallback scenarios
```

## 🔧 Operational Procedures

### Daily Operations Checklist
1. **Morning**: Check dashboard notifications for trial signups
2. **Lead Gen**: Run outreach system (follow 25, DM previous day's follows)
3. **Response Review**: Approve/edit queued AI responses in dashboard
4. **Check-ins**: Monitor Monday/Wednesday automated check-ins
5. **Analytics**: Review engagement metrics and conversion rates

### Weekly Operations Checklist
1. **Wednesday**: Full client check-in workflow (4-step automated process)
2. **Data Backup**: Export analytics data for backup
3. **System Health**: Check error logs and performance metrics
4. **A/B Testing**: Review conversation strategy performance

### Troubleshooting Guide

#### Dashboard Won't Start
```bash
# Check if port is available
netstat -ano | findstr :8501

# Kill existing Streamlit processes
taskkill /F /IM streamlit.exe

# Restart with fresh session
python -m streamlit run dashboard.py --server.headless true
```

#### Instagram Automation Blocked
1. **Check rate limits**: Max 50 DMs/day, 75 follows/day
2. **Review delays**: Ensure 30-90 second delays between actions
3. **Update Chrome**: Instagram frequently changes selectors
4. **Check profile**: May need to use different Chrome profile

#### AI Responses Not Generating
1. **Check API key**: Verify GEMINI_API_KEY in environment
2. **Rate limits**: 429 errors → wait 16 seconds, try fallback model
3. **Prompt length**: Ensure prompts under token limits
4. **Model availability**: Try different model if one is down

#### Database Issues
```sql
-- Check database integrity
PRAGMA integrity_check;

-- Backup before repairs
.backup backup_YYYYMMDD.sqlite

-- Common cleanup queries
DELETE FROM response_review_queue WHERE status = 'approved' AND created_at < datetime('now', '-7 days');
```

### Security & Compliance Notes
- **Instagram Credentials**: Store securely, rotate periodically
- **API Keys**: Never commit to version control
- **User Data**: GDPR compliance for conversation storage
- **Rate Limiting**: Respect all platform limits to avoid blocks

### System Architecture

#### Message Processing Pipeline

##### A. Webhook Handlers (`webhook_handlers.py`)
- **Core Functions**:
  - `get_user_data()`: Retrieves user context from database
  - `update_analytics_data()`: Updates conversation history
  - `build_member_chat_prompt()`: Constructs AI prompts
  - `call_gemini_with_retry()`: AI response generation
  - `send_manychat_message()`: Message delivery

##### B. Message Buffer System
- **Purpose**: Groups rapid-fire messages for context
- **Implementation**:
  ```python
  # Messages buffered for 15 seconds
  BUFFER_WINDOW = 15
  # Process when buffer times out or conversation ends
  ```

##### C. AI Response Generation
- **Models Used**:
  - `gemini-2.5-pro-exp-03-25`: Complex analysis and responses
  - `gemini-2.0-flash-thinking-exp-01-21`: Fast standard responses
  - `gemini-2.0-flash`: Backup/fallback model

#### Conversation Management

##### A. Prompt System (`app/prompts.py`)
- **Templates Available**:
  - `COMBINED_CHAT_AND_ONBOARDING_PROMPT_TEMPLATE`: Main conversation handler
  - `MEMBER_GENERAL_CHAT_PROMPT_TEMPLATE`: Existing client interactions
  - `CHECKIN_PROMPT_TEMPLATE_WED`: Wednesday check-ins
  - `CHECKIN_PROMPT_TEMPLATE_MON`: Monday encouragement
  - `STORY_COMMENT_REPLY_PROMPT_TEMPLATE`: Instagram story responses

##### B. Conversation Flow States
1. **Lead Engagement**: Initial contact and rapport building
2. **Onboarding**: Information collection for trial signup
3. **Trial Management**: Structured 4-week trial period
4. **Paying Client**: Ongoing coaching relationship

##### C. Bio-Driven Personalization
- **Profile Analysis**: Extracts interests, activities, personality traits
- **Contextual Responses**: Uses bio data for relevant questions
- **Examples**:
  ```python
  # Bio-driven question selection
  if user_interests.includes("fitness"):
      question = "Been training much lately?"
  elif user_interests.includes("travel"):
      question = "Been anywhere cool lately?"
  ```

#### Client Progress System

##### A. Complete Weekly Check-in Workflow

The check-in system is a fully automated 4-step process that handles data collection through client delivery:

###### Step 1: Data Collection & Analysis (`checkin_good_110525.py`)
```bash
python checkin_good_110525.py
```
- **Primary Function**: Automated Trainerize data extraction and AI analysis
- **Process**:
  - 🤖 Automated Trainerize login using Selenium WebDriver
  - 📊 Multi-client data extraction for all 11 clients
  - 🧠 AI-powered analysis using Gemini for insights generation
- **Capabilities**:
  - **Bodyweight tracking**: Weight trends, goal progress analysis
  - **Nutrition data**: Calories, macros, eating patterns
  - **Sleep monitoring**: Hours, quality trends, recovery analysis
  - **Activity tracking**: Daily steps, activity levels, consistency
  - **Progress photos**: AI visual analysis of body composition changes
  - **Workout performance**: Exercise progression, strength gains, completion rates
- **Output**: Individual `{client_name}_fitness_wrapped_data.json` files with comprehensive analysis

###### Step 2: Goal Progression Updates (`update_with_set_by_set_progressions_clean.py`)
```bash
python update_with_set_by_set_progressions_clean.py
```
- **Primary Function**: Intelligent workout program progression
- **Process**:
  - 📈 Loads fixed progression data with individualized set goals
  - 🎯 Applies set-by-set progression algorithm (6→8→10→12→15 reps)
  - ✏️ Updates Trainerize with new workout goals
- **Features**:
  - **Individualized Set Goals**: Each set progressed independently
  - **Smart Weight Progression**: At 15 reps → increase weight, reset to 6 reps
  - **Equipment-Specific Increments**: Dumbbell vs barbell/machine progression
  - **Multi-client Processing**: Handles all 11 clients systematically
- **Output**: Updated workout programs in Trainerize with new individualized goals

###### Step 3: Progress Video Generation (`simple_blue_video.py`)
```bash
python simple_blue_video.py
```
- **Primary Function**: Personalized progress video creation
- **Process**:
  - 📁 Loads client fitness analysis JSON files
  - 🎬 Creates individualized progress videos
  - 🎨 Applies dynamic content based on achievements
- **Features**:
  - **Progress Highlights**: Weight changes, workout improvements
  - **Goal Completion Rates**: Visual progress bars and achievements
  - **Exercise Improvements**: Strength gains with technique tips
  - **Motivational Content**: Personalized encouragement and next week focus
  - **Professional Styling**: Animated transitions, blue theme, brand consistency
- **Output**: Personalized `{client_name}_progress_video.mp4` files

###### Step 4: Check-in Delivery (`send_checkin.py`)
```bash
python send_checkin.py
```
- **Primary Function**: Video delivery and client communication
- **Process**:
  - 📺 Uploads progress videos to YouTube (unlisted)
  - 📅 Schedules delivery through Trainerize calendar
  - 💬 Generates contextual messages based on progress
- **Features**:
  - **YouTube Integration**: Automated video upload with privacy controls
  - **Trainerize Scheduling**: Direct calendar integration
  - **Personalized Messaging**: AI-generated messages reflecting individual progress
  - **Link Integration**: Embedded video links with context
- **Output**: Videos delivered to clients through Trainerize with personalized messages

##### B. Weekly Schedule Integration

###### Monday Check-ins: Quick Encouragement
- **Purpose**: Motivation boost for the week ahead
- **Method**: AI-generated encouragement through ManyChat/Instagram webhook system
- **Content**: Short motivational messages using `CHECKIN_PROMPT_TEMPLATE_MON`
- **Examples**: "Ready to crush this week! 💪", "Love seeing your consistency!"

###### Wednesday Check-ins: Full Progress Review
- **Purpose**: Comprehensive progress analysis and program updates
- **Method**: Complete 4-step automated workflow
- **Content**: Full video + data analysis + updated workout goals
- **Template**: Uses `CHECKIN_PROMPT_TEMPLATE_WED` for detailed analysis

###### Saturday Check-ins: PDF Reports (External System)
- **Purpose**: Comprehensive written reports and analytics
- **Method**: External system integration
- **Content**: Detailed analytics, recommendations, and weekly summaries

##### C. Technical Workflow Architecture

```
WEEKLY CHECK-IN FLOW:

1. DATA COLLECTION
   checkin_good_110525.py → Selenium Automation → Trainerize Data → AI Analysis → JSON

2. PROGRAM UPDATES  
   update_with_set_by_set_progressions_clean.py → Fixed Progression Data → Individual Set Goals → Trainerize Updates

3. CONTENT CREATION
   simple_blue_video.py → JSON Analysis → Dynamic Video Generation → MP4 Output

4. CLIENT DELIVERY
   send_checkin.py → YouTube Upload → Trainerize Calendar → Personalized Messages
```

##### D. System Integration Features

- **🤖 Fully Automated**: End-to-end automation requiring minimal manual intervention
- **👥 Multi-client Scalability**: Processes all 11 clients systematically  
- **📊 Data-Driven Insights**: Uses real Trainerize data for accurate analysis
- **🎨 Personalized Content**: Individual videos and messages for each client
- **📈 Progressive Programming**: Intelligent workout progression based on performance
- **⏰ Scheduled Delivery**: Integrates with Trainerize calendar system
- **🔍 AI-Powered Analysis**: Computer vision for progress photos, trend analysis
- **🎯 Goal Tracking**: Automatic goal updates with set-by-set progression
- **💬 Contextual Communication**: Messages adapted to individual progress patterns

#### Instagram Engagement Automation & Lead Generation Pipeline

##### A. Complete Outreach System - 3-Phase Lead Generation

###### Phase 1: Client Identification & Following (`get_high_potential_clients.py` + `follow_users.py`)

**Client Identification System** (`get_high_potential_clients.py`)
- **Purpose**: Identifies high-potential clients from dashboard analytics
- **Process**:
  - Analyzes client potential scores from Shannon's existing system
  - Filters clients with minimum score threshold (default: 70)
  - Ranks clients by potential score (highest first)
  - Limits results to top performers (default: 25)
- **Output**: Formatted list showing client username and potential score

**Automated Following System** (`follow_users.py`)
- **Purpose**: Phase 1 outreach - follows users from potential clients database
- **Key Features**:
  - **Daily limit of 25 users** to respect Instagram limits
  - **Database Integration**: Connects to `app/analytics_data_good.sqlite`
  - **Smart Selection**: Gets unfollowed users from `new_leads` table
  - **Instagram Automation**: Uses Selenium with stealth settings
  - **Progress Tracking**: Updates database with follow status and timestamps
- **Process**:
  1. Checks daily follow count (25 max)
  2. Retrieves unfollowed users from database
  3. Logs into Instagram (cocos_connected account)
  4. Follows each user with 30-90 second delays
  5. Updates database: `followed_at` timestamp, `follow_status = 'followed'`
- **Safety Features**:
  - Human-like delays between follows
  - Robust login with multiple selector fallbacks
  - Anti-detection browser settings
  - Comprehensive error handling and logging

###### Phase 2: Strategic DM Campaign (`dm_strategy.py` + `preview_dm_strategy.py`)

**DM Strategy System** (`dm_strategy.py`)
- **Purpose**: Phase 2 outreach - sends personalized DMs to followed users after 24-48 hour delay
- **Personalization Engine**:
  - **Hashtag-based categorization**: Groups users by interests
  - **Message templates**: Shannon's authentic voice for each category
  - **Categories**: Vegan Fitness, Vegan Lifestyle, Nutrition Focused, Fitness General
- **Message Examples** (Shannon's authentic style):
  - *Vegan Fitness*: "Heya! Noticed you're into plant based fitness 🌱 How's your training going?"
  - *Vegan Lifestyle*: "Hey! Fellow vegan here 🌱 Been vegetarian since birth myself, how's your journey been?"
  - *Nutrition*: "Hey! Love your approach to nutrition 🌱 What's your biggest focus right now?"
- **Safety & Timing**:
  - **24-hour delay** after following before DMing
  - **Daily DM limit**: 20 messages maximum
  - **Database tracking**: Prevents duplicate DMs
  - **Follow status verification**: Only DMs successfully followed users

**DM Preview System** (`preview_dm_strategy.py`)
- **Purpose**: Preview and plan DM strategy before execution
- **Features**:
  - Shows personalized messages for each followed user
  - Groups users by hashtag category for review
  - Displays message templates that would be sent
  - Provides sending timeline and instructions
- **Output**: Comprehensive preview showing 23+ personalized messages ready for delivery

###### Phase 3: Conversation Management (Existing Webhook System)
- **Integration**: DM responses flow into existing webhook system
- **AI Processing**: Uses Shannon's authentic prompts for conversation flow
- **Conversion**: Leads to trial signup through established onboarding process

##### B. Follow-up Manager (`followup_manager.py`)
- **Purpose**: Ongoing Instagram DM management for established conversations
- **Features**:
  - Persistent browser session management
  - Message queue processing
  - Rate limiting (50 messages/day)
  - Response timing optimization
- **Safety Features**:
  - Human-like interaction delays
  - Anti-detection measures
  - Error recovery mechanisms

##### C. Story Engagement (`story1.py`)
- **Function**: Automated story interaction
- **Process**:
  1. Analyze story content with AI
  2. Generate contextual responses
  3. Track interaction history
  4. Maintain engagement limits

##### D. Follower Analysis (`anaylize_followers.py`)
- **Purpose**: Profile analysis for targeting
- **Capabilities**:
  - Bio extraction and analysis
  - Interest categorization
  - Engagement potential scoring
  - Background analysis integration

##### E. Complete Outreach Workflow Integration

**Daily Outreach Process**:
1. **Morning**: Run `get_high_potential_clients.py` to identify targets
2. **Follow Phase**: Execute `follow_users.py` to follow 25 new prospects
3. **Preview DMs**: Use `preview_dm_strategy.py` to review next day's DM strategy
4. **24 Hours Later**: Run `dm_strategy.py` to send personalized DMs
5. **Ongoing**: Webhook system handles conversation management and conversions

**Database Schema Integration**:
```sql
new_leads table:
- username: Instagram username
- hashtag_found: Source hashtag for personalization
- followed_at: Timestamp when user was followed
- follow_status: 'followed', 'failed', etc.
- dm_sent_at: Timestamp when DM was sent
- status: 'new', 'contacted', 'converted', etc.
```

**Safety & Compliance**:
- **Instagram Limits**: 75 follows/day, unlimited DMs to followers
- **Human-like Behavior**: Random delays, authentic messaging
- **Database Tracking**: Prevents duplicates and tracks success rates
- **Error Recovery**: Robust handling of Instagram changes and blocks

#### Analytics and Dashboard System

##### A. Main Dashboard (`app/dashboard_modules/dashboard.py`)
- **Overview Tab**: Key business metrics
- **User Profiles**: Detailed client information
- **Follow-up Manager**: Engagement scheduling
- **Check-ins Manager**: Progress monitoring
- **Response Review**: AI response quality control

##### B. Data Storage (`app/dashboard_modules/dashboard_sqlite_utils.py`)
- **Database Schema**:
  - User profiles and conversation history
  - Response review queue
  - Learning log for AI improvements
  - Workout session tracking
- **Key Functions**:
  - `load_conversations_from_sqlite()`
  - `save_metrics_to_sqlite()`
  - `add_response_to_review_queue()`

##### C. Analytics Features
- **Engagement Tracking**: Response rates, conversation length
- **Conversion Metrics**: Trial signups, payment conversions
- **Quality Control**: Response review and approval system
- **Business Intelligence**: Revenue tracking, client progression

#### Integration Systems

##### A. ManyChat Integration (`app/manychat_utils.py`)
- **Purpose**: Instagram messaging automation
- **Functions**:
  - Field updates for conversation state
  - Message delivery confirmation
  - Subscriber management

##### B. Trainerize Automation (`pb.py`)
- **Capabilities**:
  - Program building and modification
  - Client data extraction
  - Progress tracking integration
- **API Integration**: GraphQL for data retrieval

##### C. Google Sheets Integration
- **Onboarding Data**: Trial signup tracking
- **Client Information**: Program details and progress
- **Business Metrics**: Revenue and conversion tracking

## Data Flow Architecture

### 1. Incoming Message Flow
```
Instagram DM → ManyChat → Webhook (webhook0605.py) → 
Message Buffer → AI Processing → Response Generation → 
ManyChat → Instagram DM
```

### 2. Complete Check-in Data Flow
```
STEP 1: DATA COLLECTION
Trainerize → Selenium Automation (checkin_good_110525.py) → 
AI Analysis (Gemini) → JSON Data Files

STEP 2: PROGRAM UPDATES
Fixed Progression Data → update_with_set_by_set_progressions_clean.py → 
Individual Set Goals → Trainerize Updates

STEP 3: VIDEO CREATION  
JSON Data → simple_blue_video.py → 
Dynamic Content Generation → MP4 Videos

STEP 4: CLIENT DELIVERY
MP4 Videos → send_checkin.py → 
YouTube Upload → Trainerize Calendar → Client Notification
```

### 3. Complete Outreach System Flow
```
PHASE 1: CLIENT IDENTIFICATION & FOLLOWING
Dashboard Analytics → get_high_potential_clients.py → 
Potential Client Database → follow_users.py → 
Instagram Following (25/day) → Database Updates (followed_at, follow_status)

PHASE 2: STRATEGIC DM CAMPAIGN  
Database (24hr+ after follow) → preview_dm_strategy.py → 
DM Strategy Review → dm_strategy.py → 
Personalized DMs → Database Updates (dm_sent_at)

PHASE 3: CONVERSATION MANAGEMENT
DM Responses → ManyChat → Webhook (webhook0605.py) → 
AI Processing (Shannon's voice) → Trial Conversion
```

### 4. Follow-up System Flow
```
Analytics Database → Engagement Algorithm → 
Message Queue → Instagram Automation (followup_manager.py) → 
Delivery Confirmation → Analytics Update
```

## Configuration and Environment

### Required Services
1. **Google Gemini API**: AI processing
2. **ManyChat API**: Instagram messaging
3. **Instagram Account**: Direct automation
4. **Trainerize Account**: Client data access
5. **Google Sheets API**: Data integration

### File Structure
```
shanbot/
├── webhook0605.py              # Main webhook handler
├── webhook_handlers.py         # Core processing functions
├── checkin_good_110525.py      # Progress tracking system (Step 1)
├── update_with_set_by_set_progressions_clean.py # Goal progression (Step 2)
├── simple_blue_video.py        # Video generation (Step 3)
├── send_checkin.py             # Client delivery system (Step 4)
├── weekly_program_updater.py   # Trainerize workout automation
├── fix_progression_data.py     # Progression data cleanup utility
├── followup_manager.py         # Instagram automation
├── anaylize_followers.py       # Profile analysis
│
├── # === OUTREACH SYSTEM === #
├── get_high_potential_clients.py # Client identification system
├── follow_users.py             # Phase 1: Automated following (25/day)
├── dm_strategy.py              # Phase 2: Personalized DM campaign
├── preview_dm_strategy.py      # DM strategy preview and planning
│
├── app/
│   ├── main.py                 # Application entry point
│   ├── prompts.py              # AI prompt templates
│   ├── dashboard_modules/
│   │   ├── dashboard.py        # Main analytics dashboard
│   │   ├── dashboard_sqlite_utils.py # Database operations
│   │   ├── user_profiles.py    # User management
│   │   └── scheduled_followups.py # Follow-up management
│   └── analytics_data_good.sqlite # Main database
├── pb.py                       # Trainerize automation
├── set_by_set_progressions.json # Original progression data
├── set_by_set_progressions_fixed.json # Cleaned progression data
└── output/                     # Generated content (videos, JSON files)
```

## Operational Workflows

### 1. Complete Lead Generation Workflow (Outreach System)
1. **Client Identification**: Use `get_high_potential_clients.py` to identify high-potential prospects
2. **Automated Following**: Execute `follow_users.py` to follow 25 prospects/day from potential clients database
3. **DM Strategy Planning**: Preview personalized messages using `preview_dm_strategy.py`
4. **Strategic DM Campaign**: Send personalized DMs via `dm_strategy.py` 24 hours after following
5. **Conversation Management**: AI-driven responses via webhook system using Shannon's authentic voice
6. **Trial Conversion**: Structured onboarding process leading to 28-day challenge

**Daily Outreach Schedule**:
- **Morning**: Identify targets and follow 25 new prospects
- **Next Day**: Review DM strategy and send personalized messages
- **Ongoing**: Webhook system handles conversations and conversions

### 2. Traditional Lead Generation Workflow
1. **Story Engagement**: Automated story interactions using `story1.py`
2. **Follower Analysis**: Profile analysis via `anaylize_followers.py`
3. **Initial Contact**: Personalized DMs through follow-up manager
4. **Conversation Management**: AI-driven responses via webhook system
5. **Trial Conversion**: Structured onboarding process

### 2. Client Onboarding Workflow
1. **Information Collection**: Systematic data gathering via AI conversation
2. **Program Creation**: Automated workout program generation
3. **Initial Setup**: Trainerize account configuration
4. **Welcome Sequence**: Structured trial week messaging

### 3. Complete Weekly Check-in Workflow

#### Wednesday Full Check-in Process:
1. **Data Collection & Analysis** (`checkin_good_110525.py`)
   - Automated Trainerize login and multi-client data extraction
   - AI-powered analysis of bodyweight, nutrition, sleep, activity, photos, workouts
   - Individual JSON files generated with comprehensive insights

2. **Program Progression Updates** (`update_with_set_by_set_progressions_clean.py`)
   - Load fixed progression data with individualized set goals
   - Apply set-by-set progression algorithm (6→8→10→12→15 reps)
   - Update Trainerize with new workout goals for all clients

3. **Progress Video Generation** (`simple_blue_video.py`)
   - Load client fitness analysis JSON files
   - Create personalized videos with progress highlights, goals, improvements
   - Generate MP4 files with professional styling and animations

4. **Client Delivery** (`send_checkin.py`)
   - Upload progress videos to YouTube (unlisted)
   - Schedule delivery through Trainerize calendar
   - Generate personalized messages based on individual progress

#### Monday & Saturday Integration:
- **Monday**: Quick encouragement via webhook system using AI-generated motivation
- **Saturday**: PDF reports through external system integration

### 4. Follow-up Management Workflow
1. **Engagement Analysis**: User activity and response pattern analysis
2. **Message Scheduling**: Intelligent timing based on user behavior
3. **Content Generation**: Contextual follow-up messages
4. **Delivery Management**: Instagram automation with safety controls

## System Monitoring and Maintenance

### Health Checks
- **Webhook Status**: Message processing success rates
- **AI Performance**: Response quality and generation times
- **Instagram Automation**: Session health and rate limiting
- **Database Integrity**: Data consistency and backup status

### Quality Control
- **Response Review Queue**: Human oversight of AI responses
- **Learning System**: Continuous improvement through feedback
- **Error Tracking**: Comprehensive logging and error handling
- **Performance Metrics**: System speed and reliability monitoring

## Security and Compliance

### Data Protection
- **Encryption**: Sensitive data encryption at rest and in transit
- **Access Control**: Role-based access to different system components
- **Privacy Compliance**: GDPR-compliant data handling
- **Audit Logging**: Comprehensive activity tracking

### Rate Limiting
- **Instagram Limits**: 50 messages/day, human-like timing
- **API Quotas**: Gemini API usage monitoring
- **Concurrent Operations**: Controlled parallel processing
- **Error Backoff**: Progressive retry mechanisms

## Scalability and Performance

### Current Limitations
- **Instagram Rate Limits**: 50 messages/day per account
- **Selenium Dependency**: Single browser session bottleneck
- **Manual Oversight**: Some processes require human intervention

### Optimization Opportunities
- **Multi-Account Support**: Scale Instagram automation
- **API-First Approach**: Reduce Selenium dependency where possible
- **Distributed Processing**: Parallel execution for heavy workloads
- **Caching Strategy**: Improve response times and reduce API calls

## Future Development Roadmap

### Immediate Improvements
1. **Enhanced Error Handling**: More robust error recovery
2. **Performance Optimization**: Faster response generation
3. **UI/UX Improvements**: Better dashboard functionality
4. **Integration Expansion**: Additional fitness platform support

### Long-term Vision
1. **Multi-Platform Support**: Beyond Instagram engagement
2. **Advanced AI Features**: More sophisticated conversation handling
3. **Automated Program Optimization**: AI-driven program adjustments
4. **Business Intelligence**: Advanced analytics and insights

---

This architecture document provides a complete overview of the Shanbot system, enabling developers and AI assistants to understand, maintain, and extend the platform effectively. The enhanced sections provide critical context for development work, debugging, and system modifications. 