import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def rename_user_files():
    # Path to the by_user directory
    by_user_dir = os.path.join('app', 'by_user')

    if not os.path.exists(by_user_dir):
        logger.error(f"Directory {by_user_dir} does not exist")
        return

    renamed_count = 0

    # Get list of files in directory
    files = os.listdir(by_user_dir)
    total_files = len(files)
    logger.info(f"Found {total_files} files in directory")

    for filename in files:
        if filename.startswith('user_'):
            old_path = os.path.join(by_user_dir, filename)
            new_filename = filename[5:]  # Remove 'user_' prefix
            new_path = os.path.join(by_user_dir, new_filename)

            try:
                os.rename(old_path, new_path)
                renamed_count += 1
                logger.info(f"Renamed {filename} to {new_filename}")
            except Exception as e:
                logger.error(f"Error renaming {filename}: {str(e)}")

    logger.info(f"Renamed {renamed_count} files")
    logger.info(
        f"Files remaining in directory: {len(os.listdir(by_user_dir))}")


if __name__ == "__main__":
    rename_user_files()
