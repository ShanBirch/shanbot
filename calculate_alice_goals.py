#!/usr/bin/env python3
"""
Calculate Alice's goal completion rate based on her performance vs targets
"""

# Alice's performance vs targets from our analysis
alice_performance = [
    ('Barbell Back Squat Pause', 70.0, 67.0, True),  # Exceeded +3kg
    ('Lat Pull Down Wide Grip', 50.0, 50.0, True),   # Met exactly
    ('Lat Machine Standing Straight Arm', 50.0, 48.0, True),  # Exceeded +2kg
    ('D.B bent over row', 25.0, 25.0, True),         # Met exactly
    ('Barbell Bench Chest Press', 50.0, 47.0, True),  # Exceeded +3kg
    ('Incline Dumbbell Bench', 20.0, 18.0, True),    # Exceeded +2kg
    ('Bulgarian Lunge', 15.0, 15.0, True),           # Met exactly
    ('Face Pulls', 45.0, 45.0, True),                # Met exactly
    ('Cable Hammer Curls', 32.0, 34.0, False),       # 2kg short
    ('Deltoid Lateral Raise', 12.5, 15.0, False),    # 2.5kg short
    ('Cable Triceps', 25.0, 27.0, False),            # 2kg short
    ('Romanian Deadlifts', 22.5, 25.0, False),       # 2.5kg short
    ('Cable Crunch', 60.0, 62.0, False),             # 2kg short
    ('Cable Skull Crusher', 35.0, 37.0, False),      # 2kg short
]

targets_met = 0
total_targets = len(alice_performance)

print("🏋️ ALICE'S GOAL COMPLETION ANALYSIS")
print("=" * 50)

exceeded_count = 0
for exercise, actual, target, met in alice_performance:
    status = "✅ MET" if met else "❌ MISSED"
    difference = actual - target

    if met:
        targets_met += 1
        if difference > 0:
            exceeded_count += 1
            print(
                f'{exercise}: {actual}kg vs {target}kg ({difference:+.1f}kg) - {status} 🔥')
        else:
            print(f'{exercise}: {actual}kg vs {target}kg - {status}')
    else:
        print(f'{exercise}: {actual}kg vs {target}kg ({difference:+.1f}kg) - {status}')

completion_rate = (targets_met / total_targets) * 100

print(f'\n🎯 OVERALL RESULTS:')
print(f'📊 Goal Completion Rate: {completion_rate:.1f}%')
print(f'✅ Targets Met: {targets_met}/{total_targets}')
print(f'🔥 Targets Exceeded: {exceeded_count}/{targets_met}')

if completion_rate >= 80:
    message = 'EXCELLENT! You crushed most of your goals!'
    rating = "A+"
elif completion_rate >= 60:
    message = 'GREAT JOB! Solid progress on most exercises!'
    rating = "B+"
elif completion_rate >= 40:
    message = 'GOOD EFFORT! Building momentum week by week!'
    rating = "C+"
else:
    message = 'FOUNDATION WEEK! Setting up for future success!'
    rating = "Needs Improvement"

print(f'\n💪 ASSESSMENT: {rating}')
print(f'🗣️ MESSAGE: {message}')

print(f'\n📈 WHAT THIS MEANS FOR THE VIDEO:')
print(f'   • Show: "{completion_rate:.0f}% Goal Completion Rate!"')
print(f'   • Highlight: {exceeded_count} exercises where she EXCEEDED targets')
print(
    f'   • Encourage: {total_targets - targets_met} exercises to focus on next week')
print(f'   • Overall: {message}')
