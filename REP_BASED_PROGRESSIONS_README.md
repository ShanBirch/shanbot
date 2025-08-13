# 🏋️ Rep-Based Progressive Overload System

## Overview

This system automatically analyzes client workout data and implements rep-based progressions directly in Trainerize. It follows a simple, effective progression logic based on achieved reps.

## 🎯 Progression Logic

The system uses the following rep-based rules:

- **Hit 15+ reps**: Increase weight by 2.5kg, reset reps to 6
- **Achieve target reps**: Increase target reps by 2
- **Close to target (80%+)**: Maintain current goals
- **Struggling (<80%)**: Decrease weight by 2.5kg

## 📱 Goals Format

Goals are written in Trainerize reps field as:
```
Goals: W(weight), R(reps)
```

Examples:
- `Goals: W(25), R(10)` = 25kg for 10 reps
- `Goals: W(62.5), R(6)` = 62.5kg for 6 reps

## 🚀 How to Use

### 1. Demo Mode (Test the Logic)
```bash
python demo_rep_progressions.py
```
This shows how the system works with sample data.

### 2. Test with Real Client Data
```bash
python test_rep_based_progressions.py
```
- Enter client name (or press Enter for Alice Forster)
- Review the analysis and recommendations
- Choose implementation option

### 3. Implementation Options

**Option 1: Full Automation** 🤖
- Automatically logs into Trainerize
- Finds the client's program
- Searches for exercises across workouts
- Updates goals in the reps field
- Saves all changes

**Option 2: Manual Review** 📋
- Saves progressions to history file
- You manually implement the changes

## 🔧 Technical Details

### Files Involved
- `progressive_overload_ai.py` - Main AI logic
- `pb.py` - Trainerize automation (enhanced with goal modification)
- `test_rep_based_progressions.py` - Real client testing
- `demo_rep_progressions.py` - Demo with sample data

### Data Sources
1. **SQLite Database** (Primary): `analytics_data_good.sqlite`
2. **JSON Files** (Fallback): Client-specific JSON files

### What Happens During Implementation

1. **Login** to Trainerize with trainer credentials
2. **Navigate** to the client's training program
3. **Search** for exercises across different workouts (Upper Body, Lower Body, Push, Pull, etc.)
4. **Edit** each workout containing target exercises
5. **Modify** the reps field with the new goals format
6. **Save** all changes

### Exercise Finding Strategy

The system searches these common workout names:
- Upper Body, Lower Body
- Push, Pull, Legs
- Back, Chest, Arms, Shoulders
- Full Body, Cardio, Core, Abs

## ⚠️ Important Notes

### Before Running Implementation:
- Close Trainerize in other browsers
- Make sure you have trainer access to the client
- Verify client name matches exactly in the system

### After Implementation:
- Changes are immediately visible to the client
- Goals appear in the workout reps field
- Client sees format: "Goals: W(weight), R(reps)"

## 📊 Example Workflow

```bash
# 1. Test the demo
python demo_rep_progressions.py

# 2. Test with Alice Forster (has good data)
python test_rep_based_progressions.py
# Enter: Alice Forster (or press Enter)

# 3. Review the analysis
# Example output:
# ✅ Generated progressions for 12 exercises
# ⬆️🔩 Increase Weight: 3 exercises
# ⬆️🔢 Increase Reps: 5 exercises
# ➡️ Maintain: 4 exercises

# 4. Choose implementation
# Option 1: 🚀 Implement in Trainerize (Full automation)

# 5. Confirm and watch it work!
```

## 🎯 Expected Results

After implementation, the client will see goals like:
- Bench Press: `Goals: W(62.5), R(6)` (increased weight)
- Squat: `Goals: W(80), R(12)` (increased reps)
- Row: `Goals: W(50), R(10)` (maintained)

## 🐛 Troubleshooting

### "No workout data found"
- Check client name spelling
- Verify client has logged workouts in last 4 weeks
- Check database file exists: `analytics_data_good.sqlite`

### "Could not find exercise in any workout"
- Exercise might be in a workout with an unusual name
- Manually add workout names to `common_workout_names` list
- Check exercise name matches exactly in Trainerize

### "Failed to implement progressions"
- Check Trainerize login credentials
- Verify trainer has access to client program
- Check if Trainerize interface has changed

## 🔄 Progression History

All progressions are saved to `progression_history.json` for tracking:
```json
{
  "Alice Forster": [
    {
      "date": "2025-01-27T...",
      "progressions": {
        "Bench Press": {
          "current_weight": 60,
          "recommended_weight": 62.5,
          "reason": "Hit 15 reps, increasing weight...",
          "action_type": "increase_weight"
        }
      }
    }
  ]
}
```

## 🎉 Success Indicators

✅ **Successful Implementation:**
- "✅ SUCCESS! Progressions implemented in Trainerize!"
- Goals visible in client's workouts
- Client can see new targets

📋 **Manual Review:**
- Progressions saved to history
- Detailed report generated
- Ready for manual implementation

This system bridges the gap between data analysis and actual program updates, making progressive overload truly automated! 🚀 