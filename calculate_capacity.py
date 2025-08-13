# Calculate how long the script can run in local mode
businesses = 46
followers_per_business = 200
hashtags = 50
posts_per_hashtag = 20
delay_per_profile = 12  # average seconds

total_profiles = (businesses * followers_per_business) + \
    (hashtags * posts_per_hashtag)
total_time_seconds = total_profiles * delay_per_profile
hours = total_time_seconds / 3600
days = hours / 24

print(f'📊 CAPACITY ANALYSIS:')
print(f'   • {businesses} local businesses × {followers_per_business} followers = {businesses * followers_per_business:,} profiles')
print(f'   • {hashtags} hashtags × {posts_per_hashtag} posts = {hashtags * posts_per_hashtag:,} profiles')
print(f'   • Total potential profiles: {total_profiles:,}')
print(
    f'   • At {delay_per_profile}s per profile: {total_time_seconds:,} seconds')
print(f'   • Runtime: {hours:.1f} hours ({days:.1f} days)')
print(f'')
print(f'🎯 EXPECTED LOCAL LEADS:')
print(f'   • If 1 in 100 profiles qualify: {total_profiles // 100} leads')
print(f'   • If 1 in 200 profiles qualify: {total_profiles // 200} leads')
print(f'   • If 1 in 500 profiles qualify: {total_profiles // 500} leads')
print(f'')
print(f'💡 REALISTIC EXPECTATIONS:')
print(f'   • Script can run for DAYS without running out of targets')
print(f'   • Local leads will be rare but high-quality')
print(f'   • Expect to find 10-50 local leads over several hours')
