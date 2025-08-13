#!/usr/bin/env python3
"""
Analyze Gemini errors in recent conversations
"""

import re
from datetime import datetime


def analyze_gemini_errors():
    """Read the recent conversations and identify Gemini errors"""

    # Read the conversation file
    with open('recent_conversations_20250705_102519.txt', 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into conversations
    conversations = content.split('📱 CONVERSATION WITH: ')

    errors_found = []

    for convo in conversations[1:]:  # Skip the header
        if not convo.strip():
            continue

        lines = convo.strip().split('\n')
        username = lines[0].split('(')[0].strip()

        ai_responses = []
        user_messages = []

        # Extract messages
        for line in lines:
            if '🤖 AI' in line:
                # Get the next line which should be the AI response
                idx = lines.index(line)
                if idx + 1 < len(lines):
                    response = lines[idx + 1].strip()
                    ai_responses.append(response)
            elif '👤 USER' in line:
                idx = lines.index(line)
                if idx + 1 < len(lines):
                    user_msg = lines[idx + 1].strip()
                    user_messages.append(user_msg)

        # Analyze errors for this conversation
        convo_errors = analyze_conversation_errors(
            username, ai_responses, user_messages)
        if convo_errors:
            errors_found.extend(convo_errors)

    # Print analysis
    print("=== GEMINI ERROR ANALYSIS ===")
    print(f"Total conversations analyzed: {len(conversations)-1}")
    print(f"Total errors found: {len(errors_found)}")
    print("=" * 50)

    # Group errors by type
    error_types = {}
    for error in errors_found:
        error_type = error['type']
        if error_type not in error_types:
            error_types[error_type] = []
        error_types[error_type].append(error)

    # Display errors by type
    for error_type, errors in error_types.items():
        print(f"\n🚨 {error_type.upper()} ERRORS ({len(errors)} found):")
        print("-" * 40)
        for error in errors:
            print(f"User: {error['username']}")
            print(f"Issue: {error['description']}")
            print(f"Response: {error['response'][:100]}...")
            print()


def analyze_conversation_errors(username, ai_responses, user_messages):
    """Analyze errors in a single conversation"""
    errors = []

    for response in ai_responses:
        # Check word count (should be max 15 words)
        word_count = len(response.split())
        if word_count > 15:
            errors.append({
                'username': username,
                'type': 'length_violation',
                'description': f'Response too long: {word_count} words (max 15)',
                'response': response
            })

        # Check for obvious AI language patterns
        ai_patterns = [
            'I\'m an AI', 'as an AI', 'I don\'t have personal', 'I can\'t actually',
            'I\'m not able to', 'I don\'t have the ability', 'I\'m programmed to'
        ]

        for pattern in ai_patterns:
            if pattern.lower() in response.lower():
                errors.append({
                    'username': username,
                    'type': 'ai_reveal',
                    'description': f'Response reveals AI nature: "{pattern}"',
                    'response': response
                })

        # Check for repetitive responses
        if response.count('hey') > 3:
            errors.append({
                'username': username,
                'type': 'repetitive_language',
                'description': 'Overuse of "hey" (Australian filler)',
                'response': response
            })

        # Check for context mismatches
        if 'haha looks like you' in response.lower() and 'chat' in response.lower():
            errors.append({
                'username': username,
                'type': 'context_error',
                'description': 'Incorrectly assumes user copied chat',
                'response': response
            })

        # Check for overly formal language (not Shannon's style)
        formal_phrases = ['I understand', 'I appreciate',
                          'furthermore', 'additionally', 'consequently']
        for phrase in formal_phrases:
            if phrase.lower() in response.lower():
                errors.append({
                    'username': username,
                    'type': 'tone_mismatch',
                    'description': f'Too formal language: "{phrase}"',
                    'response': response
                })

        # Check for missing Australian slang balance
        if word_count > 10 and 'hey' not in response.lower() and 'mate' not in response.lower():
            errors.append({
                'username': username,
                'type': 'tone_mismatch',
                'description': 'Missing Australian casual tone markers',
                'response': response
            })

    return errors


def identify_specific_problems():
    """Identify specific problematic conversations"""

    print("\n=== SPECIFIC PROBLEM CONVERSATIONS ===")

    problems = [
        {
            'user': 'black_monkey_go_green',
            'issue': 'CRITICAL: Mental health crisis - inappropriate response length',
            'description': 'User sharing depression/suicidal thoughts, got massive paragraph response instead of brief supportive message'
        },
        {
            'user': 'thompson.robin',
            'issue': 'AI Detection: User called out chatbot usage',
            'description': 'User said "if you\'re going to use an AI Chatbot to drum up business you need to let people know that"'
        },
        {
            'user': 'nis_somani',
            'issue': 'Context confusion: Repeated full conversation summary',
            'description': 'AI gave long summary of conversation instead of responding to current message'
        },
        {
            'user': 'cocos_pt_studio',
            'issue': 'Misunderstanding: User saying "Dirty dawg" repeatedly',
            'description': 'AI not recognizing this is likely Shannon testing the system'
        }
    ]

    for problem in problems:
        print(f"\n🚨 {problem['user']}:")
        print(f"   Issue: {problem['issue']}")
        print(f"   Problem: {problem['description']}")


if __name__ == "__main__":
    analyze_gemini_errors()
    identify_specific_problems()
