import os
import json
from datetime import datetime


def list_batch_files():
    """List all available batch files for processing"""
    batch_dir = "batch_processing"

    if not os.path.exists(batch_dir):
        print("📁 No batch processing directory found")
        print("💡 Run the main script first to generate batch files when vegan influencers are found")
        return

    batch_files = [f for f in os.listdir(batch_dir) if f.endswith('.json')]

    if not batch_files:
        print("📁 No batch files found")
        print("💡 Run the main script first to generate batch files when vegan influencers are found")
        return

    print(f"🗂️  AVAILABLE BATCH FILES ({len(batch_files)} total):")
    print("=" * 70)

    for i, filename in enumerate(sorted(batch_files), 1):
        filepath = os.path.join(batch_dir, filename)

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            influencer = data.get('influencer_username', 'Unknown')
            total = data.get('total_followers', 0)
            processed = data.get('processed_count', 0)
            status = data.get('status', 'pending')
            is_vegan = data.get('is_vegan_influencer', False)
            created = data.get('created_timestamp', '')

            # Calculate progress
            progress = (processed / total * 100) if total > 0 else 0

            print(f"\n{i:2d}. {filename}")
            print(
                f"    🌱 Influencer: @{influencer} {'🌿 (VEGAN)' if is_vegan else ''}")
            print(f"    📊 Progress: {processed}/{total} ({progress:.1f}%)")
            print(f"    📅 Created: {created[:19] if created else 'Unknown'}")
            print(f"    ⚡ Status: {status.upper()}")

            if status == 'pending':
                remaining = total - processed
                print(f"    🎯 Ready to process: {remaining} followers")
                print(
                    f"    💡 Command: python find_potential_clients.py --batch-file \"{filepath}\" --batch-size 20")

        except Exception as e:
            print(f"\n{i:2d}. {filename} (ERROR: {e})")

    print("\n" + "=" * 70)
    print("💡 USAGE:")
    print("   python find_potential_clients.py --batch-file \"batch_processing/FILENAME.json\"")
    print("   python find_potential_clients.py --batch-file \"batch_processing/FILENAME.json\" --batch-size 50")


if __name__ == "__main__":
    list_batch_files()
