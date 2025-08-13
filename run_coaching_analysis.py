#!/usr/bin/env python3
"""
Script to run coaching potential analysis on all users in the SQLite database.
This will generate the missing coaching scores for the High Potential Clients dashboard.
"""

from identify_potential_clients_sqlite import analyze_all_followers_for_coaching_sqlite, get_high_potential_clients_sqlite
import sys
import os

# Add the current directory to Python path
sys.path.append(os.getcwd())


def main():
    print("🎯 Running Coaching Potential Analysis")
    print("=" * 50)

    print("📊 This will analyze all users in your SQLite database...")
    print("   - Generate coaching potential scores (0-100)")
    print("   - Identify high-potential vegetarian/vegan fitness clients")
    print("   - Update the database with analysis results")

    # Ask for confirmation
    response = input("\n🤔 Do you want to proceed? (y/n): ").strip().lower()

    if response != 'y':
        print("❌ Analysis cancelled.")
        return

    print("\n🚀 Starting analysis...")

    try:
        # Run the analysis
        success = analyze_all_followers_for_coaching_sqlite()

        if success:
            print("\n✅ Analysis completed successfully!")

            # Show results
            print("\n📊 Checking results...")
            high_potential_clients = get_high_potential_clients_sqlite(
                min_score=50)

            print(
                f"🎯 Found {len(high_potential_clients)} high-potential clients (score ≥ 50)")

            if high_potential_clients:
                print("\n🌟 Top 10 prospects:")
                sorted_clients = sorted(
                    high_potential_clients, key=lambda x: x['score'], reverse=True)

                for i, client in enumerate(sorted_clients[:10], 1):
                    print(
                        f"{i:2d}. {client['username']:<20} Score: {client['score']:3d} ({client['category']})")

            print(f"\n🎉 Success! Refresh your dashboard to see the results.")
            print("   Dashboard URL: http://localhost:8501")

        else:
            print("\n❌ Analysis failed. Check the logs for details.")

    except Exception as e:
        print(f"\n❌ Error running analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
