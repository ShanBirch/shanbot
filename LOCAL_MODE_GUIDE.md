# 🏠 Smart Lead Finder - Local Mode Guide

## Overview
The Smart Lead Finder now supports **Local Mode** to find prospects for Shannon's physical gym in the Bayside area of Melbourne. This mode targets women 30+ (especially mothers) who live in or frequent the Hampton/Brighton/Bayside area.

## 🎯 Target Criteria

### Primary Target
- **Women 30+** (especially mothers)
- **Local to Bayside Melbourne area** (Hampton, Brighton, Sandringham, Mentone, Cheltenham)
- **NOT a business/coach/trainer**

### Location Detection
The AI looks for evidence of local presence:
- Location tags (Hampton Beach, Brighton Baths, Bayside Shopping Centre)
- Local school mentions (Brighton Grammar, Firbank Grammar, Mentone Girls Grammar)
- Local business check-ins
- Bio mentions of Bayside suburbs
- Content showing local landmarks

### Target Demographics
- Mothers with family content
- Working mums showing work-life balance
- Women posting about school pickups, local events
- Active lifestyle but not professional fitness

## 🔧 How to Use

### Command Line
```bash
# Run in local mode
python smart_lead_finder.py --mode local

# Or use the dedicated runner
python run_local_smart_finder.py

# Test a specific profile
python test_smart_finder_local.py username_to_test
```

### Dashboard
1. Open dashboard: `python run_dashboard.py`
2. Navigate to "Lead Generation" tab
3. Click "🏠 Find Local Leads" button
4. Monitor progress in "Recent Activity"

## 🏢 Account Configuration

### Local Mode (cocos_pt_studio)
- **Account**: cocos_pt_studio
- **Target**: Bayside gym prospects
- **Sources**: Local businesses, gyms, schools
- **Daily Limit**: 75 follows

### Online Mode (cocos_connected)
- **Account**: cocos_connected  
- **Target**: Vegan/plant-based prospects
- **Sources**: Vegan influencers, plant-based hashtags
- **Daily Limit**: 75 follows

## 📍 Target Sources

### Local Businesses to Mine Followers From
- Brighton Baths, Hampton Pilates, Bayside Council
- Local gyms (F45 Brighton, Anytime Fitness Brighton)
- Schools (Brighton Grammar, Firbank Grammar)
- Shannon's existing gym clients (payneinthenix, simonetindallrealestate)

### Local Hashtags to Search
- #baysidemelbourne, #hamptonvic, #brightonvic
- #melbournemums, #workingmummelbourne, #baysideparents
- #mumsworkout, #mumsfitness, #healthymum

## 🤖 AI Analysis

The AI screening for local mode asks:

1. **IS_LOCAL**: Evidence of Bayside area connection
2. **IS_TARGET_MUM**: Woman 30+ (especially mother)  
3. **IS_BUSINESS_OR_COACH**: Excludes fitness professionals
4. **FINAL_VERDICT**: Must be all: Local + Target Mum + Not Business
5. **IS_FAKE_OR_INACTIVE**: Excludes bots/inactive accounts

## 📊 Database Tracking

Leads are stored with `search_mode` field indicating 'local' or 'online':
- Queue tracking: `processing_queue` table
- Lead storage: Same database, mode-specific targeting
- Follow-up management: Integrated with existing system

## 🧪 Testing

### Test Known Profiles
```bash
python test_smart_finder_local.py payneinthenix        # Should PASS (existing gym client)
python test_smart_finder_local.py baysidecouncil       # Should FAIL (business)
python test_smart_finder_local.py simonetindallrealestate  # Should PASS (gym client)
```

### Expected Results
- **✅ PASS**: Local mums, Shannon's existing clients, Bayside residents
- **❌ FAIL**: Businesses, coaches, non-local accounts, males

## 🎯 Success Metrics

### Quality Indicators
- High percentage of actual local residents
- Women 30+ with family content
- Non-fitness professionals
- Active Instagram accounts

### Red Flags
- High business/coach detection
- Non-local accounts getting through
- Young users or males being targeted
- Inactive/fake accounts

## 🚀 Getting Started

1. **Test First**: Run `python test_smart_finder_local.py` to verify AI logic
2. **Small Batch**: Use dashboard to find 10-20 leads initially  
3. **Review Results**: Check quality in database/dashboard
4. **Scale Up**: Run full 75-lead sessions if quality is good
5. **Monitor**: Use "Recent Activity" to track progress

## ⚠️ Important Notes

- **Account Safety**: Local mode uses cocos_pt_studio account exclusively
- **Daily Limits**: 75 follows per day total (not per mode)
- **Location Focus**: AI looks specifically for Bayside area indicators
- **Quality First**: Better to find 20 high-quality local leads than 75 poor matches

## 🔄 Integration

The local mode integrates seamlessly with existing systems:
- **Follow-up Manager**: Same DM system for both modes
- **Dashboard**: Unified interface with mode selection
- **Database**: Single database with mode tracking
- **Analytics**: Same reporting for both local and online leads 