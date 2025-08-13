# Two-Phase Outreach System

A sophisticated Instagram outreach system that follows users and sends personalized DMs with optimal timing for maximum engagement.

## 🎯 System Overview

**Phase 1: Follow Users** (`follow_users.py`)
- Follows 20-25 plant-based users per day from your potential clients database
- Prioritizes followers of your actual clients for higher quality leads
- Tracks follow status and timestamps in database

**Phase 2: Send Delayed DMs** (`send_delayed_dms.py`)
- Sends personalized DMs to users followed 2-4 hours ago
- Uses intelligent message selection based on source account
- Maintains natural human-like timing

## 🚀 Quick Start

### Manual Usage

**Follow users immediately:**
```bash
python follow_users.py
```

**Send DMs to users ready for messaging:**
```bash
python send_delayed_dms.py
```

**Run complete sequence manually:**
```bash
python outreach_scheduler.py both
```

### Automated Scheduling

**Start automated daily outreach:**
```bash
python outreach_scheduler.py
```
- Runs follow script daily at 10:00 AM
- Automatically sends DMs 3 hours later (1:00 PM)
- Continues running until stopped with Ctrl+C

## 📊 Safety Features

### Daily Limits
- **Follows:** 25 per day maximum
- **DMs:** 20 per day maximum
- **Timing:** 2-4 hour gap between follow and DM

### Human-Like Behavior
- Random delays between actions (30-90 seconds for follows, 60-120 seconds for DMs)
- Natural message variations
- Stealth browser settings to avoid detection

## 💬 Message Types

### Mutual Connection Messages
For users who follow your actual clients:
- "Hey! Noticed you follow [client_name] - love connecting with people in the same circles! How's your week going?"

### Community Messages  
For users who follow famous influencers:
- "Hey! Noticed you're into the plant based fitness scene - always cool meeting like minded people! Hope you're well :)"

## 📈 Database Tracking

The system automatically tracks:
- `followed_at` - When user was followed
- `follow_status` - Success/failure of follow attempt
- `dm_sent_at` - When DM was sent
- `dm_message` - Exact message sent
- `dm_status` - Success/failure of DM attempt

## 🔧 Configuration

### Your Current Clients (High Priority Sources)
Edit in both scripts:
```python
self.your_clients = [
    'kristyleecoop', 'le_greenies', 'rebeccadangelo01',
    'payneinthenix', 'simonetindallrealestate'
]
```

### Famous Influencers (Community Sources)
```python
self.famous_influencers = [
    'nimai_delgado', 'plantyou', 'pickuplimes', 'earthyandy',
    'fullyrawkristina', 'the_buddhist_chef', 'vegan_bodybuilding'
]
```

### Daily Limits
```python
self.daily_follow_limit = 25  # Max follows per day
self.daily_dm_limit = 20      # Max DMs per day
```

## 📝 Logs

Each script creates detailed logs:
- `follow_users.log` - Follow activity and results
- `send_dms.log` - DM activity and results  
- `outreach_scheduler.log` - Scheduler activity

## ⚠️ Important Notes

1. **Database Dependency:** Requires existing `potential_clients` table from your client finder script
2. **Plant-Based Focus:** Currently filters for plant-based/vegan users only
3. **Chrome Profile:** Uses your existing Chrome profile for Instagram login
4. **Manual Login:** You may need to log into Instagram manually the first time

## 🎛️ Advanced Usage

### Run Individual Components
```bash
# Just follow users
python outreach_scheduler.py follow

# Just send DMs  
python outreach_scheduler.py dm

# Full sequence once
python outreach_scheduler.py both
```

### Monitor Progress
```bash
# Watch follow log in real-time
tail -f follow_users.log

# Watch DM log in real-time  
tail -f send_dms.log
```

## 🔄 Typical Daily Workflow

1. **10:00 AM** - Automated follow script runs
   - Follows 20-25 new plant-based users
   - Logs activity to database

2. **1:00 PM** - Automated DM script runs  
   - Sends personalized DMs to users followed at 10 AM
   - Uses intelligent message selection

3. **Results** - Check logs for success rates and any issues

## 🛠️ Troubleshooting

**No users to follow:**
- Check if `find_potential_clients.py` has been run recently
- Verify database has plant-based users with `followed_at = NULL`

**No users ready for DMs:**
- Wait 2-4 hours after running follow script
- Check that follow script completed successfully

**Login issues:**
- Manually log into Instagram in Chrome
- Check Chrome profile path in script settings

**Rate limiting:**
- Scripts automatically respect daily limits
- Instagram may impose additional restrictions if detected

## 📞 Support

For issues or questions about the outreach system, check the log files first as they contain detailed error information and success metrics. 