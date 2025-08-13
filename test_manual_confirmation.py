#!/usr/bin/env python3
"""
Test script for the manual message confirmation function.
This allows you to test the confirmation interface without running the full bot.
"""


def manual_message_confirmation(username, story_description, proposed_comment):
    """
    Allow user to manually confirm, edit, or reject a message before sending.
    Returns: (final_comment, should_send, change_reason)
    """
    print("\n" + "=" * 80)
    print("🔍 MESSAGE CONFIRMATION REQUIRED")
    print("=" * 80)
    print(f"👤 Username: {username}")
    print(f"📖 Story Description: {story_description}")
    print(f"💬 Proposed Comment: '{proposed_comment}'")
    print("=" * 80)

    while True:
        print("\n📋 Options:")
        print("  1. Press ENTER to send the message as-is")
        print("  2. Type 'edit' or 'e' to modify the message")
        print("  3. Type 'skip' or 's' to skip this story")
        print("  4. Type 'quit' or 'q' to stop the bot")

        try:
            user_input = input("\n➤ Your choice: ").strip().lower()

            if user_input == "" or user_input == "1":
                # Send as-is
                print("✅ Sending message as-is...")
                return proposed_comment, True, None

            elif user_input in ["edit", "e", "2"]:
                # Edit the message
                print(f"\n📝 Current message: '{proposed_comment}'")
                new_message = input("➤ Enter new message: ").strip()

                if new_message:
                    # Ask for reason
                    reason = input(
                        "➤ Why did you change the message? (optional): ").strip()
                    if not reason:
                        reason = "User preferred different message"

                    print(f"\n✅ Message updated to: '{new_message}'")
                    print(f"📝 Reason: {reason}")

                    # Confirm the new message
                    confirm = input(
                        "\n➤ Send this new message? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes', '']:
                        print("✅ Sending updated message...")
                        return new_message, True, reason
                    else:
                        print("🔄 Let's try again...")
                        continue
                else:
                    print("❌ Empty message not allowed. Try again.")
                    continue

            elif user_input in ["skip", "s", "3"]:
                # Skip this story
                reason = input("➤ Why are you skipping? (optional): ").strip()
                if not reason:
                    reason = "User chose to skip"
                print(f"⏭️ Skipping story for {username}")
                return None, False, reason

            elif user_input in ["quit", "q", "4"]:
                # Quit the bot
                print("🛑 Stopping bot as requested")
                return None, False, "User requested to quit"

            else:
                print(
                    "❌ Invalid option. Please choose 1, 2, 3, 4, or use the shortcuts.")
                continue

        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user (Ctrl+C)")
            return None, False, "User interrupted with Ctrl+C"
        except Exception as e:
            print(f"❌ Error getting user input: {e}")
            print("⚠️ Defaulting to sending original message...")
            return proposed_comment, True, None


def test_manual_confirmation():
    """Test the manual confirmation function with sample data."""
    print("🧪 Testing Manual Message Confirmation Function")
    print("=" * 60)

    # Sample test data
    test_username = "test_user123"
    test_description = "User is at the gym doing deadlifts with good form"
    test_comment = "Looking strong mate! 💪"

    print("This is a test of the manual confirmation interface.")
    print("Try different options to see how they work:")
    print("- Press ENTER to accept")
    print("- Type 'edit' to modify")
    print("- Type 'skip' to skip")
    print("- Type 'quit' to quit")

    result = manual_message_confirmation(
        test_username, test_description, test_comment)

    print("\n" + "=" * 60)
    print("🔍 TEST RESULTS:")
    print(f"Final comment: {result[0]}")
    print(f"Should send: {result[1]}")
    print(f"Change reason: {result[2]}")
    print("=" * 60)


if __name__ == "__main__":
    test_manual_confirmation()
