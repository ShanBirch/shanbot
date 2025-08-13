import json
import os
from datetime import datetime
import hashlib


class ProgramMemory:
    def __init__(self, memory_file="program_memory.json"):
        self.memory_file = memory_file
        self.memory = self.load_memory()

    def load_memory(self):
        """Load existing program memory from JSON file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading memory file: {e}")
                return {"programs": {}, "last_updated": None}
        return {"programs": {}, "last_updated": None}

    def save_memory(self):
        """Save program memory to JSON file"""
        try:
            self.memory["last_updated"] = datetime.now().isoformat()
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving memory file: {e}")

    def generate_program_hash(self, program_name, workouts):
        """Generate a hash for the program structure to detect changes"""
        program_data = {
            "name": program_name,
            "workouts": sorted([
                {
                    "name": workout["name"],
                    "exercises": sorted([
                        f"{ex['name']}_{ex['sets']}_{ex['reps']}"
                        for ex in workout["exercises"]
                    ])
                }
                for workout in workouts
            ], key=lambda x: x["name"])
        }
        program_str = json.dumps(program_data, sort_keys=True)
        return hashlib.md5(program_str.encode()).hexdigest()

    def is_program_built(self, program_name, workouts=None):
        """Check if a program has been built before"""
        if program_name not in self.memory["programs"]:
            return False

        program_info = self.memory["programs"][program_name]

        # If workouts are provided, check if the structure has changed
        if workouts:
            current_hash = self.generate_program_hash(program_name, workouts)
            if program_info.get("program_hash") != current_hash:
                print(
                    f"Program '{program_name}' structure has changed since last build")
                return False

        return True

    def mark_program_built(self, program_name, workouts, training_phase="Week 1-4"):
        """Mark a program as built with details"""
        program_hash = self.generate_program_hash(program_name, workouts)

        self.memory["programs"][program_name] = {
            "built_date": datetime.now().isoformat(),
            "training_phase": training_phase,
            "workout_count": len(workouts),
            "workout_names": [w["name"] for w in workouts],
            "program_hash": program_hash,
            "total_exercises": sum(len(w["exercises"]) for w in workouts)
        }

        self.save_memory()
        print(
            f"✅ Marked program '{program_name}' as built with {len(workouts)} workouts")

    def get_program_info(self, program_name):
        """Get information about a previously built program"""
        return self.memory["programs"].get(program_name)

    def list_built_programs(self):
        """List all previously built programs"""
        if not self.memory["programs"]:
            print("No programs have been built yet.")
            return

        print("\n📋 Previously Built Programs:")
        print("=" * 50)
        for name, info in self.memory["programs"].items():
            built_date = datetime.fromisoformat(
                info["built_date"]).strftime("%Y-%m-%d %H:%M")
            print(f"🏋️  {name}")
            print(f"   📅 Built: {built_date}")
            print(f"   📊 Phase: {info['training_phase']}")
            print(
                f"   💪 Workouts: {info['workout_count']} ({', '.join(info['workout_names'])})")
            print(f"   🎯 Total Exercises: {info['total_exercises']}")
            print()

    def clear_program_memory(self, program_name=None):
        """Clear memory for a specific program or all programs"""
        if program_name:
            if program_name in self.memory["programs"]:
                del self.memory["programs"][program_name]
                self.save_memory()
                print(f"🗑️  Cleared memory for program '{program_name}'")
            else:
                print(f"❌ Program '{program_name}' not found in memory")
        else:
            self.memory["programs"] = {}
            self.save_memory()
            print("🗑️  Cleared all program memory")

    def force_rebuild_program(self, program_name):
        """Force a program to be rebuilt by clearing its memory"""
        self.clear_program_memory(program_name)


# Convenience functions for easy import
def is_program_built(program_name, workouts=None):
    memory = ProgramMemory()
    return memory.is_program_built(program_name, workouts)


def mark_program_built(program_name, workouts, training_phase="Week 1-4"):
    memory = ProgramMemory()
    memory.mark_program_built(program_name, workouts, training_phase)


def list_built_programs():
    memory = ProgramMemory()
    memory.list_built_programs()


def clear_program_memory(program_name=None):
    memory = ProgramMemory()
    memory.clear_program_memory(program_name)


def force_rebuild_program(program_name):
    memory = ProgramMemory()
    memory.force_rebuild_program(program_name)
