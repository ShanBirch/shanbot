from program_memory import ProgramMemory

# Create memory instance
memory = ProgramMemory()

# Sample workout data
workouts = [
    {
        "name": "Chest Day",
        "exercises": [
            {"name": "Barbell Bench Chest Press", "sets": "4", "reps": "8-10"},
            {"name": "Incline Dumbbell Bench press", "sets": "4", "reps": "8-10"}
        ]
    },
    {
        "name": "Back Day",
        "exercises": [
            {"name": "Wide Grip Chin Up", "sets": "4", "reps": "5-8"},
            {"name": "Lat Pull Down Wide Grip", "sets": "4", "reps": "8-10"}
        ]
    }
]

program_name = "Coco's Studio"

print("=== Program Memory Demo ===")

# Check if program exists
print(f"\n1. Checking if '{program_name}' is built...")
is_built = memory.is_program_built(program_name, workouts)
print(f"   Result: {is_built}")

if not is_built:
    print(f"\n2. Marking '{program_name}' as built...")
    memory.mark_program_built(program_name, workouts)
    print("   ✅ Program marked as built!")
else:
    print(f"\n2. Program '{program_name}' already exists!")

print(f"\n3. Checking again...")
is_built = memory.is_program_built(program_name, workouts)
print(f"   Result: {is_built}")

print(f"\n4. Listing all built programs...")
memory.list_built_programs()

print(f"\n5. Getting program info...")
info = memory.get_program_info(program_name)
if info:
    print(f"   Built: {info['built_date'][:19]}")
    print(f"   Workouts: {', '.join(info['workout_names'])}")
    print(f"   Total Exercises: {info['total_exercises']}")

print(f"\n✅ Demo completed! Memory file 'program_memory.json' created.")
print(
    f"\n💡 To clear this program: memory.clear_program_memory('{program_name}')")
print(f"💡 To clear all programs: memory.clear_program_memory()")
