#!/usr/bin/env python3
"""
📊 SHANNON'S BOT EVALUATION RESULTS ANALYZER
Comprehensive analysis of AI evaluation results
"""

import sqlite3
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
from typing import Dict, List


class EvaluationAnalyzer:
    """Analyze and visualize AI evaluation results"""

    def __init__(self, db_path: str = "evaluation_results.sqlite"):
        self.db_path = db_path
        self.df = None
        self.load_data()

    def load_data(self):
        """Load evaluation data from SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            self.df = pd.read_sql_query(
                "SELECT * FROM evaluations ORDER BY created_at DESC",
                conn
            )
            conn.close()

            if self.df.empty:
                print("❌ No evaluation data found")
                return

            print(f"📊 Loaded {len(self.df):,} evaluation records")

            # Parse JSON evaluation data
            self.df['evaluation_json'] = self.df['evaluation_data'].apply(
                lambda x: json.loads(x) if x else {}
            )

        except Exception as e:
            print(f"❌ Error loading data: {e}")
            self.df = pd.DataFrame()

    def show_overview(self):
        """Display comprehensive overview of results"""
        if self.df.empty:
            return

        print("\n🎯 EVALUATION OVERVIEW")
        print("=" * 50)

        # Basic stats
        total_tests = len(self.df)
        successful_webhooks = self.df['webhook_success'].sum()
        avg_response_time = self.df['webhook_response_time'].mean()
        avg_overall_score = self.df['overall_score'].mean()
        avg_vegan_score = self.df['fresh_vegan_score'].mean()

        print(f"📊 Total Tests: {total_tests:,}")
        print(
            f"✅ Webhook Success Rate: {successful_webhooks/total_tests*100:.1f}%")
        print(f"⏱️ Average Response Time: {avg_response_time:.2f}s")
        print(f"🌱 Average Fresh Vegan Score: {avg_vegan_score:.1f}/10")
        print(f"⭐ Average Overall Score: {avg_overall_score:.1f}/10")

        # Test run distribution
        test_runs = self.df['test_run_id'].value_counts()
        print(f"\n🔬 Test Runs:")
        for run_id, count in test_runs.head(5).items():
            print(f"   {run_id}: {count:,} tests")

        # Strategy distribution
        strategy_dist = self.df['recommended_strategy'].value_counts()
        print(f"\n🎯 A/B Strategy Distribution:")
        for strategy, count in strategy_dist.items():
            percentage = count / len(self.df) * 100
            print(f"   Group {strategy}: {count:,} ({percentage:.1f}%)")

        # Scenario performance
        scenario_scores = self.df.groupby('scenario_type')[
            'overall_score'].mean().sort_values(ascending=False)
        print(f"\n🎭 Scenario Performance:")
        for scenario, score in scenario_scores.items():
            print(f"   {scenario}: {score:.1f}/10")

    def analyze_performance_trends(self):
        """Analyze performance trends over time"""
        if self.df.empty:
            return

        print("\n📈 PERFORMANCE TRENDS")
        print("=" * 50)

        # Convert timestamp to datetime
        self.df['timestamp'] = pd.to_datetime(self.df['created_at'])

        # Group by test run
        run_performance = self.df.groupby('test_run_id').agg({
            'overall_score': ['mean', 'std', 'count'],
            'fresh_vegan_score': 'mean',
            'webhook_success': 'mean',
            'webhook_response_time': 'mean'
        }).round(2)

        print("📊 Performance by Test Run:")
        print(run_performance.to_string())

        # Score distribution
        print(f"\n🎯 Score Distribution:")
        score_ranges = [
            (0, 3, "Poor"),
            (3, 5, "Below Average"),
            (5, 7, "Average"),
            (7, 8.5, "Good"),
            (8.5, 10, "Excellent")
        ]

        for min_score, max_score, label in score_ranges:
            count = len(self.df[
                (self.df['overall_score'] >= min_score) &
                (self.df['overall_score'] < max_score)
            ])
            percentage = count / len(self.df) * 100
            print(
                f"   {label} ({min_score}-{max_score}): {count:,} ({percentage:.1f}%)")

    def analyze_failure_patterns(self):
        """Analyze patterns in low-performing tests"""
        if self.df.empty:
            return

        print("\n⚠️ FAILURE PATTERN ANALYSIS")
        print("=" * 50)

        # Low scoring conversations
        low_scores = self.df[self.df['overall_score'] < 5]
        if len(low_scores) > 0:
            print(
                f"🔍 Found {len(low_scores):,} low-scoring conversations (<5.0)")

            # Analyze common patterns
            print("\n🎭 Low-scoring scenarios:")
            low_scenario_dist = low_scores['scenario_type'].value_counts()
            for scenario, count in low_scenario_dist.items():
                percentage = count / len(low_scores) * 100
                print(f"   {scenario}: {count} ({percentage:.1f}%)")

            # Show example messages
            print("\n📝 Example low-scoring messages:")
            for _, row in low_scores.head(3).iterrows():
                print(
                    f"   Score: {row['overall_score']:.1f} - \"{row['user_message']}\"")

        # Webhook failures
        webhook_failures = self.df[~self.df['webhook_success']]
        if len(webhook_failures) > 0:
            print(f"\n⚠️ Webhook Failures: {len(webhook_failures):,}")
            print("   These may indicate system issues or rate limiting")

    def suggest_improvements(self):
        """Suggest improvements based on evaluation results"""
        if self.df.empty:
            return

        print("\n💡 IMPROVEMENT SUGGESTIONS")
        print("=" * 50)

        # Analyze evaluation data for insights
        insights = []

        # Strategy balance
        strategy_dist = self.df['recommended_strategy'].value_counts(
            normalize=True)
        if len(strategy_dist) > 1:
            max_strategy = strategy_dist.index[0]
            max_percentage = strategy_dist.iloc[0] * 100

            if max_percentage > 70:
                insights.append(
                    f"🎯 Strategy Distribution: {max_percentage:.1f}% assigned to Group {max_strategy}. Consider adjusting A/B test criteria for more balanced distribution.")

        # Performance by scenario
        scenario_performance = self.df.groupby(
            'scenario_type')['overall_score'].mean()
        worst_scenario = scenario_performance.idxmin()
        best_scenario = scenario_performance.idxmax()

        insights.append(
            f"📊 Best Scenario: '{best_scenario}' (avg: {scenario_performance[best_scenario]:.1f}/10)")
        insights.append(
            f"📊 Worst Scenario: '{worst_scenario}' (avg: {scenario_performance[worst_scenario]:.1f}/10)")

        # Response time analysis
        avg_response_time = self.df['webhook_response_time'].mean()
        if avg_response_time > 10:
            insights.append(
                f"⏱️ Average response time is {avg_response_time:.1f}s. Consider optimizing webhook processing.")

        # Vegan detection accuracy
        avg_vegan_score = self.df['fresh_vegan_score'].mean()
        if avg_vegan_score < 7:
            insights.append(
                f"🌱 Fresh vegan detection score is {avg_vegan_score:.1f}/10. Consider improving vegan signal detection.")

        # Display insights
        for i, insight in enumerate(insights, 1):
            print(f"{i}. {insight}")

        if not insights:
            print("✅ No major issues detected! Your bot is performing well.")

    def generate_report(self, output_file: str = None):
        """Generate comprehensive report"""
        if self.df.empty:
            print("❌ No data to generate report")
            return

        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"evaluation_report_{timestamp}.txt"

        report_lines = []

        # Capture all output
        import io
        import sys

        # Redirect stdout to capture report content
        original_stdout = sys.stdout
        report_buffer = io.StringIO()
        sys.stdout = report_buffer

        try:
            self.show_overview()
            self.analyze_performance_trends()
            self.analyze_failure_patterns()
            self.suggest_improvements()

            # Get captured output
            report_content = report_buffer.getvalue()

        finally:
            sys.stdout = original_stdout

        # Save to file
        with open(output_file, 'w') as f:
            f.write(f"SHANNON'S BOT EVALUATION REPORT\n")
            f.write(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Database: {self.db_path}\n")
            f.write("=" * 60 + "\n\n")
            f.write(report_content)

        print(f"📄 Report saved to: {output_file}")

        # Also print to console
        print(report_content)


def main():
    """Main analyzer function"""

    analyzer = EvaluationAnalyzer()

    if analyzer.df.empty:
        print("❌ No evaluation data found. Run some tests first!")
        return

    print("📊 SHANNON'S BOT EVALUATION ANALYZER")
    print("=" * 50)

    while True:
        print("\n🔍 ANALYSIS OPTIONS:")
        print("1. Show Overview")
        print("2. Performance Trends")
        print("3. Failure Analysis")
        print("4. Improvement Suggestions")
        print("5. Generate Full Report")
        print("6. Exit")

        choice = input("\nSelect option (1-6): ").strip()

        try:
            if choice == "1":
                analyzer.show_overview()
            elif choice == "2":
                analyzer.analyze_performance_trends()
            elif choice == "3":
                analyzer.analyze_failure_patterns()
            elif choice == "4":
                analyzer.suggest_improvements()
            elif choice == "5":
                analyzer.generate_report()
            elif choice == "6":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Please enter 1, 2, 3, 4, 5, or 6")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
