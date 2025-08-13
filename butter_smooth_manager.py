"""
🧈 BUTTER SMOOTH SYSTEM MANAGER
Complete system optimization and monitoring for Shannon's automation
"""

import psutil
import subprocess
import time
from datetime import datetime


class ButterSmoothManager:
    def __init__(self):
        self.memory_threshold = 80  # Restart if above 80%

    def get_system_status(self):
        """Get comprehensive system status"""
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)

        status = {
            'memory_percent': mem.percent,
            'memory_available_gb': mem.available / (1024**3),
            'memory_used_gb': mem.used / (1024**3),
            'cpu_percent': cpu,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        return status

    def get_memory_hogs(self, top_n=10):
        """Find the biggest memory consumers"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                memory_mb = proc.info['memory_info'].rss / (1024 * 1024)
                processes.append({
                    'name': proc.info['name'],
                    'pid': proc.info['pid'],
                    'memory_mb': round(memory_mb, 1)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return sorted(processes, key=lambda x: x['memory_mb'], reverse=True)[:top_n]

    def clean_automation_blockers(self):
        """Clean up processes that block automation"""
        cleaned = []

        # Kill hidden Chrome processes (no window title)
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    # You can add logic here to check if it has a window
                    # For now, we'll be conservative
                    pass
            except:
                pass

        return cleaned

    def is_safe_for_automation(self):
        """Check if system is safe for running automation"""
        mem = psutil.virtual_memory()
        return mem.percent < self.memory_threshold

    def print_status_report(self):
        """Print a comprehensive status report"""
        status = self.get_system_status()
        hogs = self.get_memory_hogs(5)

        print("🧈 BUTTER SMOOTH STATUS REPORT")
        print("=" * 40)
        print(f"⏰ Time: {status['timestamp']}")
        print(
            f"🧠 RAM: {status['memory_percent']:.1f}% ({status['memory_available_gb']:.1f}GB available)")
        print(f"⚡ CPU: {status['cpu_percent']:.1f}%")
        print()

        if status['memory_percent'] > 85:
            print("🚨 HIGH MEMORY WARNING!")
        elif status['memory_percent'] > 75:
            print("⚠️  Memory getting high")
        else:
            print("✅ Memory looks good")

        print()
        print("🔝 TOP MEMORY USERS:")
        for i, proc in enumerate(hogs, 1):
            print(
                f"  {i}. {proc['name']}: {proc['memory_mb']} MB (PID: {proc['pid']})")

        print()
        automation_safe = self.is_safe_for_automation()
        if automation_safe:
            print("🚀 ✅ SAFE FOR AUTOMATION")
        else:
            print("🛑 ❌ NOT SAFE - CLEAN UP FIRST")

        return status

# Quick functions for easy use


def check_system():
    """Quick system check"""
    manager = ButterSmoothManager()
    return manager.print_status_report()


def get_memory_percent():
    """Quick memory check"""
    return psutil.virtual_memory().percent


def is_automation_safe():
    """Quick automation safety check"""
    return psutil.virtual_memory().percent < 80


if __name__ == "__main__":
    check_system()
