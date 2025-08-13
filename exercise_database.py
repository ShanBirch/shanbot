#!/usr/bin/env python

"""
Exercise Database for Fitness Video Auto-Labeler
Contains information about exercises, their proper technique, and text overlay templates.
"""

import os
import json
from pathlib import Path

# Database file path
DB_FILE = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'data', 'exercise_database.json')

# Default exercise database structure
DEFAULT_DATABASE = {
    # Basic Compound Movements
    "squat": {
        "name": "Squat",
        "variations": ["goblet", "front", "back", "sumo", "box", "jump", "overhead", "split"],
        "primary_muscles": ["quads", "glutes", "hamstrings", "core"],
        "hook": "PERFECT YOUR SQUAT FORM",
        "technique_tips": [
            "FEET SHOULDER-WIDTH APART",
            "CHEST UP, CORE TIGHT",
            "KNEES TRACK WITH TOES",
            "HIPS BACK AND DOWN",
            "DEPTH: THIGHS PARALLEL OR LOWER"
        ],
        "common_mistakes": [
            "Knees collapsing inward",
            "Heels lifting off ground",
            "Rounding lower back",
            "Not achieving proper depth",
            "Looking down instead of forward"
        ],
        "hashtags": ["squatform", "legday", "strengthtraining", "squatchallenge", "lowerbodyworkout"]
    },
    "deadlift": {
        "name": "Deadlift",
        "variations": ["conventional", "sumo", "romanian", "stiff_leg", "trap_bar", "single_leg"],
        "primary_muscles": ["hamstrings", "glutes", "lower_back", "traps"],
        "hook": "MASTER THE DEADLIFT",
        "technique_tips": [
            "FEET HIP-WIDTH APART",
            "BAR OVER MID-FOOT",
            "FLAT BACK THROUGHOUT",
            "PUSH THROUGH HEELS",
            "HIPS AND SHOULDERS RISE TOGETHER"
        ],
        "common_mistakes": [
            "Rounding the back",
            "Bar too far from shins",
            "Jerking the weight up",
            "Looking up instead of neutral",
            "Starting with hips too low"
        ],
        "hashtags": ["deadliftform", "posteriorchain", "strengthtraining", "deadliftday", "powerlifting"]
    },
    "deadlift_romanian": {
        "name": "Romanian Deadlift",
        "variations": ["single_leg", "dumbbell", "kettlebell", "barbell", "elevated"],
        "primary_muscles": ["hamstrings", "glutes", "lower_back"],
        "hook": "BUILD THAT POSTERIOR CHAIN",
        "technique_tips": [
            "SOFT KNEE BEND",
            "HINGE AT HIPS, FLAT BACK",
            "PUSH HIPS BACK",
            "BAR CLOSE TO BODY",
            "FEEL THE HAMSTRING STRETCH"
        ],
        "common_mistakes": [
            "Bending knees too much",
            "Rounding the back",
            "Not pushing hips back far enough",
            "Bar drifting away from legs",
            "Not engaging core properly"
        ],
        "hashtags": ["romatiandeadlift", "rdl", "hamstringworkout", "hingepattern", "posteriorchain"]
    },
    "pushup": {
        "name": "Push-Up",
        "variations": ["wide", "narrow", "decline", "incline", "diamond", "spiderman", "archer"],
        "primary_muscles": ["chest", "shoulders", "triceps", "core"],
        "hook": "PUSH-UP PERFECTION",
        "technique_tips": [
            "HANDS SLIGHTLY WIDER THAN SHOULDERS",
            "BODY IN STRAIGHT LINE",
            "ELBOWS 45° TO BODY",
            "LOWER TO 1-2 INCHES FROM FLOOR",
            "PRESS THROUGH ENTIRE PALM"
        ],
        "common_mistakes": [
            "Sagging hips",
            "Flaring elbows too wide",
            "Incomplete range of motion",
            "Head dropping forward",
            "Not engaging core"
        ],
        "hashtags": ["pushupchallenge", "calisthenics", "bodyweightstrength", "chestworkout", "pushupform"]
    },
    "plank_side": {
        "name": "Side Plank",
        "variations": ["elbow", "straight_arm", "modified_knee", "raised_leg", "rotation"],
        "primary_muscles": ["obliques", "transverse_abdominis", "hip_abductors", "shoulders"],
        "hook": "IGNITE YOUR OBLIQUES",
        "technique_tips": [
            "STACK SHOULDERS, HIPS, KNEES",
            "LIFT HIPS HIGH",
            "ENGAGE OBLIQUES",
            "KEEP NECK NEUTRAL",
            "BREATHE STEADILY"
        ],
        "common_mistakes": [
            "Letting hips sag",
            "Improper alignment",
            "Holding breath",
            "Looking up or down",
            "Not engaging core fully"
        ],
        "hashtags": ["sideplank", "coreworkout", "obliques", "functionalfitness", "stabilitytraining"]
    },
    "burpee": {
        "name": "Burpee",
        "variations": ["standard", "pushup", "jump", "box_jump", "single_leg", "lateral"],
        "primary_muscles": ["full_body", "chest", "quads", "shoulders", "core"],
        "hook": "BURN MORE WITH BURPEES",
        "technique_tips": [
            "DROP HANDS TO FLOOR",
            "JUMP TO PLANK POSITION",
            "OPTIONAL: ADD PUSH-UP",
            "JUMP FEET TOWARD HANDS",
            "EXPLOSIVE JUMP UP"
        ],
        "common_mistakes": [
            "Rounding back during squat",
            "Improper push-up form",
            "Shallow squat on landing",
            "Not extending fully on jump",
            "Inadequate core engagement"
        ],
        "hashtags": ["burpeechallenge", "hiitworkout", "fullbodyworkout", "functionaltraining", "cardioworkout"]
    },

    # Upper Body Exercises
    "bench_press": {
        "name": "Bench Press",
        "variations": ["flat", "incline", "decline", "close_grip", "wide_grip", "dumbbell"],
        "primary_muscles": ["chest", "shoulders", "triceps"],
        "hook": "BENCH PRESS BASICS",
        "technique_tips": [
            "FEET PLANTED FIRMLY",
            "SHOULDER BLADES RETRACTED",
            "SLIGHT ARCH IN LOWER BACK",
            "BAR PATH OVER MID-CHEST",
            "ELBOWS AT 45° TO BODY"
        ],
        "common_mistakes": [
            "Bouncing bar off chest",
            "Excessive arch",
            "Flaring elbows too wide",
            "Lifting head off bench",
            "Uneven bar path"
        ],
        "hashtags": ["benchpress", "chestday", "strengthtraining", "upperbodyworkout", "gymlife"]
    },
    "row": {
        "name": "Row",
        "variations": ["barbell", "dumbbell", "cable", "inverted", "pendlay", "meadows", "t-bar"],
        "primary_muscles": ["upper_back", "lats", "biceps", "rear_deltoids"],
        "hook": "BUILD A STRONGER BACK",
        "technique_tips": [
            "CHEST UP, SHOULDERS BACK",
            "PULL TOWARD LOWER RIBS",
            "ELBOWS CLOSE TO BODY",
            "SQUEEZE SHOULDER BLADES",
            "CONTROLLED ECCENTRIC"
        ],
        "common_mistakes": [
            "Using momentum",
            "Rounding shoulders",
            "Insufficient range of motion",
            "Lifting hips/torso",
            "Wrist flexion/extension"
        ],
        "hashtags": ["backmuscles", "rowingworkout", "latbuilder", "backday", "pullmovement"]
    },

    # Lower Body Exercises
    "lunge": {
        "name": "Lunge",
        "variations": ["forward", "reverse", "lateral", "walking", "curtsy", "jump", "deficit"],
        "primary_muscles": ["quads", "glutes", "hamstrings", "calves"],
        "hook": "PERFECT LUNGE TECHNIQUE",
        "technique_tips": [
            "TORSO UPRIGHT",
            "FRONT KNEE OVER ANKLE",
            "BACK KNEE TOWARD GROUND",
            "90° ANGLES IN BOTH KNEES",
            "CORE ENGAGED THROUGHOUT"
        ],
        "common_mistakes": [
            "Front knee extending past toes",
            "Leaning too far forward",
            "Not going deep enough",
            "Knees collapsing inward",
            "Uneven weight distribution"
        ],
        "hashtags": ["lungevariations", "legworkout", "lowerbody", "unilateraltraining", "stabilitytraining"]
    },

    # Adding Cable Crunch Oblique exercise
    "cable_crunch_oblique": {
        "name": "Cable Crunch Oblique",
        "variations": ["kneeling", "standing", "rope", "bar", "single_arm"],
        "primary_muscles": ["obliques", "rectus_abdominis", "transverse_abdominis", "serratus"],
        "hook": "SCULPT YOUR OBLIQUES",
        "technique_tips": [
            "HINGE AT HIPS",
            "PULL WITH ABDOMINALS, NOT ARMS",
            "TWIST TOWARD OPPOSITE KNEE",
            "KEEP NECK NEUTRAL",
            "EXHALE ON CONTRACTION"
        ],
        "common_mistakes": [
            "Using too much weight",
            "Pulling with arms instead of abs",
            "Insufficient rotation",
            "Rounding shoulders forward",
            "Moving too quickly"
        ],
        "hashtags": ["cablecrunch", "obliqueworkout", "corestrength", "absworkout", "rotationalmovement"]
    }
}


class ExerciseDatabase:
    """
    Manages the exercise database, providing methods to add, retrieve, and update exercise information.
    """

    def __init__(self):
        """Initialize the exercise database, creating it if it doesn't exist."""
        self.exercises = {}
        self.load_database()

    def load_database(self):
        """Load the exercise database from file or create a new one if it doesn't exist."""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

            if os.path.exists(DB_FILE):
                with open(DB_FILE, 'r') as file:
                    self.exercises = json.load(file)
                    print(
                        f"Loaded {len(self.exercises)} exercises from database.")
            else:
                # Initialize with default database
                self.exercises = DEFAULT_DATABASE
                self.save_database()
                print(
                    f"Created new exercise database with {len(self.exercises)} default exercises.")
        except Exception as e:
            print(f"Error loading exercise database: {e}")
            self.exercises = DEFAULT_DATABASE

    def save_database(self):
        """Save the current exercise database to file."""
        try:
            with open(DB_FILE, 'w') as file:
                json.dump(self.exercises, file, indent=4)
            print(f"Saved {len(self.exercises)} exercises to database.")
        except Exception as e:
            print(f"Error saving exercise database: {e}")

    def get_exercise_info(self, filename):
        """
        Extract exercise information from a filename and match with database.

        Args:
            filename (str): The filename to analyze (e.g., 'Squat_Goblet.mp4', 'DeadliftRomanian.MOV')

        Returns:
            dict: Exercise information including name, technique tips, etc., or None if not found
        """
        try:
            # Remove extension and convert to lowercase
            base_name = os.path.splitext(os.path.basename(filename))[0].lower()

            # Check for exact match
            for exercise_key, exercise_data in self.exercises.items():
                if exercise_key == base_name:
                    return exercise_data

            # Look for main exercise name and possible variation
            for exercise_key, exercise_data in self.exercises.items():
                # Check if the exercise name is in the filename
                if exercise_key in base_name:
                    # Make a copy of the exercise data
                    result = dict(exercise_data)

                    # Check for variations
                    for variation in exercise_data.get('variations', []):
                        if variation.lower() in base_name:
                            result['name'] = f"{result['name']} ({variation.title()})"
                            break

                    return result

            # Special case for Romanian Deadlift
            if "deadlift_romanian" in base_name or "romanian_deadlift" in base_name or "rdl" in base_name:
                return self.exercises.get("deadlift_romanian")

            return None
        except Exception as e:
            print(
                f"Error extracting exercise info from filename '{filename}': {e}")
            return None

    def add_exercise(self, exercise_key, exercise_data):
        """
        Add a new exercise to the database.

        Args:
            exercise_key (str): Unique identifier for the exercise
            exercise_data (dict): Exercise information including name, technique tips, etc.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.exercises[exercise_key] = exercise_data
            self.save_database()
            return True
        except Exception as e:
            print(f"Error adding exercise '{exercise_key}': {e}")
            return False

    def update_exercise(self, exercise_key, updated_data):
        """
        Update an existing exercise in the database.

        Args:
            exercise_key (str): Unique identifier for the exercise
            updated_data (dict): Updated exercise information

        Returns:
            bool: True if successful, False otherwise
        """
        if exercise_key not in self.exercises:
            return False

        try:
            self.exercises[exercise_key].update(updated_data)
            self.save_database()
            return True
        except Exception as e:
            print(f"Error updating exercise '{exercise_key}': {e}")
            return False

    def get_all_exercises(self):
        """
        Get all exercises in the database.

        Returns:
            dict: All exercises in the database
        """
        return self.exercises


# Create a singleton instance
exercise_db = ExerciseDatabase()
