# Shanbot AI Assistant Development Guide
*Companion to System Architecture - Optimized for AI Development Context*

## 🎯 Critical Context for AI Assistants

### Business Goals & User Journey
- **Shannon's Mission**: Scale 1-on-1 fitness coaching from 11 to 30+ clients through AI automation
- **Target Audience**: Plant-based fitness women (25-40 years old)
- **Revenue Model**: Free challenge → Trial (28 days) → Paying client ($200-400/month)
- **Shannon's Voice**: Casual Australian ("Heya!", "How's things?", "Been training much?")

### Key Development Constraints
- **Response Length**: ALL AI responses must be 1-15 words (Shannon's authentic style)
- **Instagram Limits**: 50 DMs/day, 75 follows/day
- **Database**: SQLite primary storage (`app/analytics_data_good.sqlite`)
- **AI Model**: 3-tier Gemini fallback system (pro → flash-thinking → flash-standard)

## 💻 Critical Code Patterns

### 1. Database Operations (ALWAYS Use This Pattern)
```python
def database_operation(param: str):
    conn = None
    try:
        conn = sqlite3.connect("app/analytics_data_good.sqlite")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM table WHERE field = ?", (param,))
        return cursor.fetchone()
    except Exception as e:
        logger.error(f"Database error in {function_name}: {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()
```

### 2. AI Response Generation (ALWAYS Use Fallback)
```python
# 3-tier fallback system - CRITICAL for reliability
GEMINI_MODEL_PRO = "gemini-2.5-pro-exp-03-25"           # Primary
GEMINI_MODEL_FLASH = "gemini-2.0-flash-thinking-exp-01-21"  # Fallback 1  
GEMINI_MODEL_FLASH_STANDARD = "gemini-2.0-flash"        # Fallback 2

async def call_gemini_with_retry(model_name: str, prompt: str, retry_count: int = 0):
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        if "429" in str(e) and retry_count < 3:  # Rate limit
            if model_name == GEMINI_MODEL_PRO:
                await asyncio.sleep(16)  # Wait 16 seconds
                return await call_gemini_with_retry(GEMINI_MODEL_FLASH, prompt, retry_count + 1)
            # Continue fallback chain...
```

### 3. Instagram Automation Safety Pattern
```python
# ALWAYS include these safety features for Instagram automation
def instagram_action():
    try:
        # Random delay between actions (30-90 seconds)
        delay = random.randint(30, 90)
        time.sleep(delay)
        
        # Multiple selector fallbacks
        selectors = [
            'button[aria-label="Follow"]',
            'button:contains("Follow")',
            '[data-testid="follow-button"]'
        ]
        
        for selector in selectors:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                element.click()
                return True
            except TimeoutException:
                continue
                
        return False
    except Exception as e:
        logger.error(f"Instagram automation error: {e}")
        return False
```

### 4. Response Length Validation (CRITICAL)
```python
def validate_response_length(response: str) -> bool:
    """ALL Shannon responses must be 1-15 words"""
    word_count = len(response.split())
    if word_count > 15:
        logger.warning(f"Response too long: {word_count} words")
        return False
    return True

def generate_shannon_response(prompt: str) -> str:
    response = call_gemini_with_retry(GEMINI_MODEL_PRO, prompt)
    
    # ALWAYS validate length
    if not validate_response_length(response):
        # Regenerate with explicit length constraint
        length_prompt = f"{prompt}\n\nCRITICAL: Response must be exactly 1-15 words maximum."
        response = call_gemini_with_retry(GEMINI_MODEL_FLASH, length_prompt)
    
    return response
```

## 🗂️ File Dependencies & Relationships

### Core Processing Chain
```
Instagram DM → ManyChat webhook → webhook0605.py → 
webhook_handlers.py → prompts.py → Gemini API → 
dashboard_sqlite_utils.py → Response back to Instagram
```

### Dashboard Module Dependencies
```
dashboard.py (main hub)
├── user_profiles.py (user management & bulk operations)
├── followup_manager.py (message queuing & Instagram automation)
├── checkins_manager.py (automated Monday/Wednesday check-ins)
├── response_review.py (AI response review queue)
├── analytics_overview.py (business metrics)
├── dashboard_sqlite_utils.py (database layer)
└── shared_utils.py (common functions)
```

### Instagram Automation Chain
```
new_leads table → get_high_potential_clients.py → 
follow_users.py (25/day) → dm_strategy.py (personalized DMs) → 
followup_manager.py (ongoing DMs) → webhook system (responses)
```

### Weekly Check-in Automation (4-Step Process)
```
Step 1: checkin_good_110525.py (Trainerize data extraction)
Step 2: update_with_set_by_set_progressions_clean.py (workout progression)
Step 3: simple_blue_video.py (progress video creation)
Step 4: send_checkin.py (YouTube upload + Trainerize delivery)
```

## 🗄️ Database Schema (SQLite)

### Core Tables You'll Work With
```sql
-- Main conversation storage
conversation_history (
    ig_username TEXT,           -- Instagram username
    message_type TEXT,          -- 'user' or 'ai'  
    message_text TEXT,          -- Message content
    timestamp TEXT,             -- ISO timestamp
    context_data TEXT           -- JSON metadata
)

-- AI response review queue
response_review_queue (
    id INTEGER PRIMARY KEY,
    ig_username TEXT,
    user_message TEXT,
    ai_response TEXT,
    status TEXT,                -- 'pending', 'approved', 'discarded'
    prompt_type TEXT,           -- 'general_chat', 'member_chat', etc.
    created_at TEXT
)

-- Lead generation tracking
new_leads (
    username TEXT PRIMARY KEY,
    hashtag_found TEXT,         -- Source hashtag for personalization
    followed_at TEXT,           -- When we followed them
    dm_sent_at TEXT,           -- When we DMed them
    follow_status TEXT,         -- 'followed', 'failed', etc.
    status TEXT                 -- 'new', 'contacted', 'converted'
)

-- A/B testing for conversation strategies  
conversation_strategy_log (
    username TEXT,
    strategy TEXT,              -- 'rapport_first' or 'direct'
    is_fresh_vegan INTEGER,     -- 0 or 1
    timestamp TEXT
)
```

### Common Query Patterns
```python
# Get user conversation history
cursor.execute("""
    SELECT message_type, message_text, timestamp 
    FROM conversation_history 
    WHERE ig_username = ? 
    ORDER BY timestamp DESC LIMIT 10
""", (username,))

# Add message to history
cursor.execute("""
    INSERT INTO conversation_history 
    (ig_username, message_type, message_text, timestamp)
    VALUES (?, ?, ?, ?)
""", (username, message_type, message_text, datetime.now().isoformat()))

# Get pending reviews
cursor.execute("""
    SELECT * FROM response_review_queue 
    WHERE status = 'pending' 
    ORDER BY created_at ASC
""")
```

## ⚙️ Environment Configuration

### Required Environment Variables
```bash
# AI Processing (REQUIRED)
GEMINI_API_KEY=your_gemini_api_key_here

# Instagram Automation (REQUIRED)
INSTAGRAM_USERNAME=cocos_connected
INSTAGRAM_PASSWORD=your_instagram_password

# ManyChat Integration (REQUIRED)
MANYCHAT_API_KEY=your_manychat_api_key

# Trainerize Integration (REQUIRED) 
TRAINERIZE_USERNAME=shannonbirch@cocospersonaltraining.com
TRAINERIZE_PASSWORD=cyywp7nyk2

# Optional Services
PERPLEXITY_API_KEY=your_perplexity_key  # For research features
```

### Critical File Paths
```python
# Database
DB_PATH = "app/analytics_data_good.sqlite"

# Instagram automation
FOLLOWUP_QUEUE_PATH = "followup_queue.json"
CHROME_PROFILE_BASE = "chrome_profile_"

# Analytics backup
ANALYTICS_JSON_PATH = "app/analytics_data_good.json"

# Check-in system
PROGRESSION_DATA_PATH = "set_by_set_progressions_fixed.json"
OUTPUT_DIR = "output/"
```

## 🚀 Common Development Tasks

### Adding New AI Conversation Prompts
1. **File**: `app/prompts.py`
2. **Pattern**: Follow existing template structure with Shannon's voice
3. **Integration**: Reference in `webhook_handlers.py` build functions
4. **Testing**: Use Response Review Queue in dashboard for validation

### Modifying Dashboard Features
1. **Structure**: Create new module in `app/dashboard_modules/`
2. **Import**: Add to `dashboard.py` navigation tabs
3. **Data**: Use `dashboard_sqlite_utils.py` for database operations
4. **UI**: Follow Streamlit patterns (tabs, columns, expanders)

### Instagram Automation Changes
1. **Core**: Modify `followup_manager.py` for DM sending
2. **Strategy**: Update `dm_strategy.py` for outreach templates
3. **Safety**: ALWAYS respect rate limits (50 DMs/day, 75 follows/day)
4. **Testing**: Use preview functions before live deployment

### AI Response Logic Updates
1. **File**: `webhook_handlers.py` → `build_*_prompt()` functions
2. **Length**: MAINTAIN 1-15 word response limit
3. **Personalization**: Use `regenerate_with_enhanced_context()`
4. **Fallback**: IMPLEMENT 3-tier Gemini model fallback

## 🐛 Troubleshooting Patterns

### Dashboard Won't Start
```bash
# Check port availability
netstat -ano | findstr :8501

# Kill existing processes
taskkill /F /IM streamlit.exe  

# Start with fresh session
cd app/dashboard_modules
python -m streamlit run dashboard.py --server.headless true
```

### Instagram Automation Blocked
1. **Rate Limits**: Check daily limits (50 DMs, 75 follows)
2. **Delays**: Ensure 30-90 second delays between actions
3. **Selectors**: Instagram changes selectors frequently
4. **Chrome Profile**: Try different profile if blocked

### AI Responses Not Generating
1. **API Key**: Verify `GEMINI_API_KEY` environment variable
2. **Rate Limits**: 429 errors → wait 16 seconds, try fallback model
3. **Prompts**: Check prompt length under token limits
4. **Models**: Test different models if one is down

### Database Errors
```sql
-- Check database integrity
PRAGMA integrity_check;

-- Backup before any repairs
.backup backup_YYYYMMDD.sqlite

-- Clean old review queue items
DELETE FROM response_review_queue 
WHERE status = 'approved' AND created_at < datetime('now', '-7 days');
```

## 📋 Daily Operations Checklist

### Morning Routine
1. Check dashboard notifications for trial signups
2. Run outreach: follow 25 new prospects
3. Review and send DMs to yesterday's follows
4. Approve/edit AI responses in review queue

### Weekly Routine  
1. **Wednesday**: Run full check-in workflow (4 automated steps)
2. **Data**: Export analytics backup
3. **Health**: Check error logs and performance
4. **A/B Testing**: Review conversation strategy results

## 🎨 Shannon's Communication Style Guide

### Tone & Voice
- **Casual**: "Heya!", "How's things?", "Been training much?"
- **Supportive**: Never preachy, always encouraging
- **Authentic**: Real Australian personality, not robotic
- **Concise**: 1-15 words maximum per response

### Message Examples by Context
```python
# Monday encouragement
"Goooooood Morning! Ready for the week?"
"Morning! How's your week starting?"

# Wednesday check-ins  
"Heya! How's your week going?"
"Hey hey! How's the week treating you?"

# Follow-up messages
"hey! been thinking about [topic]..."
"heya! how's things been? was just thinking about [topic]..."

# Bio-driven personalization
if user_interests.includes("hiking"):
    "Been on any good hikes lately?"
elif user_interests.includes("cooking"):
    "Been cooking anything exciting?"
```

### Conversation Flow Stages
1. **Fresh Lead (0-5 msgs)**: Build rapport, plant-based connection
2. **Engaged Prospect (5-15 msgs)**: Qualify fitness goals, build trust
3. **Trial Member (28 days)**: Structured program with regular check-ins
4. **Paying Client (ongoing)**: Advanced coaching with progress tracking

## 🔧 System Integration Points

### ManyChat Integration
- **Webhook**: Receives Instagram DMs via POST to `/webhook/manychat`
- **Fields**: Updates user conversation state and journey stage
- **Delivery**: Sends responses back through ManyChat API

### Trainerize Integration
- **Data Extraction**: Selenium automation for client progress data
- **Program Updates**: API calls for workout progression
- **Calendar**: Delivery scheduling for check-in videos

### Instagram Direct Automation
- **Following**: Selenium WebDriver with stealth settings
- **DMing**: Direct Instagram automation bypassing ManyChat
- **Rate Limiting**: Respect platform limits to avoid blocks

This guide provides AI assistants with the essential context needed for effective development work on the Shanbot system. 