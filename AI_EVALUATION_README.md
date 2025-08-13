# 🚀 Shannon's Bot AI Evaluation System

**3-Tier AI evaluation at massive scale** - Test your bot with 10,000+ AI-generated conversations!

## 🎯 What This Does

This system creates a **comprehensive AI testing loop**:

1. **🤖 AI Generator** → Creates realistic fresh vegan lead messages
2. **🧠 Shannon's Bot** → Processes messages through your webhook 
3. **🔍 AI Evaluator** → Scores responses on multiple criteria

Perfect for optimizing your bot's performance across thousands of scenarios!

## 🏗️ System Components

### Core Files
- `ai_evaluation_system.py` - Main 3-tier evaluation engine
- `run_evaluation.py` - Simple launcher with presets
- `analyze_results.py` - Comprehensive results analysis
- `app/dashboard_modules/evaluation_dashboard.py` - Real-time Streamlit dashboard

### Database
- `evaluation_results.sqlite` - Stores all test results and analysis data

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_evaluation.txt
```

### 2. Start Your Webhook
Make sure your webhook is running and accessible:
```bash
# In one terminal
python webhook0605.py

# In another terminal  
ngrok http 8000
```

### 3. Run Evaluation
```bash
# Simple launcher with presets
python run_evaluation.py

# Choose from:
# 1. Quick Test (100 conversations)
# 2. Standard Test (1,000 conversations)  
# 3. Comprehensive Test (5,000 conversations)
# 4. Massive Test (10,000 conversations)
# 5. Custom amount
```

### 4. Monitor in Dashboard
Add to your Streamlit dashboard:
```python
# In dashboard.py navigation
elif st.session_state.selected_page == "AI Evaluation":
    from evaluation_dashboard import display_evaluation_dashboard
    display_evaluation_dashboard()
```

### 5. Analyze Results
```bash
# Comprehensive analysis
python analyze_results.py

# Options:
# 1. Show Overview
# 2. Performance Trends  
# 3. Failure Analysis
# 4. Improvement Suggestions
# 5. Generate Full Report
```

## 📊 What Gets Evaluated

### AI Generator Creates:
- **Initial contact messages** - "hey! noticed youre plant based too..."
- **Fitness struggles** - "struggling to build muscle on vegan diet..."
- **Direct inquiries** - "do you do plant based coaching?"
- **Personal stories** - "vegan for 2 years but having trouble..."
- **Referral messages** - "friend recommended you for..."

### AI Evaluator Scores On:
- **Fresh Vegan Detection** (1-10) - How well it identifies vegan leads
- **A/B Strategy Assignment** - Group A (rapport) vs Group B (direct)
- **Response Tone Quality** - Shannon's casual Australian style
- **Response Length** - 1-15 word compliance
- **Conversation Stage** - Lead journey progression
- **Overall Performance** (1-10) - Combined effectiveness score

## 📈 Sample Results

```
🎯 EVALUATION OVERVIEW
===================================
📊 Total Tests: 10,000
✅ Webhook Success Rate: 98.5%
⏱️ Average Response Time: 2.3s
🌱 Average Fresh Vegan Score: 8.2/10
⭐ Average Overall Score: 7.8/10

🎯 A/B Strategy Distribution:
   Group A (Rapport): 5,240 (52.4%)
   Group B (Direct): 4,760 (47.6%)

🎭 Scenario Performance:
   direct_inquiry: 8.4/10
   fitness_struggle: 8.1/10
   initial_contact: 7.9/10
   personal_story: 7.6/10
   referral_inquiry: 7.4/10
```

## 🔧 Configuration

### Webhook URL
Update in `ai_evaluation_system.py`:
```python
WEBHOOK_URL = "your_ngrok_url/webhook/manychat"
```

### Concurrency Limits
Adjust for your system:
```python
MAX_CONCURRENT_TESTS = 10  # Parallel requests
```

### Evaluation Criteria
Customize scoring in `AIResponseEvaluator` class

## 🎯 Advanced Usage

### Custom Scenarios
Add new scenario types:
```python
scenario_prompts = {
    "custom_scenario": "Your custom prompt here...",
    # ... existing scenarios
}
```

### Batch Processing
Run specific batch sizes:
```python
# In ai_evaluation_system.py
await evaluation_system.run_massive_evaluation(
    total_tests=5000, 
    batch_size=50
)
```

### Real-time Monitoring
The dashboard shows:
- Live test progress
- Score distributions
- Strategy assignments
- Performance trends
- Failure analysis

## 📊 Output Files

### Database: `evaluation_results.sqlite`
```sql
-- Main evaluation table
evaluations (
    id, test_run_id, user_message, ig_username,
    scenario_type, webhook_success, fresh_vegan_score,
    recommended_strategy, overall_score, evaluation_data
)
```

### Reports: `evaluation_report_TIMESTAMP.txt`
- Comprehensive performance analysis
- Improvement suggestions
- Failure pattern analysis
- Trend identification

### CSV Exports
Download data for external analysis tools

## ⚠️ Important Notes

### Rate Limiting
- System respects webhook response times
- Built-in delays between batches
- Async processing prevents overload

### API Keys
Uses your existing Gemini API key from `ai_evaluation_system.py`

### Memory Usage
Large evaluations (10k+ tests) use significant memory. Monitor system resources.

## 🔍 Troubleshooting

### Common Issues

**Webhook timeouts:**
- Increase timeout in `send_webhook_async()`
- Check ngrok tunnel stability

**Low success rates:**
- Verify webhook URL is correct
- Check ManyChat integration
- Monitor system logs

**Memory issues:**
- Reduce batch size
- Run smaller test batches
- Clear old evaluation data

### Debug Mode
Enable detailed logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Next Steps

1. **Start Small** - Run 100 tests to verify setup
2. **Iterate** - Use analysis to identify improvements  
3. **Scale Up** - Run comprehensive 10k test evaluations
4. **Optimize** - Implement suggested improvements
5. **Monitor** - Use dashboard for ongoing performance tracking

## 💡 Pro Tips

- Run evaluations during low-traffic periods
- Compare results before/after bot improvements
- Use A/B test insights to optimize strategy assignment
- Export data for custom analysis in Excel/Python
- Monitor trends over time to track improvements

---

**🎯 Goal**: Optimize Shannon's bot to achieve 8.5+ average scores across all scenarios!

**📊 Success Metrics**: 
- Fresh vegan detection: >8.0/10
- Response compliance: >95%
- A/B balance: 45-55% split
- Overall performance: >8.0/10 