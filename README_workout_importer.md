# Workout Data Importer for SQLite

This script automatically imports workout session data from your check-in JSON files into your SQLite database for dashboard display.

## What It Does

- **Monitors** the `output/checkin_reviews/` directory for new `*_fitness_wrapped_data.json` files
- **Extracts** detailed workout sessions, exercises, and performance data
- **Imports** this data into your SQLite database workout tables
- **Tracks** processed files to avoid duplicates
- **Logs** all operations for debugging

## How to Run

### 1. One-Time Import (Process All Recent Files)
```bash
python import_workout_data_to_sqlite.py --once
```
This will process all JSON files from the last 7 days that haven't been imported yet.

### 2. Continuous Monitoring (Recommended)
```bash
python import_workout_data_to_sqlite.py
```
This will run continuously, checking for new files every 30 seconds.

### 3. Process a Specific File
```bash
python import_workout_data_to_sqlite.py --file "path/to/ClientName_2025-01-06_fitness_wrapped_data.json"
```

### 4. Custom Time Range
```bash
python import_workout_data_to_sqlite.py --once --days 30
```
Process files from the last 30 days instead of default 7 days.

## Integration with Your Workflow

### Option A: Run After Check-ins
Add this to the end of your `checkin_good_110525.py` script:
```python
# At the end of your check-in process
import subprocess
subprocess.run(["python", "import_workout_data_to_sqlite.py", "--once"], check=False)
```

### Option B: Run as Background Service
Start the monitor and let it run continuously:
```bash
python import_workout_data_to_sqlite.py
```
Press Ctrl+C to stop.

### Option C: Schedule with Task Scheduler (Windows)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to run every hour
4. Set action to run: `python import_workout_data_to_sqlite.py --once`

## What Gets Imported

For each workout session in your JSON files:
- **Client Information**: Name and Instagram username
- **Workout Details**: Name, date, exercises
- **Exercise Data**: Sets, reps, weights, performance metrics
- **Raw Data**: Complete JSON for advanced analysis
- **Metadata**: Import timestamp and source tracking

## Files Created

- `processed_workout_files.json` - Tracks which files have been processed
- `workout_data_importer.log` - Detailed operation logs

## Dashboard Integration

Once imported, your workout data will be available in your dashboard through the SQLite database. The data appears in:

- **Client Progress Tracking**
- **Workout History Views** 
- **Performance Analytics**
- **Progress Visualization**

## Troubleshooting

### Common Issues

1. **Import errors**: Check the log file for details
2. **Database connection issues**: Ensure SQLite database exists
3. **File permissions**: Make sure the script can read the JSON files

### Log Files
Check `workout_data_importer.log` for detailed operation logs and error messages.

### Verification
After running, check your dashboard to confirm workout data appears correctly.

## Configuration

Edit the script to customize:
- `CHECKIN_REVIEWS_DIR`: Path to your checkin reviews folder
- `CHECK_INTERVAL`: How often to check for new files (seconds)
- `MAX_FILE_AGE_DAYS`: How far back to look for files

## Support

If you encounter issues:
1. Check the log file for error details
2. Verify file paths and permissions
3. Test with a single file using `--file` option
4. Ensure SQLite utility functions are working 