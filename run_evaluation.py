#!/usr/bin/env python3
"""
🚀 SHANNON'S BOT AI EVALUATION RUNNER
Simple launcher for massive AI evaluation system
"""

import asyncio
import sys
import os
from ai_evaluation_system import MassiveEvaluationSystem


def main():
    """Main runner function"""

    print("🤖 SHANNON'S BOT EVALUATION SYSTEM")
    print("=" * 50)
    print("🎯 This will test your bot with AI-generated conversations")
    print("📊 Results will be saved to evaluation_results.sqlite")
    print("🔍 Each test includes payload generation, webhook testing, and AI evaluation")
    print()

    # Quick preset options
    print("🚀 QUICK PRESETS:")
    print("1. Quick Test (100 conversations)")
    print("2. Standard Test (1,000 conversations)")
    print("3. Comprehensive Test (5,000 conversations)")
    print("4. Massive Test (10,000 conversations)")
    print("5. Custom amount")
    print()

    while True:
        try:
            choice = input("Select option (1-5): ").strip()

            if choice == "1":
                num_tests = 100
                break
            elif choice == "2":
                num_tests = 1000
                break
            elif choice == "3":
                num_tests = 5000
                break
            elif choice == "4":
                num_tests = 10000
                break
            elif choice == "5":
                while True:
                    try:
                        num_tests = int(
                            input("Enter number of tests (1-10000): "))
                        if 1 <= num_tests <= 10000:
                            break
                        else:
                            print("❌ Please enter a number between 1 and 10,000")
                    except ValueError:
                        print("❌ Please enter a valid number")
                break
            else:
                print("❌ Please enter 1, 2, 3, 4, or 5")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)

    print(f"\n✅ Starting evaluation with {num_tests:,} tests...")
    print("⏳ This may take a while depending on your webhook response times")
    print("🔄 You can press Ctrl+C to stop at any time")
    print()

    # Run the evaluation
    try:
        evaluation_system = MassiveEvaluationSystem()
        asyncio.run(evaluation_system.run_massive_evaluation(
            total_tests=num_tests))
    except KeyboardInterrupt:
        print("\n⚠️ Evaluation stopped by user")
        print("📊 Partial results may be available in evaluation_results.sqlite")
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        print("🔍 Check your webhook URL and API keys")


if __name__ == "__main__":
    main()
