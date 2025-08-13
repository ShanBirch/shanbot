import sqlite3
import datetime


def check_progress():
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM new_leads WHERE coaching_score >= 80')
    premium = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM new_leads')
    total = c.fetchone()[0]

    print(f'🎯 PREMIUM LEADS: {premium}/100 target')
    print(f'📊 Total leads: {total}')
    print(f'📈 Progress: {premium}% toward goal')

    print('\n🌟 Premium leads:')
    c.execute('SELECT username, coaching_score, hashtag_found FROM new_leads WHERE coaching_score >= 80 ORDER BY coaching_score DESC')
    for row in c.fetchall():
        print(f'  @{row[0]} - {row[1]}/100 - #{row[2]}')

    conn.close()


if __name__ == "__main__":
    check_progress()
