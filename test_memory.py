#!/usr/bin/env python3
"""
Test script for the Program Memory system
"""

from program_memory import ProgramMemory, list_built_programs, clear_program_memory, force_rebuild_program


def test_memory_system():
    """Test the program memory functionality"""

    print("🧪 Testing Program Memory System")
    print("=" * 40)

    # Initialize memory
    memory = ProgramMemory()

    # Sample workout data (same as in the main script)
    sample_workouts = [
        {
            "name": "Chest Day",
            "exercises": [
                {"name": "Barbell Bench Chest Press", "sets": "4", "reps": "8-10"},
                {"name": "Incline Dumbbell Bench press",
                    "sets": "4", "reps": "8-10"},
                {"name": "Cable Chest Press", "sets": "3", "reps": "10-12"},
                {"name": "Dumbbell Chest Fly", "sets": "3", "reps": "10-12"},
                {"name": "Cable Bench Triceps Push Down",
                    "sets": "3", "reps": "12-15"}
            ]
        },
        {
            "name": "Back Day",
            "exercises": [
                {"name": "Wide Grip Chin Up/ Assisted Chin Up",
                    "sets": "4", "reps": "5-8"},
                {"name": "Lat Pull Down Wide Grip", "sets": "4", "reps": "8-10"},
                {"name": "Barbell Bent Over Row Pause",
                    "sets": "3", "reps": "10-12"},
                {"name": "Bench Dumbbell Rows", "sets": "3", "reps": "10-12"},
                {"name": "Cable Hammer Curls", "sets": "3", "reps": "12-15"}
            ]
        }
    ]

    program_name = "Test Program"

    # Test 1: Check if program is built (should be False initially)
    print(f"\n1️⃣ Testing if '{program_name}' is built...")
    is_built = memory.is_program_built(program_name, sample_workouts)
    print(f"   Result: {is_built}")

    # Test 2: Mark program as built
    print(f"\n2️⃣ Marking '{program_name}' as built...")
    memory.mark_program_built(program_name, sample_workouts)

    # Test 3: Check if program is built (should be True now)
    print(f"\n3️⃣ Testing if '{program_name}' is built again...")
    is_built = memory.is_program_built(program_name, sample_workouts)
    print(f"   Result: {is_built}")

    # Test 4: List all built programs
    print(f"\n4️⃣ Listing all built programs...")
    list_built_programs()

    # Test 5: Get program info
    print(f"\n5️⃣ Getting program info...")
    info = memory.get_program_info(program_name)
    if info:
        print(f"   Built: {info['built_date'][:19].replace('T', ' ')}")
        print(f"   Workouts: {info['workout_count']}")
        print(f"   Names: {', '.join(info['workout_names'])}")
        print(f"   Total Exercises: {info['total_exercises']}")

    # Test 6: Test program structure change detection
    print(f"\n6️⃣ Testing structure change detection...")
    modified_workouts = sample_workouts.copy()
    modified_workouts[0]["exercises"].append(
        {"name": "New Exercise", "sets": "3", "reps": "10"})

    is_built_modified = memory.is_program_built(
        program_name, modified_workouts)
    print(f"   Modified program is built: {is_built_modified}")

    print(f"\n✅ Memory system test completed!")
    print(f"\n💡 Available commands:")
    print(f"   - list_built_programs()")
    print(f"   - clear_program_memory('program_name')")
    print(f"   - force_rebuild_program('program_name')")
    print(f"   - clear_program_memory()  # Clear all")


def demo_commands():
    """Demonstrate available memory commands"""
    print("\n🎮 Memory System Commands Demo")
    print("=" * 35)

    # Show current programs
    print("\n📋 Current built programs:")
    list_built_programs()

    # Show how to clear specific program
    print("\n🗑️  To clear a specific program:")
    print("   clear_program_memory('Coco\\'s Studio')")

    # Show how to force rebuild
    print("\n🔄 To force rebuild a program:")
    print("   force_rebuild_program('Coco\\'s Studio')")

    # Show how to clear all
    print("\n🗑️  To clear all program memory:")
    print("   clear_program_memory()")


if __name__ == "__main__":
    test_memory_system()
    demo_commands()
