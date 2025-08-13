import re

# Read the file
with open('app/dashboard_modules/dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Function to add
function_code = '''

# --- Instagram Analysis Functions ---

def trigger_instagram_analysis_for_user(ig_username: str) -> tuple[bool, str]:
    """
    Trigger Instagram analysis for a specific user by calling anaylize_followers.py
    
    Args:
        ig_username: The Instagram username to analyze
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Create a temporary file with the username
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(ig_username)
            temp_file_path = temp_file.name
        
        # Path to the analyzer script
        analyzer_script_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\anaylize_followers.py"
        
        if not os.path.exists(analyzer_script_path):
            return False, f"❌ Analyzer script not found at {analyzer_script_path}"
        
        # Run the analyzer script with the temporary file
        cmd = ["python", analyzer_script_path, "--followers-list", temp_file_path]
        
        # Execute the command
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300,  # 5 minute timeout
            cwd=os.path.dirname(analyzer_script_path)
        )
        
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except Exception as cleanup_error:
            st.warning(f"Could not delete temporary file: {cleanup_error}")
        
        if result.returncode == 0:
            return True, f"✅ Instagram analysis completed successfully for {ig_username}"
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            return False, f"❌ Analysis failed for {ig_username}: {error_msg[:200]}..."
            
    except subprocess.TimeoutExpired:
        return False, f"❌ Analysis timed out for {ig_username} (took longer than 5 minutes)"
    except Exception as e:
        return False, f"❌ Error triggering analysis for {ig_username}: {str(e)}"

# --- End Instagram Analysis Functions ---

'''

# Find the location after the Gemini configuration and before call_gemini_with_retry_sync
pattern = r'(.*?st\.info\("Gemini API Key not configured\. AI features disabled\."\)\s*\n\s*)(def call_gemini_with_retry_sync.*)'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Insert the function between the config and call_gemini_with_retry_sync
    new_content = match.group(1) + function_code + match.group(2)

    # Write back to file
    with open('app/dashboard_modules/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

    print('✅ Function added successfully!')
else:
    print('❌ Could not find the right location to add the function')
    print('Trying to add at the end of configuration section...')

    # Fallback: add before the first function definition
    pattern2 = r'(.*?st\.info\("Gemini API Key not configured\. AI features disabled\."\)\s*\n)(.*)'
    match2 = re.search(pattern2, content, re.DOTALL)
    if match2:
        new_content = match2.group(1) + function_code + match2.group(2)
        with open('app/dashboard_modules/dashboard.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('✅ Function added successfully (fallback method)!')
    else:
        print('❌ Could not add function anywhere')
