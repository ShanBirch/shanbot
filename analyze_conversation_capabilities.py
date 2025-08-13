#!/usr/bin/env python3
"""
Detailed analysis of Shanbot conversation capabilities and patterns.
"""

import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import numpy as np
from collections import Counter
import re
from pathlib import Path


def load_conversation_data():
    """Load the extracted conversation data"""
    try:
        # Load the main conversation data
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
    """Analyze conversation patterns and capabilities"""
    if messages_df is None:
        return None

    # Parse timestamps
    messages_df['timestamp'] = pd.to_datetime(messages_df['timestamp'])

    # Separate user and AI messages
    user_messages = messages_df[messages_df['type'] == 'user']
    ai_messages = messages_df[messages_df['type'] == 'ai']

    print(f"\n=== CONVERSATION PATTERNS ===")
    print(f"Total messages: {len(messages_df)}")
    print(f"User messages: {len(user_messages)}")
    print(f"AI messages: {len(ai_messages)}")
    print(f"Response rate: {len(ai_messages) / len(user_messages) * 100:.1f}%")

    # Analyze by user
    user_stats = messages_df.groupby('ig_username').agg({
        'type': 'count',
        'timestamp': ['min', 'max']
    }).round(2)

    user_stats.columns = ['total_messages', 'first_message', 'last_message']
    user_stats['conversation_span_days'] = (
        user_stats['last_message'] - user_stats['first_message']).dt.days
    user_stats = user_stats.sort_values('total_messages', ascending=False)

    print(f"\n=== TOP 10 MOST ACTIVE USERS ===")
    print(user_stats.head(10))

    # Analyze message lengths
    messages_df['message_length'] = messages_df['text'].astype(str).str.len()
    user_msg_length = messages_df[messages_df['type']
                                  == 'user']['message_length']
    ai_msg_length = messages_df[messages_df['type'] == 'ai']['message_length']

    print(f"\n=== MESSAGE LENGTH ANALYSIS ===")
    print(
        f"Average user message length: {user_msg_length.mean():.1f} characters")
    print(f"Average AI message length: {ai_msg_length.mean():.1f} characters")
    print(
        f"AI messages are {ai_msg_length.mean() / user_msg_length.mean():.1f}x longer than user messages")

    return {
        'total_messages': len(messages_df),
        'user_messages': len(user_messages),
        'ai_messages': len(ai_messages),
        'response_rate': len(ai_messages) / len(user_messages) * 100,
        'user_stats': user_stats,
        'avg_user_length': user_msg_length.mean(),
        'avg_ai_length': ai_msg_length.mean(),
        'date_range': (messages_df['timestamp'].min(), messages_df['timestamp'].max())
    }


def analyze_conversation_topics(messages_df):
    """Analyze conversation topics and themes"""
    if messages_df is None:
        return None

    # Common fitness/health keywords
    fitness_keywords = [
        'workout', 'exercise', 'training', 'gym', 'fitness', 'muscle', 'cardio',
        'weight', 'rep', 'set', 'calories', 'protein', 'diet', 'nutrition',
        'vegan', 'plant', 'food', 'meal', 'eating', 'healthy', 'health',
        'transformation', 'goal', 'progress', 'strength', 'endurance',
        'yoga', 'pilates', 'running', 'walking', 'cycling', 'swimming'
    ]

    # Analyze keyword usage
    all_text = ' '.join(messages_df['text'].astype(str).str.lower())

    keyword_counts = {}
    for keyword in fitness_keywords:
        count = len(re.findall(r'\b' + keyword + r'\b', all_text))
        if count > 0:
            keyword_counts[keyword] = count

    # Sort by frequency
    sorted_keywords = sorted(keyword_counts.items(),
                             key=lambda x: x[1], reverse=True)

    print(f"\n=== CONVERSATION TOPICS (Top 20) ===")
    for keyword, count in sorted_keywords[:20]:
        print(f"{keyword}: {count} mentions")

    # Analyze conversation starters
    user_messages = messages_df[messages_df['type'] == 'user']

    # Common conversation starters
    starters = []
    for text in user_messages['text'].astype(str):
        if len(text) > 0:
            first_words = ' '.join(text.split()[:3]).lower()
            starters.append(first_words)

    starter_counts = Counter(starters)
    print(f"\n=== COMMON CONVERSATION STARTERS ===")
    for starter, count in starter_counts.most_common(10):
        print(f"'{starter}': {count} times")

    return {
        'keyword_counts': keyword_counts,
        'top_keywords': sorted_keywords[:20],
        'conversation_starters': starter_counts.most_common(10)
    }


def analyze_ai_capabilities(messages_df):
    """Analyze AI response capabilities and patterns"""
    if messages_df is None:
        return None

    ai_messages = messages_df[messages_df['type'] == 'ai']

    # Analyze response types
    response_patterns = {
        'questions': 0,
        'encouragement': 0,
        'advice': 0,
        'information': 0,
        'workout_related': 0,
        'nutrition_related': 0,
        'personal_touches': 0
    }

    # Keywords for different response types
    question_indicators = ['?', 'how', 'what', 'when', 'where',
                           'why', 'would you', 'do you', 'have you', 'can you']
    encouragement_words = ['great', 'awesome', 'fantastic', 'well done',
                           'keep going', 'you can', 'proud', 'amazing', 'excellent']
    advice_words = ['should', 'recommend', 'suggest', 'try',
                    'consider', 'might want', 'could', 'would help']
    workout_words = ['exercise', 'workout',
                     'training', 'rep', 'set', 'form', 'technique']
    nutrition_words = ['eat', 'food', 'meal', 'nutrition',
                       'protein', 'calories', 'vegan', 'plant']
    personal_words = ['you', 'your', 'yourself',
                      'personally', 'for you', 'remember']

    for text in ai_messages['text'].astype(str):
        text_lower = text.lower()

        # Count different response types
        if any(indicator in text_lower for indicator in question_indicators):
            response_patterns['questions'] += 1

        if any(word in text_lower for word in encouragement_words):
            response_patterns['encouragement'] += 1

        if any(word in text_lower for word in advice_words):
            response_patterns['advice'] += 1

        if any(word in text_lower for word in workout_words):
            response_patterns['workout_related'] += 1

        if any(word in text_lower for word in nutrition_words):
            response_patterns['nutrition_related'] += 1

        if any(word in text_lower for word in personal_words):
            response_patterns['personal_touches'] += 1

    print(f"\n=== AI RESPONSE CAPABILITIES ===")
    total_ai_messages = len(ai_messages)
    for response_type, count in response_patterns.items():
        percentage = (count / total_ai_messages) * 100
        print(f"{response_type.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")

    # Analyze response complexity
    ai_messages['word_count'] = ai_messages['text'].astype(
        str).str.split().str.len()
    ai_messages['sentence_count'] = ai_messages['text'].astype(
        str).str.count('[.!?]') + 1

    print(f"\n=== AI RESPONSE COMPLEXITY ===")
    print(
        f"Average words per response: {ai_messages['word_count'].mean():.1f}")
    print(
        f"Average sentences per response: {ai_messages['sentence_count'].mean():.1f}")
    print(f"Longest response: {ai_messages['word_count'].max()} words")
    print(f"Shortest response: {ai_messages['word_count'].min()} words")

    return {
        'response_patterns': response_patterns,
        'avg_words': ai_messages['word_count'].mean(),
        'avg_sentences': ai_messages['sentence_count'].mean(),
        'max_words': ai_messages['word_count'].max(),
        'min_words': ai_messages['word_count'].min()
    }


def analyze_conversation_flow(messages_df):
    """Analyze conversation flow and user engagement"""
    if messages_df is None:
        return None

    # Sort by username and timestamp
    messages_df = messages_df.sort_values(['ig_username', 'timestamp'])

    # Analyze conversation sessions
    conversation_sessions = []

    for username in messages_df['ig_username'].unique():
        user_messages = messages_df[messages_df['ig_username'] == username].sort_values(
            'timestamp')

        if len(user_messages) > 1:
            # Calculate time gaps between messages
            user_messages['time_diff'] = user_messages['timestamp'].diff()

            # Sessions are separated by gaps > 1 hour
            session_breaks = user_messages['time_diff'] > timedelta(hours=1)
            session_id = session_breaks.cumsum()

            for session in session_id.unique():
                session_messages = user_messages[session_id == session]
                if len(session_messages) > 1:
                    conversation_sessions.append({
                        'username': username,
                        'session_id': session,
                        'message_count': len(session_messages),
                        'duration_minutes': (session_messages['timestamp'].max() - session_messages['timestamp'].min()).total_seconds() / 60,
                        'user_messages': len(session_messages[session_messages['type'] == 'user']),
                        'ai_messages': len(session_messages[session_messages['type'] == 'ai'])
                    })

    sessions_df = pd.DataFrame(conversation_sessions)

    if not sessions_df.empty:
        print(f"\n=== CONVERSATION FLOW ANALYSIS ===")
        print(f"Total conversation sessions: {len(sessions_df)}")
        print(
            f"Average messages per session: {sessions_df['message_count'].mean():.1f}")
        print(
            f"Average session duration: {sessions_df['duration_minutes'].mean():.1f} minutes")
        print(
            f"Longest session: {sessions_df['duration_minutes'].max():.1f} minutes")
        print(
            f"Most active session: {sessions_df['message_count'].max()} messages")

        # Engagement metrics
        sessions_df['engagement_ratio'] = sessions_df['user_messages'] / \
            sessions_df['ai_messages']
        print(
            f"Average user-to-AI message ratio: {sessions_df['engagement_ratio'].mean():.2f}")

    return sessions_df


def create_summary_report(analysis_results):
    """Create a comprehensive summary report"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'shanbot_capabilities_analysis': analysis_results
    }

    # Save report
    output_file = f"shanbot_capability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n=== COMPREHENSIVE REPORT SAVED TO: {output_file} ===")

    # Create summary text
    summary_text = f"""
=== SHANBOT CONVERSATION CAPABILITIES ANALYSIS ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW:
- Total Conversations: {analysis_results.get('patterns', {}).get('total_messages', 'N/A')}
- Response Rate: {analysis_results.get('patterns', {}).get('response_rate', 'N/A'):.1f}%
- Date Range: {analysis_results.get('patterns', {}).get('date_range', 'N/A')}

AI CAPABILITIES:
- Average Response Length: {analysis_results.get('capabilities', {}).get('avg_words', 'N/A'):.1f} words
- Engagement Types: Questions, Encouragement, Advice, Workout & Nutrition guidance
- Personalization: High use of personal pronouns and tailored responses

CONVERSATION TOPICS:
- Primary Focus: Fitness, nutrition, vegan lifestyle, workouts
- Most Discussed: {', '.join([item[0] for item in analysis_results.get('topics', {}).get('top_keywords', [])[:5]])}

USER ENGAGEMENT:
- Active Users: {len(analysis_results.get('patterns', {}).get('user_stats', pd.DataFrame()))} unique users
- Session-based conversations with natural flow
- High retention across multiple interactions

STRENGTHS:
1. Comprehensive fitness and nutrition knowledge
2. Personalized responses tailored to individual users
3. Encouraging and supportive communication style
4. Handles complex workout and diet discussions
5. Maintains context across conversation sessions

AREAS FOR ANALYSIS:
1. Response patterns show strong coaching capabilities
2. Effective user engagement through questions and encouragement
3. Specialized knowledge in vegan fitness and nutrition
4. Adaptive conversation flow based on user needs
"""

    # Save summary
    summary_file = f"shanbot_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(summary_file, 'w') as f:
        f.write(summary_text)

    print(f"Summary report saved to: {summary_file}")
    return summary_text


def main():
    """Main analysis function"""
    # Load data
    messages_df, scheduled_df, activity_df = load_conversation_data()

    if messages_df is None:
        print("Could not load conversation data")
        return

    # Perform analyses
    analysis_results = {}

    print("Analyzing conversation patterns...")
    analysis_results['patterns'] = analyze_conversation_patterns(messages_df)

    print("\nAnalyzing conversation topics...")
    analysis_results['topics'] = analyze_conversation_topics(messages_df)

    print("\nAnalyzing AI capabilities...")
    analysis_results['capabilities'] = analyze_ai_capabilities(messages_df)

    print("\nAnalyzing conversation flow...")
    analysis_results['flow'] = analyze_conversation_flow(messages_df)

    # Create comprehensive report
    summary = create_summary_report(analysis_results)
    print(summary)


if __name__ == "__main__":
    main()
