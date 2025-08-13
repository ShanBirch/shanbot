"""
Windows Task Scheduler Setup for Instagram Lead Automation
Creates two scheduled tasks:
1. Lead Following: Daily at 5:00 AM
2. Follow-back Checking: Daily at 4:00 PM
"""

import os
import subprocess
from pathlib import Path


def create_task_scheduler_automation():
    """Create Windows Task Scheduler tasks for automated Instagram lead management"""

    # Paths
    shanbot_dir = Path(__file__).parent.absolute()
    python_exe = f'"{shanbot_dir}/venv/Scripts/python.exe"' if (
        shanbot_dir / "venv").exists() else "python"

    # Task 1: Lead Following (5:00 AM daily)
    lead_following_script = shanbot_dir / \
        "smart_lead_finder.py"  # or dual_mode_smart_finder.py
    follow_task_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Daily Instagram lead following at 5:00 AM</Description>
    <Author>Shannon</Author>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2025-07-03T05:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions>
    <Exec>
      <Command>{python_exe}</Command>
      <Arguments>"{lead_following_script}"</Arguments>
      <WorkingDirectory>{shanbot_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

    # Task 2: Follow-back Checking (4:00 PM daily)
    followback_script = shanbot_dir / "check_daily_follow_backs.py"
    followback_task_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Daily Instagram follow-back checking at 4:00 PM</Description>
    <Author>Shannon</Author>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2025-07-03T16:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT3H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions>
    <Exec>
      <Command>{python_exe}</Command>
      <Arguments>"{followback_script}" --analyze-profiles</Arguments>
      <WorkingDirectory>{shanbot_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

    # Save task XML files
    follow_task_file = shanbot_dir / "lead_following_task.xml"
    followback_task_file = shanbot_dir / "followback_checking_task.xml"

    with open(follow_task_file, 'w', encoding='utf-16') as f:
        f.write(follow_task_xml)

    with open(followback_task_file, 'w', encoding='utf-16') as f:
        f.write(followback_task_xml)

    print("📁 Task XML files created:")
    print(f"   - {follow_task_file}")
    print(f"   - {followback_task_file}")
    print()

    # Instructions for manual setup
    print("🔧 SETUP INSTRUCTIONS:")
    print("1. Open Task Scheduler (search 'Task Scheduler' in Start menu)")
    print("2. Click 'Import Task...' in the Actions panel")
    print(f"3. Import: {follow_task_file}")
    print("4. Import: {followback_task_file}")
    print("5. Verify both tasks are enabled and scheduled correctly")
    print()

    print("📅 SCHEDULE SUMMARY:")
    print("   🌅 5:00 AM - Lead Following (finds and follows new prospects)")
    print("   🌙 4:00 PM - Follow-back Checking (processes previous day's follows)")
    print()

    print("⚙️ TASK SETTINGS:")
    print("   - Runs only when network is available")
    print("   - Ignores new instances if already running")
    print("   - 2-3 hour timeout limits")
    print("   - Starts even if missed (catch-up)")

    # Alternative: PowerShell commands for advanced users
    print()
    print("💻 ALTERNATIVE - PowerShell Commands (run as Administrator):")
    print(
        f'schtasks /create /xml "{follow_task_file}" /tn "Instagram Lead Following"')
    print(
        f'schtasks /create /xml "{followback_task_file}" /tn "Instagram Followback Checking"')


if __name__ == "__main__":
    create_task_scheduler_automation()
