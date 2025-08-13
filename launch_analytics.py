import os
import subprocess

# Get the absolute path to the virtual environment Python
venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'Scripts', 'python.exe')

# Get the absolute path to the analytics dashboard
dashboard_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'analytics_dashboard_new.py')

# Change to the app directory
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))

# Run streamlit
cmd = [venv_python, '-m', 'streamlit', 'run', 'analytics_dashboard_new.py']
subprocess.run(cmd) 