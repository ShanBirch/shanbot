"""
Fix for emoji encoding issues in Windows console
"""

# Create aliases for common emojis that might cause issues
import builtins
CHECK_MARK = "[PASS]"  # Instead of ✅
CROSS_MARK = "[FAIL]"  # Instead of ❌
WARNING = "[WARN]"  # Instead of ⚠️
INFO = "[INFO]"  # Instead of ℹ️
HOURGLASS = "[WAIT]"  # Instead of ⏳

# Function to replace emojis in a string with their text alternatives


def fix_emojis(text):
    replacements = {
        "✅": CHECK_MARK,
        "❌": CROSS_MARK,
        "⚠️": WARNING,
        "ℹ️": INFO,
        "⏳": HOURGLASS,
    }

    for emoji, replacement in replacements.items():
        text = text.replace(emoji, replacement)

    return text


# Override the built-in print function with one that fixes emojis
original_print = print


def emoji_safe_print(*args, **kwargs):
    # Convert all arguments to strings and fix emojis
    new_args = []
    for arg in args:
        if isinstance(arg, str):
            new_args.append(fix_emojis(arg))
        else:
            new_args.append(arg)

    # Call the original print function with the fixed arguments
    return original_print(*new_args, **kwargs)


# Replace the built-in print function with our emoji-safe version
builtins.print = emoji_safe_print
