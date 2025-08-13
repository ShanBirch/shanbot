#!/usr/bin/env python3
"""
Script to extract ad response data and sign-up link data from the database.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# Database path
DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def get_ad_responses(days_back: int = 30) -> List[Dict]:
    """
    Get list of people who responded to ads in the last N days.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Get users who responded to ads (have lead_source and is_in_ad_flow)
        cursor.execute("""
            SELECT 
                u.ig_username,
                u.subscriber_id,
                u.first_name,
                u.last_name,
                u.lead_source,
                u.ad_script_state,
                u.ad_scenario,
                u.last_interaction_timestamp,
                COUNT(m.id) as message_count
            FROM users u
            LEFT JOIN messages m ON u.ig_username = m.ig_username
            WHERE u.lead_source IS NOT NULL 
            AND u.lead_source != ''
            AND u.is_in_ad_flow = 1
            AND u.last_interaction_timestamp >= ?
            AND u.last_interaction_timestamp <= ?
            GROUP BY u.ig_username
            ORDER BY u.last_interaction_timestamp DESC
        """, (start_date.isoformat(), end_date.isoformat()))

        results = cursor.fetchall()

        ad_responses = []
        for row in results:
            ad_responses.append({
                'ig_username': row[0],
                'subscriber_id': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'lead_source': row[4],
                'ad_script_state': row[5],
                'ad_scenario': row[6],
                'last_interaction': row[7],
                'message_count': row[8]
            })

        conn.close()
        return ad_responses

    except Exception as e:
        print(f"Error getting ad responses: {e}")
        return []


def get_signup_links_sent(days_back: int = 30) -> List[Dict]:
    """
    Get list of people who were sent the sign-up link.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Method 1: Check messages containing various sign-up link patterns
        cursor.execute("""
            SELECT 
                m.ig_username,
                m.subscriber_id,
                m.text,
                m.timestamp,
                u.first_name,
                u.last_name
            FROM messages m
            LEFT JOIN users u ON m.ig_username = u.ig_username
            WHERE (m.text LIKE '%calendly.com/shannonrhysbirch/15min%'
                   OR m.text LIKE '%cocospersonaltraining.com/plantbasedchallenge%'
                   OR m.text LIKE '%cocospersonaltraining.com/coaching-onboarding-form%'
                   OR m.text LIKE '%book a call%'
                   OR m.text LIKE '%schedule a call%'
                   OR m.text LIKE '%calendar link%'
                   OR m.text LIKE '%booking link%')
            AND m.sender = 'ai'
            AND m.timestamp >= ?
            AND m.timestamp <= ?
            ORDER BY m.timestamp DESC
        """, (start_date.isoformat(), end_date.isoformat()))

        message_results = cursor.fetchall()

        # Method 2: Check calendar_link_tracking table if it exists
        calendar_links = []
        try:
            cursor.execute("""
                SELECT 
                    ig_username,
                    subscriber_id,
                    link_sent_timestamp,
                    booking_status
                FROM calendar_link_tracking
                WHERE link_sent_timestamp >= ?
                AND link_sent_timestamp <= ?
                ORDER BY link_sent_timestamp DESC
            """, (start_date.isoformat(), end_date.isoformat()))

            calendar_results = cursor.fetchall()

            for row in calendar_results:
                calendar_links.append({
                    'ig_username': row[0],
                    'subscriber_id': row[1],
                    'link_sent_timestamp': row[2],
                    'booking_status': row[3],
                    'source': 'calendar_tracking'
                })
        except sqlite3.OperationalError:
            print("calendar_link_tracking table not found")

        # Combine and deduplicate results
        signup_links = []

        # Add message-based results
        for row in message_results:
            signup_links.append({
                'ig_username': row[0],
                'subscriber_id': row[1],
                'message_text': row[2],
                'timestamp': row[3],
                'first_name': row[4],
                'last_name': row[5],
                'source': 'message_content'
            })

        # Add calendar tracking results
        for link in calendar_links:
            # Check if already in list
            if not any(s['ig_username'] == link['ig_username'] for s in signup_links):
                signup_links.append(link)

        conn.close()
        return signup_links

    except Exception as e:
        print(f"Error getting signup links: {e}")
        return []


def get_all_challenge_enquiries(days_back: int = 30) -> List[Dict]:
    """
    Get all people who enquired about the challenge (not just ad responses).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Find all messages containing challenge-related keywords
        cursor.execute("""
            SELECT DISTINCT
                m.ig_username,
                m.subscriber_id,
                u.first_name,
                u.last_name,
                COUNT(m2.id) as message_count,
                MAX(m.timestamp) as last_message
            FROM messages m
            LEFT JOIN users u ON m.ig_username = u.ig_username
            LEFT JOIN messages m2 ON m.ig_username = m2.ig_username
            WHERE (m.text LIKE '%challenge%' 
                   OR m.text LIKE '%vegan%'
                   OR m.text LIKE '%plant-based%'
                   OR m.text LIKE '%coaching%'
                   OR m.text LIKE '%program%'
                   OR m.text LIKE '%interested%'
                   OR m.text LIKE '%tell me more%'
                   OR m.text LIKE '%how much%'
                   OR m.text LIKE '%price%'
                   OR m.text LIKE '%cost%')
            AND m.sender = 'user'
            AND m.timestamp >= ?
            AND m.timestamp <= ?
            GROUP BY m.ig_username
            ORDER BY last_message DESC
        """, (start_date.isoformat(), end_date.isoformat()))

        results = cursor.fetchall()

        enquiries = []
        for row in results:
            enquiries.append({
                'ig_username': row[0],
                'subscriber_id': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'message_count': row[4],
                'last_message': row[5]
            })

        conn.close()
        return enquiries

    except Exception as e:
        print(f"Error getting challenge enquiries: {e}")
        return []


def print_all_challenge_enquiries(days_back: int = 30):
    """
    Print a formatted list of all challenge enquiries.
    """
    print(f"\n{'='*60}")
    print(f"ALL CHALLENGE ENQUIRIES (Last {days_back} days)")
    print(f"{'='*60}")

    enquiries = get_all_challenge_enquiries(days_back)

    if not enquiries:
        print("No challenge enquiries found in the specified time period.")
        return

    print(f"Total challenge enquiries: {len(enquiries)}")
    print()

    for i, enquiry in enumerate(enquiries, 1):
        print(f"{i}. @{enquiry['ig_username']}")
        if enquiry['first_name']:
            print(
                f"   Name: {enquiry['first_name']} {enquiry.get('last_name', '')}")
        print(f"   Messages: {enquiry['message_count']}")
        print(f"   Last Message: {enquiry['last_message']}")
        print()


def get_ad_analytics_summary(days_back: int = 30) -> Dict:
    """
    Get summary analytics for ad responses and sign-up links.
    """
    ad_responses = get_ad_responses(days_back)
    signup_links = get_signup_links_sent(days_back)

    # Count by lead source
    lead_source_counts = {}
    for response in ad_responses:
        source = response['lead_source']
        lead_source_counts[source] = lead_source_counts.get(source, 0) + 1

    # Count by ad script state
    script_state_counts = {}
    for response in ad_responses:
        state = response['ad_script_state'] or 'unknown'
        script_state_counts[state] = script_state_counts.get(state, 0) + 1

    # Count booking status
    booking_status_counts = {}
    for link in signup_links:
        if 'booking_status' in link:
            status = link['booking_status'] or 'unknown'
            booking_status_counts[status] = booking_status_counts.get(
                status, 0) + 1

    return {
        'total_ad_responses': len(ad_responses),
        'total_signup_links_sent': len(signup_links),
        'lead_source_breakdown': lead_source_counts,
        'script_state_breakdown': script_state_counts,
        'booking_status_breakdown': booking_status_counts,
        'days_analyzed': days_back
    }


def print_ad_responses_list(days_back: int = 30):
    """
    Print a formatted list of ad responses.
    """
    print(f"\n{'='*60}")
    print(f"AD RESPONSES (Last {days_back} days)")
    print(f"{'='*60}")

    ad_responses = get_ad_responses(days_back)

    if not ad_responses:
        print("No ad responses found in the specified time period.")
        return

    print(f"Total ad responses: {len(ad_responses)}")
    print()

    for i, response in enumerate(ad_responses, 1):
        print(f"{i}. @{response['ig_username']}")
        print(f"   Name: {response['first_name']} {response['last_name']}")
        print(f"   Lead Source: {response['lead_source']}")
        print(f"   Script State: {response['ad_script_state']}")
        print(f"   Last Interaction: {response['last_interaction']}")
        print(f"   Messages: {response['message_count']}")
        print()


def print_signup_links_list(days_back: int = 30):
    """
    Print a formatted list of sign-up links sent.
    """
    print(f"\n{'='*60}")
    print(f"SIGN-UP LINKS SENT (Last {days_back} days)")
    print(f"{'='*60}")

    signup_links = get_signup_links_sent(days_back)

    if not signup_links:
        print("No sign-up links found in the specified time period.")
        return

    print(f"Total sign-up links sent: {len(signup_links)}")
    print()

    for i, link in enumerate(signup_links, 1):
        print(f"{i}. @{link['ig_username']}")
        if 'first_name' in link and link['first_name']:
            print(f"   Name: {link['first_name']} {link.get('last_name', '')}")
        print(f"   Timestamp: {link['timestamp']}")
        if 'booking_status' in link:
            print(f"   Booking Status: {link['booking_status']}")
        print(f"   Source: {link['source']}")
        print()


def print_analytics_summary(days_back: int = 30):
    """
    Print a summary of ad analytics.
    """
    print(f"\n{'='*60}")
    print(f"AD ANALYTICS SUMMARY (Last {days_back} days)")
    print(f"{'='*60}")

    summary = get_ad_analytics_summary(days_back)

    print(f"Total Ad Responses: {summary['total_ad_responses']}")
    print(f"Total Sign-up Links Sent: {summary['total_signup_links_sent']}")
    print()

    print("Lead Source Breakdown:")
    for source, count in summary['lead_source_breakdown'].items():
        print(f"  {source}: {count}")
    print()

    print("Script State Breakdown:")
    for state, count in summary['script_state_breakdown'].items():
        print(f"  {state}: {count}")
    print()

    if summary['booking_status_breakdown']:
        print("Booking Status Breakdown:")
        for status, count in summary['booking_status_breakdown'].items():
            print(f"  {status}: {count}")
        print()


def main():
    """
    Main function to run the analytics.
    """
    print("Shanbot Ad Analytics Report")
    print("=" * 60)

    # Use default 30 days
    days = 30
    print(f"Analyzing last {days} days...")

    # Print all reports
    print_analytics_summary(days)
    print_ad_responses_list(days)
    print_signup_links_list(days)
    print_all_challenge_enquiries(days)

    print("\n" + "="*60)
    print("Report complete!")


if __name__ == "__main__":
    main()
