import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from progressive_overload_ai import ProgressiveOverloadAI, ProgressionDecision
from dataclasses import dataclass


@dataclass
class WeeklyProgressionReport:
    """Complete weekly progression report for video generation"""
    client_name: str

    # This week's performance
    current_week_goals: List[Dict]
    goal_completion_rate: float
    exercises_improved: List[Dict]
    exercises_maintained: List[Dict]
    exercises_declined: List[Dict]

    # Next week's plan
    next_week_progressions: List[Dict]
    overall_progression_summary: str
    motivation_message: str


class ProgressionVideoIntegrator:
    """Integrates Progressive Overload AI with video generation"""

    def __init__(self):
        self.ai = ProgressiveOverloadAI()
        self.logger = logging.getLogger(__name__)

    def generate_weekly_progression_report(self, client_name: str) -> WeeklyProgressionReport:
        """Generate comprehensive progression report for video"""

        # Get workout data for analysis
        workout_data = self.ai.load_client_workout_data(
            client_name, weeks_back=4)

        if not workout_data:
            return self._create_no_data_report(client_name)

        # Analyze progressions
        progressions = self.ai.analyze_progression_patterns(workout_data)

        # Categorize exercises by performance
        exercises_improved = []
        exercises_maintained = []
        exercises_declined = []

        total_exercises = len(progressions)
        goals_met = 0

        for exercise_name, decisions in progressions.items():
            decision = decisions[0] if decisions else None
            if not decision:
                continue

            exercise_data = {
                "name": exercise_name,
                "current_weight": decision.current_weight,
                "recommended_weight": decision.recommended_weight,
                "action": decision.action_type,
                "reason": decision.reason,
                "confidence": decision.confidence
            }

            if decision.action_type == "increase_weight" or decision.action_type == "increase_reps":
                exercises_improved.append({
                    **exercise_data,
                    "improvement_type": "Weight Increase" if decision.action_type == "increase_weight" else "Rep Increase",
                    "improvement_amount": f"+{decision.recommended_weight - decision.current_weight}kg" if decision.action_type == "increase_weight" else "+1 rep"
                })
                goals_met += 1

            elif decision.action_type == "maintain":
                exercises_maintained.append({
                    **exercise_data,
                    "status": "Maintained Load",
                    "focus": "Consistency & Form"
                })
                goals_met += 0.5  # Partial credit for maintaining

            elif decision.action_type in ["decrease_weight", "deload"]:
                exercises_declined.append({
                    **exercise_data,
                    "decline_reason": "Form Focus" if "form" in decision.reason.lower() else "Recovery Focus",
                    "adjustment": f"{decision.current_weight - decision.recommended_weight}kg lighter"
                })

        goal_completion_rate = (goals_met / total_exercises) * \
            100 if total_exercises > 0 else 0

        # Generate next week's goals
        next_week_progressions = self._format_next_week_goals(progressions)

        # Create summary messages
        overall_summary = self._create_overall_summary(
            len(exercises_improved), len(exercises_maintained), len(
                exercises_declined), goal_completion_rate
        )

        motivation_message = self._create_motivation_message(
            goal_completion_rate, len(exercises_improved))

        return WeeklyProgressionReport(
            client_name=client_name,
            current_week_goals=self._format_current_week_goals(progressions),
            goal_completion_rate=goal_completion_rate,
            exercises_improved=exercises_improved,
            exercises_maintained=exercises_maintained,
            exercises_declined=exercises_declined,
            next_week_progressions=next_week_progressions,
            overall_progression_summary=overall_summary,
            motivation_message=motivation_message
        )

    def _create_no_data_report(self, client_name: str) -> WeeklyProgressionReport:
        """Create report when no workout data is available"""
        return WeeklyProgressionReport(
            client_name=client_name,
            current_week_goals=[],
            goal_completion_rate=0,
            exercises_improved=[],
            exercises_maintained=[],
            exercises_declined=[],
            next_week_progressions=[],
            overall_progression_summary="No workout data available for analysis.",
            motivation_message="Let's get back to training and build some momentum!"
        )

    def _format_current_week_goals(self, progressions: Dict) -> List[Dict]:
        """Format this week's goals for video display"""
        goals = []
        for exercise_name, decisions in progressions.items():
            decision = decisions[0] if decisions else None
            if decision:
                goals.append({
                    "exercise": exercise_name,
                    "target_weight": f"{decision.current_weight}kg",
                    "target_reps": decision.current_reps,
                    "goal": "Maintain good form & complete all sets"
                })
        return goals[:6]  # Limit to top 6 for video

    def _format_next_week_goals(self, progressions: Dict) -> List[Dict]:
        """Format next week's progression goals"""
        next_week = []
        for exercise_name, decisions in progressions.items():
            decision = decisions[0] if decisions else None
            if decision:
                goal_data = {
                    "exercise": exercise_name,
                    "current_weight": f"{decision.current_weight}kg",
                    "new_weight": f"{decision.recommended_weight}kg",
                    "action": decision.action_type,
                    "reason": decision.reason
                }

                if decision.action_type == "increase_weight":
                    goal_data["goal_text"] = f"Increase to {decision.recommended_weight}kg"
                    goal_data["why"] = "You've mastered the current weight!"
                elif decision.action_type == "maintain":
                    goal_data["goal_text"] = f"Keep working at {decision.current_weight}kg"
                    goal_data["why"] = "Focus on perfect form & consistency"
                elif decision.action_type == "decrease_weight":
                    goal_data["goal_text"] = f"Reduce to {decision.recommended_weight}kg"
                    goal_data["why"] = "Let's nail the technique first"

                next_week.append(goal_data)

        return next_week[:6]  # Limit for video

    def _create_overall_summary(self, improved: int, maintained: int, declined: int, completion_rate: float) -> str:
        """Create overall weekly summary"""
        total = improved + maintained + declined

        if completion_rate >= 80:
            return f"Excellent week! {improved} exercises progressed forward."
        elif completion_rate >= 60:
            return f"Solid progress! {improved} exercises improved, {maintained} maintained."
        elif completion_rate >= 40:
            return f"Building momentum! {improved} wins this week."
        else:
            return f"Recovery focus week. {declined} exercises adjusted for better form."

    def _create_motivation_message(self, completion_rate: float, improvements: int) -> str:
        """Create motivational message based on performance"""
        if completion_rate >= 80:
            return "You're absolutely crushing it! Keep this momentum going strong! 💪"
        elif completion_rate >= 60:
            return f"Great work this week! {improvements} exercises leveled up - consistency pays off! 🔥"
        elif completion_rate >= 40:
            return "Progress isn't always linear - you're building a stronger foundation! 💪"
        else:
            return "Every champion has recovery weeks. You're setting up for your next breakthrough! 🚀"


def enhance_video_data_with_progressions(client_data: Dict, client_name: str) -> Dict:
    """Enhance existing video data with progression analysis"""

    integrator = ProgressionVideoIntegrator()
    progression_report = integrator.generate_weekly_progression_report(
        client_name)

    # Add progression data to existing client data
    has_any_progression_data = len(progression_report.exercises_improved +
                                   progression_report.exercises_maintained + progression_report.exercises_declined) > 0

    # Fallback: If no progression data, calculate goal completion from workout data
    if not has_any_progression_data and client_data.get('has_exercise_data', False):
        print("  📊 Creating fallback goal completion analysis from workout data...")
        fallback_analysis = _create_fallback_goal_analysis(client_data)
        if fallback_analysis:
            has_any_progression_data = True
            progression_report.goal_completion_rate = fallback_analysis['goal_completion_rate']
            progression_report.exercises_improved = fallback_analysis['exercises_improved']
            progression_report.exercises_maintained = fallback_analysis['exercises_maintained']
            progression_report.exercises_declined = fallback_analysis['exercises_declined']
            print(
                f"  ✓ Fallback analysis: {progression_report.goal_completion_rate:.1f}% goal completion rate")

    client_data['progression_analysis'] = {
        'goal_completion_rate': progression_report.goal_completion_rate,
        'exercises_improved': progression_report.exercises_improved,
        'exercises_maintained': progression_report.exercises_maintained,
        'exercises_declined': progression_report.exercises_declined,
        'next_week_goals': progression_report.next_week_progressions,
        'overall_summary': progression_report.overall_progression_summary,
        'motivation_message': progression_report.motivation_message,
        'has_progression_data': has_any_progression_data,
        # Match what enhanced_video_slides.py expects
        'has_progressions': has_any_progression_data,
        'recommendations': progression_report.next_week_progressions if has_any_progression_data else {}
    }

    return client_data


def _create_fallback_goal_analysis(client_data: Dict) -> Dict:
    """Create simple goal analysis from workout breakdown when Progressive Overload AI fails"""
    try:
        workout_breakdown = client_data.get('workout_breakdown', [])
        if not workout_breakdown:
            return None

        total_exercises = 0
        improved_exercises = 0
        maintained_exercises = 0
        declined_exercises = 0

        exercises_improved = []
        exercises_maintained = []
        exercises_declined = []

        for workout in workout_breakdown:
            for session in workout.get('sessions_current_week', []):
                for exercise in session.get('exercises', []):
                    exercise_name = exercise.get('name', '')
                    workload_improvement = exercise.get(
                        'workload_improvement_vs_previous', 0)
                    current_workload = exercise.get('workload_current', 0)

                    # Skip exercises with no meaningful workload
                    if current_workload <= 0:
                        continue

                    total_exercises += 1

                    if workload_improvement > 0:
                        improved_exercises += 1
                        exercises_improved.append({
                            'name': exercise_name,
                            'improvement_amount': f"+{workload_improvement:.1f}%",
                            'current_workload': current_workload
                        })
                    elif workload_improvement == 0:
                        maintained_exercises += 1
                        exercises_maintained.append({
                            'name': exercise_name,
                            'status': 'Maintained workload',
                            'current_workload': current_workload
                        })
                    else:
                        declined_exercises += 1
                        exercises_declined.append({
                            'name': exercise_name,
                            'decline_amount': f"{workload_improvement:.1f}%",
                            'current_workload': current_workload
                        })

        if total_exercises == 0:
            return None

        # Calculate goal completion rate (improved + maintained exercises count as goals met)
        # Partial credit for maintaining
        goals_met = improved_exercises + (maintained_exercises * 0.5)
        goal_completion_rate = (goals_met / total_exercises) * 100

        return {
            'goal_completion_rate': goal_completion_rate,
            'exercises_improved': exercises_improved[:5],  # Limit for display
            'exercises_maintained': exercises_maintained[:3],
            'exercises_declined': exercises_declined[:3],
            'total_exercises': total_exercises
        }

    except Exception as e:
        print(f"  ⚠️ Error creating fallback analysis: {e}")
        return None


# Usage example:
if __name__ == "__main__":
    # Test the integration
    integrator = ProgressionVideoIntegrator()
    report = integrator.generate_weekly_progression_report("Shannon Birch")
    print(f"Goal Completion: {report.goal_completion_rate:.1f}%")
    print(f"Exercises Improved: {len(report.exercises_improved)}")
    print(f"Next Week Goals: {len(report.next_week_progressions)}")
