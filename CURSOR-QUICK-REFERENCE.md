# 🤖 Cursor AI Quick Reference - Shanbot System

> **Purpose**: Give AI assistants immediate context about what we're building

## What is Shanbot?
**Shannon's AI-powered fitness coaching automation system** that scales her 1-on-1 coaching business through Instagram automation and AI conversation management.

## 🎯 Key Business Context
- **Current**: 9 paying clients at $200-400/month
- **Goal**: Scale to 30+ clients through automation
- **Target**: Plant-based fitness women (25-40 years old)
- **Journey**: facebook ad → combined vegan ad response prompt → phone call - paying client

## 🗣️ Shannon's Voice (CRITICAL)
- **Tone**: Casual Australian ("Heya!", "How's things?", "Been training much?")
- **Length**: **ALL responses must be 1-15 words maximum**
- **Style**: Supportive, authentic, never preachy

## 🏗️ System Architecture at a Glance

### Main Components
1. **Instagram Automation**: Follow/DM prospects automatically
2. **AI Conversations**: Gemini-powered responses in Shannon's voice  
3. **Check-in System**: Automated weekly progress tracking for clients
4. **Analytics Dashboard**: Streamlit-based management interface

### Core Files You'll Work With
- `webhook_main.py` – Main FastAPI webhook app (current entry point; previously used `webhook0605.py`)
- `action_router.py` – Message routing and action detection logic
- `action_handlers/` – Specialized handlers actually used:
  - `action_handlers/ad_response_handler.py`
  - `action_handlers/core_action_handler.py`
  - `action_handlers/trainerize_action_handler.py`
  - `action_handlers/calorie_action_handler.py`
  - `action_handlers/form_check_handler.py`
- `services/message_buffer.py` – Message buffering and delayed processing
- `webhook_handlers.py` (root-level) – LLM calls, media analysis, prompt builders, analytics/ManyChat helpers
- `app/analytics.py` – Analytics updates
- `app/manychat_utils.py` – ManyChat field updates
- `app/prompts.py` – AI conversation templates
- Dashboard modules:
  - `app/dashboard_modules/response_review.py` – Review/edit/send; rationale; media descriptions
  - `app/dashboard_modules/dashboard_sqlite_utils.py` – DB I/O, queueing, few-shot
  - `app/dashboard_modules/dashboard.py` – Main Streamlit dashboard
  - (plus: `checkins_manager.py`, `followup_utils.py`, `notifications.py`, `user_profiles.py`, `user_management.py`, `new_leads.py`)
- `story1.py` – Important standalone script in current workflow
- `followup_manager.py` – Instagram DM automation
- `app/analytics_data_good.sqlite` – Main database

## 💻 Critical Patterns to Follow

### 1. Database Operations
```python
conn = sqlite3.connect("app/analytics_data_good.sqlite")
try:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM table WHERE field = ?", (param,))
    return cursor.fetchone()
finally:
    conn.close()
```

### 2. AI Response Generation
```python
# Fast-first fallback: flash-lite → flash-thinking → flash-standard
GEMINI_MODEL_PRO = "gemini-2.5-flash-lite"
GEMINI_MODEL_FLASH = "gemini-2.0-flash-thinking-exp-01-21"
GEMINI_MODEL_FLASH_STANDARD = "gemini-2.0-flash"
```

### 3. Response Length Validation
```python
# ALWAYS validate Shannon's response length
def validate_response_length(response: str) -> bool:
    return len(response.split()) <= 15  # MAX 15 words
```

## 🗄️ Database Tables (SQLite)
- `conversation_history` - All Instagram message history
- `response_review_queue` - AI responses awaiting approval
- `new_leads` - Lead generation and outreach tracking
- `conversation_strategy_log` - A/B testing data

## ⚙️ Required Environment Variables
```bash
GEMINI_API_KEY=your_gemini_api_key
INSTAGRAM_USERNAME=cocos_connected
INSTAGRAM_PASSWORD=your_instagram_password
MANYCHAT_API_KEY=your_manychat_api_key
TRAINERIZE_USERNAME=shannonbirch@cocospersonaltraining.com
TRAINERIZE_PASSWORD=cyywp7nyk2
```

## 🚀 Quick Development Setup
```bash
# 1. Start webhook system (current main)
python webhook_main.py

# 2. Start dashboard (separate terminal, headless mode)
cd app/dashboard_modules && python -m streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 --server.headless true

# Alternative: Use run_dashboard.py launcher
python run_dashboard.py

# 3. Start ngrok tunnel (separate terminal)
ngrok http 8001
```

### Dashboard Access
- **URL**: http://localhost:8501
- **Headless mode**: No browser auto-open, manual navigation required
- **Features**: Lead Generation, Response & Review, Analytics, User Profiles

## 🔧 Common Tasks
- **Add AI prompts**: Edit `app/prompts.py`
- **Modify dashboard**: Create module in `app/dashboard_modules/`
- **Update Instagram automation**: Modify `followup_manager.py`
- **Database changes**: Use `app/dashboard_modules/dashboard_sqlite_utils.py`

## 📝 Notes: Meal Plan Creator
- See `MEAL_PLAN_CREATOR.md` for exact PDF structure and build steps.
- Use Woolworths links (bot-safe) and brand links (e.g., VitaWerx).
- No macro formula lines; show only “Macros: …”.
- Shopping list on its own page; de-duplicate; use “Mixed Nuts 300g”.
- Reference implementation: `amy_meal_plan_week2_pdf_pro.py`.

## ⚠️ Critical Constraints
- **Instagram limits**: 50 DMs/day, 75 follows/day
- **Response length**: Maximum 15 words per AI response
- **Safety delays**: 30-90 seconds between Instagram actions
- **Rate limiting**: 3-tier Gemini fallback for API reliability

---

**💡 For complete details**: See [Shanbot - Complete System Architecture.md](Shanbot%20-%20Complete%20System%20Architecture.md)

**💻 For development patterns**: See [AI-Assistant-Development-Guide.md](AI-Assistant-Development-Guide.md) 