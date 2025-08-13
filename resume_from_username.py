#!/usr/bin/env python3
"""
Utility to resume Instagram analysis from a specific username.
This helps when you get locked out and need to continue from where you left off.
"""

import json
import os


def resume_from_username(target_username, followers_file="instagram_followers.txt", progress_file="analysis_progress.json"):
    """
    Find the position of a username in the followers list and update progress file to resume from there.
    """
    try:
        # Load the followers list
        if not os.path.exists(followers_file):
            print(f"❌ Followers file not found: {followers_file}")
            return False

        with open(followers_file, 'r') as f:
            all_usernames = [line.strip() for line in f if line.strip(
            ) and not line.strip().startswith('#')]

        print(f"📁 Loaded {len(all_usernames)} usernames from {followers_file}")

        # Find the target username
        try:
            target_index = all_usernames.index(target_username)
            print(
                f"🎯 Found '{target_username}' at position {target_index + 1} (index {target_index})")
        except ValueError:
            print(
                f"❌ Username '{target_username}' not found in the followers list")
            return False

        # Calculate which batch this username would be in (with new batch size of 10)
        batch_size = 10
        target_batch = target_index // batch_size
        position_in_batch = target_index % batch_size

        print(
            f"📊 This username is in batch {target_batch + 1}, position {position_in_batch + 1} within that batch")

        # Create or update progress file to resume from the PREVIOUS batch
        # (so we don't skip the problematic username entirely)
        # Start from previous batch to be safe
        resume_batch = max(0, target_batch - 1)

        progress_data = {
            'last_completed_batch': resume_batch,
            'processed_usernames': [],  # Start fresh with processed usernames
            'batch_size': batch_size,
            'resume_note': f"Resumed from {target_username} at index {target_index}, starting from batch {resume_batch + 1}"
        }

        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)

        print(
            f"✅ Updated {progress_file} to resume from batch {resume_batch + 1}")
        print(
            f"📋 The script will now start processing from batch {resume_batch + 1}")
        print(
            f"🔄 This ensures '{target_username}' will be processed again in case it failed")

        # Show what usernames will be processed first
        start_index = resume_batch * batch_size
        # Show first 20
        next_usernames = all_usernames[start_index:start_index + 20]
        print(f"\n📝 Next usernames to process:")
        for i, username in enumerate(next_usernames):
            marker = " ← TARGET" if username == target_username else ""
            print(f"  {start_index + i + 1:4d}. {username}{marker}")

        if len(next_usernames) == 20:
            print("  ... and more")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python resume_from_username.py <username>")
        print("Example: python resume_from_username.py eugen.kdk")
        sys.exit(1)

    target_username = sys.argv[1]
    print(f"🚀 Setting up resume from username: {target_username}")

    success = resume_from_username(target_username)

    if success:
        print(f"\n✅ Ready to resume! Run the main script with:")
        print(f"   python anaylize_followers.py")
        print(f"\n⚠️ Remember: The script now has enhanced safety features:")
        print(f"   - Batch size reduced to 10 profiles")
        print(f"   - 30-120 second delays between profiles")
        print(f"   - 5-15 minute delays between batches")
        print(f"   - Rate limiting detection")
    else:
        print(f"\n❌ Failed to set up resume. Please check the username and try again.")
