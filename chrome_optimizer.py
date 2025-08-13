"""
🧈 BUTTER SMOOTH CHROME CONFIG
Memory-optimized Chrome settings for Instagram automation
"""

from selenium.webdriver.chrome.options import Options
import psutil


def get_optimized_chrome_options(profile_path=None):
    """Returns butter-smooth Chrome options for automation"""
    options = Options()

    # MEMORY OPTIMIZATIONS
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--memory-pressure-off")
    options.add_argument("--max_old_space_size=2048")

    # SPEED OPTIMIZATIONS
    options.add_argument("--disable-images")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")

    # CRASH PREVENTION
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--log-level=3")

    # INSTAGRAM OPTIMIZATIONS
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    if profile_path:
        options.add_argument(f"--user-data-dir={profile_path}")

    return options


def check_memory_safe():
    """Check if memory usage is safe for automation"""
    return psutil.virtual_memory().percent < 85


def get_memory_status():
    """Get current memory status"""
    mem = psutil.virtual_memory()
    return f"RAM: {mem.percent}% ({mem.available / (1024**3):.1f}GB available)"


print("✅ Chrome Optimizer loaded! Use get_optimized_chrome_options() in your scripts")
