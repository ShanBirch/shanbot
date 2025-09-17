#!/usr/bin/env python3
"""
GitHub Connection Test
=====================
Test script to verify GitHub integration setup.
"""

import os
import sys
import json
from datetime import datetime

# Add utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utilities'))

try:
    from utilities.github_utils import test_github_connection, create_github_manager
    from utilities.config import Config
except ImportError as e:
    print(f"❌ Failed to import utilities: {e}")
    print("Make sure you've installed the required packages: pip install -r requirements.txt")
    sys.exit(1)


def test_configuration():
    """Test GitHub configuration."""
    print("🔧 Testing GitHub Configuration...")
    print(
        f"   GITHUB_TOKEN: {'✅ Set' if Config.GITHUB_TOKEN else '❌ Not set'}")
    print(
        f"   GITHUB_USERNAME: {'✅ Set' if Config.GITHUB_USERNAME else '❌ Not set'}")
    print(f"   GITHUB_REPO: {'✅ Set' if Config.GITHUB_REPO else '❌ Not set'}")
    print()

    if not Config.GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN is required!")
        print("   Get a token from: https://github.com/settings/tokens")
        print("   Set it with: export GITHUB_TOKEN='your_token_here'")
        return False

    return True


def test_basic_connection():
    """Test basic GitHub connection."""
    print("🔗 Testing GitHub Connection...")

    result = test_github_connection()

    if result["status"] == "success":
        print("✅ GitHub connection successful!")
        user_info = result["user_info"]
        print(f"   👤 User: {user_info['name']} (@{user_info['login']})")
        print(f"   📚 Public Repos: {user_info['public_repos']}")
        print(f"   👥 Followers: {user_info['followers']}")
        print(f"   🔗 Following: {user_info['following']}")
        print()
        return True
    else:
        print(f"❌ GitHub connection failed: {result['message']}")
        print()
        return False


def test_repository_access():
    """Test repository access if configured."""
    if not Config.GITHUB_REPO:
        print("ℹ️  No repository configured (GITHUB_REPO not set)")
        print("   This is optional - you can still use most GitHub features")
        print()
        return True

    print(f"🏗️ Testing Repository Access: {Config.GITHUB_REPO}")

    try:
        manager = create_github_manager()
        repo_info = manager.get_repository_info()

        print("✅ Repository access successful!")
        print(
            f"   📝 Description: {repo_info['description'] or 'No description'}")
        print(f"   🏷️ Language: {repo_info['language'] or 'Not specified'}")
        print(f"   ⭐ Stars: {repo_info['stargazers_count']}")
        print(f"   🍴 Forks: {repo_info['forks_count']}")
        print(f"   🐛 Open Issues: {repo_info['open_issues_count']}")
        print(
            f"   🔒 Visibility: {'Private' if repo_info['private'] else 'Public'}")
        print()
        return True

    except Exception as e:
        print(f"❌ Repository access failed: {e}")
        print("   Make sure the repository exists and you have access to it")
        print()
        return False


def test_github_operations():
    """Test basic GitHub operations."""
    if not Config.GITHUB_TOKEN:
        return False

    print("🛠️ Testing GitHub Operations...")

    try:
        manager = create_github_manager()

        # Test listing repositories
        print("   📚 Testing repository listing...")
        repos = manager.list_repositories(type_filter="owner")
        print(f"   ✅ Found {len(repos)} repositories")

        if repos:
            print(f"   📁 Latest repo: {repos[0]['name']}")

        # If repository is configured, test more operations
        if Config.GITHUB_REPO:
            print("   🐛 Testing issue listing...")
            issues = manager.get_issues(state="open")
            print(f"   ✅ Found {len(issues)} open issues")

            print("   📝 Testing commit history...")
            commits = manager.get_commit_history(limit=3)
            print(f"   ✅ Found {len(commits)} recent commits")

            if commits:
                print(
                    f"   🔄 Latest commit: {commits[0]['sha'][:8]} - {commits[0]['message'][:50]}...")

        print("   ✅ All operations successful!")
        print()
        return True

    except Exception as e:
        print(f"   ❌ Operations test failed: {e}")
        print()
        return False


def main():
    """Main test function."""
    print("🚀 GitHub Integration Test")
    print("=" * 50)
    print()

    # Track test results
    tests_passed = 0
    total_tests = 4

    # Test 1: Configuration
    if test_configuration():
        tests_passed += 1

    # Test 2: Basic connection
    if test_basic_connection():
        tests_passed += 1

    # Test 3: Repository access
    if test_repository_access():
        tests_passed += 1

    # Test 4: GitHub operations
    if test_github_operations():
        tests_passed += 1

    # Summary
    print("📊 Test Summary")
    print("=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")

    if tests_passed == total_tests:
        print("🎉 All tests passed! GitHub integration is ready to use.")
        print()
        print("💬 You can now use GitHub commands in your webhook:")
        print("   • 'github status' - Check connection")
        print("   • 'list repos' - List your repositories")
        print("   • 'repo info' - Get current repository info")
        print("   • 'create repo called my-project' - Create new repository")
        print("   • 'create issue: Bug report' - Create new issue")
        print("   • 'commit history' - View recent commits")
        print("   • 'search code \"function name\"' - Search repository code")
    else:
        print(
            f"⚠️ {total_tests - tests_passed} test(s) failed. Check the output above for details.")

        if not Config.GITHUB_TOKEN:
            print()
            print("🔧 Quick Setup Guide:")
            print("1. Get a GitHub token: https://github.com/settings/tokens")
            print("2. Set environment variable: export GITHUB_TOKEN='your_token_here'")
            print("3. Optional: export GITHUB_USERNAME='your_username'")
            print("4. Optional: export GITHUB_REPO='username/repository'")
            print("5. Run this test again")

    print()
    return tests_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
