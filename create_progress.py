import json

# Create initial progress file marking first 4 batches as completed
progress_data = {
    'last_completed_batch': 4,  # First 4 batches completed
    'batch_size': 50,  # Match the batch size in the main script
    'total_profiles': 221,  # Total number of profiles to process
    'processed_usernames': [
        # Add any usernames you know were successfully processed
        # Leave empty if unsure, better to reprocess than to skip
    ]
}

# Save progress file
with open('analysis_progress.json', 'w') as f:
    json.dump(progress_data, f, indent=2)

print("Created progress file marking first 4 batches as completed")
print(
    f"Next batch will start at profile {progress_data['last_completed_batch'] * progress_data['batch_size'] + 1}")
