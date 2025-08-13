import ast
import sys

try:
    with open('check_daily_follow_backs.py', 'r', encoding='utf-8') as f:
        source_code = f.read()

    ast.parse(source_code)
    print("✅ Syntax is valid!")

except SyntaxError as e:
    print(f"❌ Syntax Error:")
    print(f"Line {e.lineno}: {e.text}")
    print(f"Error: {e.msg}")
    print(f"Position: {' ' * (e.offset - 1)}^")

except Exception as e:
    print(f"❌ Other Error: {e}")
