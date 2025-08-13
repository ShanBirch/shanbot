with open('instagram_followers.txt', 'r') as f:
    lines = [line.strip() for line in f if line.strip()]

print(f"Total usernames: {len(lines)}")

# Search for usernames containing 'eugen'
matches = []
for i, line in enumerate(lines):
    if 'eugen' in line.lower():
        matches.append((i, line))

print(f"Found {len(matches)} usernames containing 'eugen':")
for i, username in matches:
    print(f"  {i+1}: {username}")

# Also search for similar usernames around the expected area
print("\nSample usernames around position 4000:")
start = max(0, 4000 - 5)
end = min(len(lines), 4000 + 5)
for i in range(start, end):
    print(f"  {i+1}: {lines[i]}")
