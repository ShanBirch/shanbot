import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup")


def cleanup_user_files():
    """Remove duplicate user files without the user_ prefix"""
    user_dir = Path(__file__).parent / 'app' / 'by_user'

    if not user_dir.exists():
        logger.error(f"User directory not found: {user_dir}")
        return

    # Get all JSON files
    all_files = list(user_dir.glob('*.json'))

    # Group files by Instagram username
    username_files = {}
    for file in all_files:
        # Get base name without .json
        base_name = file.stem

        # If it starts with user_, strip that prefix for grouping
        if base_name.startswith('user_'):
            username = base_name[5:]  # Remove 'user_' prefix
        else:
            username = base_name

        if username not in username_files:
            username_files[username] = []
        username_files[username].append(file)

    # Process each group
    deleted_count = 0
    for username, files in username_files.items():
        if len(files) > 1:
            # Find files without user_ prefix
            to_delete = [f for f in files if not f.stem.startswith('user_')]

            # Delete files without prefix
            for file in to_delete:
                try:
                    file.unlink()
                    logger.info(f"Deleted duplicate file: {file}")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting {file}: {e}")

    logger.info(f"Cleanup complete. Deleted {deleted_count} duplicate files.")
    logger.info(f"Remaining files: {len(list(user_dir.glob('*.json')))}")


if __name__ == "__main__":
    cleanup_user_files()
