# Webhook Refactoring Task for AI Assistant

## Current Situation
You are working on Shannon's fitness coaching automation system called "Shanbot". There are multiple webhook files that need to be refactored into a clean, modular structure. The current webhook system is working but scattered across multiple files.

## Current Webhook Files
- `webhook_main.py` - Partially refactored main app (exists, needs completion)
- `action_router.py` - Routing logic (exists, 187 lines)
- `webhook1.py`, `webhook2.py`, `webhook3.py` - Original webhook files (78KB, 76KB, 57KB respectively)
- `webhook0605.py` - Main production webhook (207KB, 4215 lines)
- `webhook_handlers.py` - Core processing functions (78KB, 1768 lines)
- `action_handlers/` - Directory exists but may need expansion
- `services/` - Directory exists but may need expansion

## Current TODO Status
The following tasks are in progress:
1. ✅ COMPLETED: Analyze existing webhook structure
2. 🔄 IN PROGRESS: Create webhook_main.py - core FastAPI app entry point
3. ⏳ PENDING: Create action_router.py - route definitions and message routing
4. ⏳ PENDING: Create action_handlers/ directory with specialized handlers
5. ⏳ PENDING: Create services/ directory with supporting services
6. ⏳ PENDING: Create utilities/ directory with shared utilities
7. ⏳ PENDING: Test the refactored webhook system

## Key Requirements
1. **Maintain Functionality**: The refactored system must preserve all existing webhook functionality
2. **Modular Structure**: Break down the monolithic webhook files into organized modules
3. **FastAPI**: Use FastAPI as the main framework (already started in webhook_main.py)
4. **Shannon's Voice**: Preserve the AI response patterns that match Shannon's communication style
5. **Message Buffering**: Maintain the message buffering system for grouping rapid messages
6. **Action Handlers**: Separate handlers for different message types (workout requests, form checks, calorie tracking, etc.)

## Target Structure
```
shanbot/
├── webhook_main.py              # Main FastAPI app entry point
├── action_router.py             # Message routing logic
├── action_handlers/             # Specialized message handlers
│   ├── __init__.py
│   ├── workout_handler.py       # Workout modification requests
│   ├── form_check_handler.py    # Video form analysis
│   ├── calorie_handler.py       # Food/calorie tracking
│   ├── general_chat_handler.py  # General conversation
│   └── onboarding_handler.py    # New user onboarding
├── services/                    # Supporting services
│   ├── __init__.py
│   ├── message_buffer.py        # Message buffering logic
│   ├── ai_service.py            # AI/Gemini integration
│   ├── manychat_service.py      # ManyChat API calls
│   └── analytics_service.py     # Analytics and logging
└── utilities/                   # Shared utilities
    ├── __init__.py
    ├── models.py                # Pydantic models
    ├── config.py                # Configuration
    └── helpers.py               # Helper functions
```

## Current System Context
- **Business**: Shannon's fitness coaching automation for Instagram
- **Tech Stack**: FastAPI, Python, ManyChat integration, Google Gemini AI
- **Main Functions**: 
  - Instagram message processing via ManyChat webhooks
  - AI responses in Shannon's voice (casual Australian, 1-15 words)
  - Workout program modifications via Trainerize
  - Form check video analysis
  - Calorie tracking and food analysis
  - Client onboarding flows

## Immediate Next Steps
1. **Complete webhook_main.py**: Ensure it has proper FastAPI setup, CORS, health endpoints
2. **Fix import issues**: Many files reference missing modules - create them or fix imports
3. **Create missing handlers**: Based on the existing code, create proper action handlers
4. **Test basic functionality**: Ensure the refactored system can handle a simple webhook request
5. **Preserve existing integrations**: Don't break ManyChat, Trainerize, or Gemini integrations

## Key Files to Reference
- `webhook0605.py` - The main production webhook with all functionality
- `webhook_handlers.py` - Core processing functions that should be modularized
- `app/prompts.py` - AI prompt templates (83KB, 1188 lines)
- `app/dashboard_modules/dashboard_sqlite_utils.py` - Database utilities

## Current Working Directory
- Path: `C:\Users\Shannon\OneDrive\Desktop\shanbot`
- The user is currently looking at `webhook2.py` line 6

## Critical Notes
- **Don't get stuck in terminals** - Focus on actual file creation and code implementation
- **Avoid endless analysis** - The structure is analyzed, now implement
- **Test as you go** - Create small, testable components
- **Maintain existing functionality** - This is a refactor, not a rewrite
- **Check existing action_handlers/ and services/ directories** - Some files may already exist

## Success Criteria
1. A working webhook_main.py that can start without import errors
2. Properly organized action handlers that can process different message types
3. Clean separation of concerns between routing, handling, and services
4. All existing webhook functionality preserved
5. The system can handle a test webhook request end-to-end

Start by fixing import errors in webhook_main.py and creating any missing modules it references. Then systematically work through the action handlers and services. 