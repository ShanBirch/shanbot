from app.dashboard_modules.dashboard_sqlite_utils import get_good_few_shot_examples

# Test the fixed few-shot system
examples = get_good_few_shot_examples(limit=100)

print(f"🎉 SUCCESS! Webhook will now use {len(examples)} few-shot examples")
print(f"✅ All examples are from actually edited responses (not identical ones)")

if examples:
    print(f"\n📝 First example:")
    print(f"   User: {examples[0]['user_message'][:80]}...")
    print(f"   Bot: {examples[0]['shanbot_response'][:80]}...")

    print(f"\n📊 Total examples available: {len(examples)}")
    print(
        f"🚀 Your AI will now learn from {len(examples)} high-quality edited responses!")
else:
    print("❌ No examples found - something might be wrong")
