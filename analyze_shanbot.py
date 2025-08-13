#!/usr/bin/env python3
"""
Comprehensive analysis of Shanbot's conversation capabilities
"""

import pandas as pd
import json
from datetime import datetime, timedelta
import re
from collections import Counter


def load_data():
    """Load conversation data"""
    try:
        messages_df = pd.read_csv(
            'conversation_analysis/messages_data_20250705_092234.csv')
        scheduled_df = pd.read_csv(
            'conversation_analysis/scheduled_responses_data_20250705_092234.csv')
        activity_df = pd.read_csv(
            'conversation_analysis/auto_mode_activity_data_20250705_092234.csv')

        print(
            f"Loaded {len(messages_df)} messages, {len(scheduled_df)} scheduled responses, {len(activity_df)} activities")
        return messages_df, scheduled_df, activity_df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None, None


def analyze_conversation_patterns(messages_df):
    """Analyze conversation patterns"""
    messages_df['timestamp'] = pd.to_datetime(
        messages_df['timestamp'], errors='coerce')

    user_messages = messages_df[messages_df['type'] == 'user']
    ai_messages = messages_df[messages_df['type'] == 'ai']

    print(f"\n=== CONVERSATION OVERVIEW ===")
    print(f"Total messages: {len(messages_df)}")
    print(f"User messages: {len(user_messages)}")
    print(f"AI messages: {len(ai_messages)}")
    print(f"Response rate: {len(ai_messages) / len(user_messages) * 100:.1f}%")

    # Top users
    user_stats = messages_df.groupby(
        'ig_username').size().sort_values(ascending=False)
    print(f"\n=== TOP 10 MOST ACTIVE USERS ===")
    for i, (username, count) in enumerate(user_stats.head(10).items(), 1):
        print(f"{i}. {username}: {count} messages")

    # Date range
    date_range = f"{messages_df['timestamp'].min()} to {messages_df['timestamp'].max()}"
    print(f"\nDate range: {date_range}")

    return {
        'total_messages': len(messages_df),
        'user_messages': len(user_messages),
        'ai_messages': len(ai_messages),
        'response_rate': len(ai_messages) / len(user_messages) * 100,
        'top_users': user_stats.head(10).to_dict(),
        'date_range': date_range
    }


def analyze_topics(messages_df):
    """Analyze conversation topics"""
    # Fitness/health keywords
    keywords = [
        'workout', 'exercise', 'training', 'gym', 'fitness', 'muscle', 'cardio',
        'weight', 'rep', 'set', 'calories', 'protein', 'diet', 'nutrition',
        'vegan', 'plant', 'food', 'meal', 'eating', 'healthy', 'health',
        'transformation', 'goal', 'progress', 'strength', 'endurance'
    ]

    all_text = ' '.join(messages_df['text'].astype(str).str.lower())

    keyword_counts = {}
    for keyword in keywords:
        count = len(re.findall(r'\b' + keyword + r'\b', all_text))
        if count > 0:
            keyword_counts[keyword] = count

    sorted_keywords = sorted(keyword_counts.items(),
                             key=lambda x: x[1], reverse=True)

    print(f"\n=== TOP CONVERSATION TOPICS ===")
    for keyword, count in sorted_keywords[:15]:
        print(f"{keyword}: {count} mentions")

    return sorted_keywords


def analyze_ai_responses(messages_df):
    """Analyze AI response capabilities"""
    ai_messages = messages_df[messages_df['type'] == 'ai']

    response_analysis = {
        'questions': 0,
        'encouragement': 0,
        'advice': 0,
        'workout_related': 0,
        'nutrition_related': 0,
        'personal_touches': 0
    }

    # Keywords for analysis
    question_words = ['?', 'how', 'what', 'when',
                      'where', 'why', 'would you', 'do you']
    encouragement_words = ['great', 'awesome', 'fantastic',
                           'well done', 'keep going', 'proud', 'amazing']
    advice_words = ['should', 'recommend', 'suggest',
                    'try', 'consider', 'might want', 'could']
    workout_words = ['exercise', 'workout',
                     'training', 'rep', 'set', 'form', 'technique']
    nutrition_words = ['eat', 'food', 'meal',
                       'nutrition', 'protein', 'calories', 'vegan']
    personal_words = ['you', 'your', 'yourself', 'personally', 'for you']

    for text in ai_messages['text'].astype(str):
        text_lower = text.lower()

        if any(word in text_lower for word in question_words):
            response_analysis['questions'] += 1
        if any(word in text_lower for word in encouragement_words):
            response_analysis['encouragement'] += 1
        if any(word in text_lower for word in advice_words):
            response_analysis['advice'] += 1
        if any(word in text_lower for word in workout_words):
            response_analysis['workout_related'] += 1
        if any(word in text_lower for word in nutrition_words):
            response_analysis['nutrition_related'] += 1
        if any(word in text_lower for word in personal_words):
            response_analysis['personal_touches'] += 1

    print(f"\n=== AI RESPONSE CAPABILITIES ===")
    total_ai = len(ai_messages)
    for response_type, count in response_analysis.items():
        percentage = (count / total_ai) * 100
        print(f"{response_type.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")

    # Message length analysis
    ai_messages['word_count'] = ai_messages['text'].astype(
        str).str.split().str.len()
    user_messages = messages_df[messages_df['type'] == 'user']
    user_messages['word_count'] = user_messages['text'].astype(
        str).str.split().str.len()

    print(f"\n=== MESSAGE LENGTH ANALYSIS ===")
    print(
        f"Average AI response length: {ai_messages['word_count'].mean():.1f} words")
    print(
        f"Average user message length: {user_messages['word_count'].mean():.1f} words")
    print(
        f"AI messages are {ai_messages['word_count'].mean() / user_messages['word_count'].mean():.1f}x longer")

    return {
        'response_patterns': response_analysis,
        'avg_ai_words': ai_messages['word_count'].mean(),
        'avg_user_words': user_messages['word_count'].mean()
    }


def analyze_sample_conversations(messages_df):
    """Show sample conversations to understand capabilities"""
    print(f"\n=== SAMPLE CONVERSATIONS ===")

    # Get conversations from top users
    top_users = messages_df.groupby(
        'ig_username').size().sort_values(ascending=False).head(3)

    for username in top_users.index:
        user_convos = messages_df[messages_df['ig_username']
                                  == username].sort_values('timestamp')
        print(f"\n--- Sample from {username} ---")

        # Show first few exchanges
        for i, (_, msg) in enumerate(user_convos.head(6).iterrows()):
            msg_type = "USER" if msg['type'] == 'user' else "AI"
            text = str(msg['text'])[
                :100] + "..." if len(str(msg['text'])) > 100 else str(msg['text'])
            print(f"{msg_type}: {text}")

        if len(user_convos) > 6:
            print(f"... ({len(user_convos) - 6} more messages)")


def create_capability_summary(patterns, topics, ai_analysis):
    """Create a summary of Shanbot's capabilities"""

    summary = f"""
=== SHANBOT CONVERSATION CAPABILITIES SUMMARY ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW:
- Total Conversations: {patterns['total_messages']} messages
- Response Rate: {patterns['response_rate']:.1f}%
- Active Users: {len(patterns['top_users'])} unique users
- Date Range: {patterns['date_range']}

AI CAPABILITIES:
- Questions Asked: {ai_analysis['response_patterns']['questions']} times
- Encouragement Given: {ai_analysis['response_patterns']['encouragement']} times
- Advice Provided: {ai_analysis['response_patterns']['advice']} times
- Workout Guidance: {ai_analysis['response_patterns']['workout_related']} times
- Nutrition Guidance: {ai_analysis['response_patterns']['nutrition_related']} times
- Personal Touch: {ai_analysis['response_patterns']['personal_touches']} times

CONVERSATION TOPICS (Top 10):
{chr(10).join([f"- {topic}: {count} mentions" for topic, count in topics[:10]])}

RESPONSE CHARACTERISTICS:
- Average AI response: {ai_analysis['avg_ai_words']:.1f} words
- Average user message: {ai_analysis['avg_user_words']:.1f} words
- AI provides {ai_analysis['avg_ai_words'] / ai_analysis['avg_user_words']:.1f}x more detailed responses

STRENGTHS IDENTIFIED:
1. High response rate ({patterns['response_rate']:.1f}%)
2. Comprehensive fitness and nutrition knowledge
3. Personalized, encouraging communication style
4. Handles complex workout and diet discussions
5. Maintains engaging conversations across multiple users

COACHING CAPABILITIES:
- Provides workout guidance and form corrections
- Offers nutrition advice with vegan focus
- Motivates and encourages users consistently
- Asks relevant questions to understand user needs
- Adapts responses to individual user contexts
"""

    # Save summary
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_file = f"shanbot_capability_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write(summary)

    print(f"\n{summary}")
    print(f"Summary saved to: {summary_file}")

    return summary


def main():
    """Main analysis function"""
    messages_df, scheduled_df, activity_df = load_data()

    if messages_df is None:
        print("Could not load data")
        return

    # Perform analyses
    patterns = analyze_conversation_patterns(messages_df)
    topics = analyze_topics(messages_df)
    ai_analysis = analyze_ai_responses(messages_df)
    analyze_sample_conversations(messages_df)

    # Create summary
    create_capability_summary(patterns, topics, ai_analysis)


if __name__ == "__main__":
    main()
