import json
import os


def check_incomplete_bios(analytics_file):
    print("\n=== Checking for Incomplete Profile Bios ===\n")

    try:
        with open(analytics_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        incomplete_profiles = []
        total_profiles = 0
        completely_empty = []
        partially_empty = []

        # Iterate through all profiles
        for username, profile_data in data.get('conversations', {}).items():
            total_profiles += 1
            metrics = profile_data.get('metrics', {})
            client_analysis = metrics.get('client_analysis', {})
            profile_bio = client_analysis.get('profile_bio', {})

            issues = []

            # Check for missing or empty bio sections
            if not profile_bio:
                issues.append("Missing profile_bio")
                completely_empty.append(username)
            else:
                empty_sections = []
                if not profile_bio.get('INTERESTS') or len(profile_bio.get('INTERESTS', [])) == 0:
                    empty_sections.append("Empty INTERESTS")

                if profile_bio.get('LIFESTYLE') in ["Unknown", "", None]:
                    empty_sections.append("Unknown LIFESTYLE")

                if not profile_bio.get('PERSONALITY TRAITS') or len(profile_bio.get('PERSONALITY TRAITS', [])) == 0:
                    empty_sections.append("Empty PERSONALITY TRAITS")

                if profile_bio.get('PERSON NAME') in ["Unknown", "", None]:
                    empty_sections.append("Unknown PERSON NAME")

                if len(empty_sections) == 4:  # All sections are empty
                    completely_empty.append(username)
                    issues.extend(empty_sections)
                elif empty_sections:  # Some sections are empty
                    partially_empty.append(username)
                    issues.extend(empty_sections)

            # If any issues found, add to incomplete profiles
            if issues:
                incomplete_profiles.append({
                    'username': username,
                    'issues': issues
                })

        # Print results
        print(f"Total profiles analyzed: {total_profiles}")
        print(f"Profiles with incomplete bios: {len(incomplete_profiles)}\n")
        print(f"Completely empty bios: {len(completely_empty)}")
        print(f"Partially empty bios: {len(partially_empty)}\n")

        if incomplete_profiles:
            print("The following profiles need attention:")
            print("-" * 50)
            print("\nCompletely empty bios:")
            for username in completely_empty:
                print(f"  - {username}")

            print("\nPartially empty bios:")
            for username in partially_empty:
                print(f"  - {username}")

            # Save usernames to files for reanalysis
            with open('completely_empty_bios.txt', 'w') as f:
                for username in completely_empty:
                    f.write(f"{username}\n")

            with open('partially_empty_bios.txt', 'w') as f:
                for username in partially_empty:
                    f.write(f"{username}\n")

            print(
                "\nSaved usernames to 'completely_empty_bios.txt' and 'partially_empty_bios.txt'")
        else:
            print("All profiles have complete bios!")

        return incomplete_profiles

    except Exception as e:
        print(f"Error reading analytics file: {str(e)}")
        return None


if __name__ == "__main__":
    # Path to analytics file
    analytics_file = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"

    if not os.path.exists(analytics_file):
        print(f"Error: Analytics file not found at {analytics_file}")
    else:
        check_incomplete_bios(analytics_file)
