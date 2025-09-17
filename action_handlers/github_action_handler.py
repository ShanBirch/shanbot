"""
GitHub Action Handler
====================
Handles GitHub-related actions triggered by webhook messages.
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from utilities.github_utils import GitHubManager, test_github_connection
from utilities.config import Config

logger = logging.getLogger("shanbot_github_actions")


class GitHubActionHandler:
    """Handles GitHub operations triggered by user messages."""

    def __init__(self):
        """Initialize the GitHub action handler."""
        self.github_manager = None
        self._initialize_github()

    def _initialize_github(self):
        """Initialize GitHub connection if credentials are available."""
        try:
            if Config.GITHUB_TOKEN:
                self.github_manager = GitHubManager()
                logger.info("GitHub integration initialized successfully")
            else:
                logger.warning(
                    "GitHub token not configured. GitHub features will be disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub integration: {e}")
            self.github_manager = None

    @staticmethod
    def detect_github_action(message_text: str) -> Optional[str]:
        """Detect if message contains GitHub-related requests.

        Args:
            message_text: User message text

        Returns:
            Action type if detected, None otherwise
        """
        message_lower = message_text.lower()

        # GitHub action patterns
        github_patterns = {
            "create_repo": [
                r"create.*repo",
                r"new.*repository",
                r"make.*repo",
                r"setup.*repository"
            ],
            "create_issue": [
                r"create.*issue",
                r"new.*issue",
                r"report.*bug",
                r"add.*issue"
            ],
            "list_repos": [
                r"list.*repo",
                r"show.*repo",
                r"my.*repo",
                r"repositories"
            ],
            "repo_info": [
                r"repo.*info",
                r"repository.*info",
                r"about.*repo"
            ],
            "commit_history": [
                r"commit.*history",
                r"recent.*commits",
                r"git.*log"
            ],
            "search_code": [
                r"search.*code",
                r"find.*code",
                r"look.*for.*code"
            ],
            "github_status": [
                r"github.*status",
                r"git.*status",
                r"github.*connection"
            ]
        }

        for action, patterns in github_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return action

        return None

    async def handle_github_action(self, action: str, message_text: str,
                                   ig_username: str, subscriber_id: str) -> Tuple[bool, str]:
        """Handle detected GitHub action.

        Args:
            action: Detected action type
            message_text: Original message text
            ig_username: Instagram username
            subscriber_id: ManyChat subscriber ID

        Returns:
            Tuple of (success, response_message)
        """
        if not self.github_manager:
            return False, "GitHub integration is not configured. Please set up your GitHub token first."

        try:
            if action == "github_status":
                return await self._handle_github_status()
            elif action == "list_repos":
                return await self._handle_list_repos()
            elif action == "repo_info":
                return await self._handle_repo_info()
            elif action == "create_repo":
                return await self._handle_create_repo(message_text)
            elif action == "create_issue":
                return await self._handle_create_issue(message_text)
            elif action == "commit_history":
                return await self._handle_commit_history()
            elif action == "search_code":
                return await self._handle_search_code(message_text)
            else:
                return False, f"Unknown GitHub action: {action}"

        except Exception as e:
            logger.error(f"Error handling GitHub action {action}: {e}")
            return False, f"Failed to execute GitHub action: {str(e)}"

    async def _handle_github_status(self) -> Tuple[bool, str]:
        """Handle GitHub status check."""
        try:
            result = test_github_connection()
            if result["status"] == "success":
                user_info = result["user_info"]
                response = f"✅ GitHub Connected!\n\n"
                response += f"👤 User: {user_info['name']} (@{user_info['login']})\n"
                response += f"📚 Public Repos: {user_info['public_repos']}\n"
                response += f"👥 Followers: {user_info['followers']}\n"
                response += f"🔗 Following: {user_info['following']}\n"

                if Config.GITHUB_REPO:
                    repo_info = self.github_manager.get_repository_info()
                    response += f"\n🏗️ Current Repo: {repo_info['full_name']}\n"
                    response += f"⭐ Stars: {repo_info['stargazers_count']}\n"
                    response += f"🍴 Forks: {repo_info['forks_count']}\n"
                    response += f"🐛 Open Issues: {repo_info['open_issues_count']}\n"

                return True, response
            else:
                return False, f"❌ GitHub Connection Failed: {result['message']}"

        except Exception as e:
            return False, f"❌ Failed to check GitHub status: {str(e)}"

    async def _handle_list_repos(self) -> Tuple[bool, str]:
        """Handle list repositories request."""
        try:
            repos = self.github_manager.list_repositories()[
                :10]  # Limit to top 10

            if not repos:
                return True, "📚 No repositories found."

            response = f"📚 Your Repositories (showing {len(repos)}):\n\n"

            for i, repo in enumerate(repos, 1):
                response += f"{i}. **{repo['name']}**\n"
                if repo['description']:
                    response += f"   📝 {repo['description']}\n"
                response += f"   🏷️ {repo['language'] or 'No language'}"
                response += f" | ⭐ {repo['stargazers_count']}"
                response += f" | 🍴 {repo['forks_count']}\n"
                response += f"   🔒 {'Private' if repo['private'] else 'Public'}\n"
                response += f"   🔗 {repo['html_url']}\n\n"

            return True, response

        except Exception as e:
            return False, f"❌ Failed to list repositories: {str(e)}"

    async def _handle_repo_info(self) -> Tuple[bool, str]:
        """Handle repository information request."""
        try:
            if not Config.GITHUB_REPO:
                return False, "❌ No repository configured. Set GITHUB_REPO environment variable."

            repo_info = self.github_manager.get_repository_info()

            response = f"🏗️ Repository Information\n\n"
            response += f"**{repo_info['full_name']}**\n"
            if repo_info['description']:
                response += f"📝 {repo_info['description']}\n\n"

            response += f"🏷️ Language: {repo_info['language'] or 'Not specified'}\n"
            response += f"⭐ Stars: {repo_info['stargazers_count']}\n"
            response += f"🍴 Forks: {repo_info['forks_count']}\n"
            response += f"🐛 Open Issues: {repo_info['open_issues_count']}\n"
            response += f"📦 Size: {repo_info['size']} KB\n"
            response += f"🔒 Visibility: {'Private' if repo_info['private'] else 'Public'}\n"
            response += f"🌿 Default Branch: {repo_info['default_branch']}\n"
            response += f"📅 Created: {repo_info['created_at'][:10]}\n"
            response += f"🔄 Updated: {repo_info['updated_at'][:10]}\n"
            response += f"🔗 URL: {repo_info['html_url']}\n"

            return True, response

        except Exception as e:
            return False, f"❌ Failed to get repository info: {str(e)}"

    async def _handle_create_repo(self, message_text: str) -> Tuple[bool, str]:
        """Handle create repository request."""
        try:
            # Extract repository name from message
            # Look for patterns like "create repo called X" or "new repository X"
            name_patterns = [
                r"create.*repo.*called\s+(\w+)",
                r"new.*repository\s+(\w+)",
                r"make.*repo\s+(\w+)",
                r"create\s+(\w+)\s+repo"
            ]

            repo_name = None
            for pattern in name_patterns:
                match = re.search(pattern, message_text.lower())
                if match:
                    repo_name = match.group(1)
                    break

            if not repo_name:
                return False, "❌ Please specify a repository name. Example: 'create repo called my-project'"

            # Check if "private" is mentioned
            is_private = "private" in message_text.lower()

            # Extract description if mentioned
            desc_patterns = [
                r"description\s+['\"]([^'\"]+)['\"]",
                r"for\s+([^.!?]+)",
                r"about\s+([^.!?]+)"
            ]

            description = ""
            for pattern in desc_patterns:
                match = re.search(pattern, message_text, re.IGNORECASE)
                if match:
                    description = match.group(1).strip()
                    break

            # Create the repository
            result = self.github_manager.create_repository(
                name=repo_name,
                description=description,
                private=is_private
            )

            response = f"✅ Repository Created Successfully!\n\n"
            response += f"🏗️ **{result['full_name']}**\n"
            if result['description']:
                response += f"📝 {result['description']}\n"
            response += f"🔒 Visibility: {'Private' if result['private'] else 'Public'}\n"
            response += f"🔗 URL: {result['html_url']}\n"
            response += f"📥 Clone: {result['clone_url']}\n"

            return True, response

        except Exception as e:
            return False, f"❌ Failed to create repository: {str(e)}"

    async def _handle_create_issue(self, message_text: str) -> Tuple[bool, str]:
        """Handle create issue request."""
        try:
            if not Config.GITHUB_REPO:
                return False, "❌ No repository configured. Set GITHUB_REPO environment variable."

            # Extract issue title and body from message
            # Look for patterns like "create issue: title" or "report bug: description"
            title_patterns = [
                r"create.*issue[:\s]+([^.!?]+)",
                r"new.*issue[:\s]+([^.!?]+)",
                r"report.*bug[:\s]+([^.!?]+)",
                r"issue[:\s]+([^.!?]+)"
            ]

            title = None
            for pattern in title_patterns:
                match = re.search(pattern, message_text, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    break

            if not title:
                return False, "❌ Please specify an issue title. Example: 'create issue: Fix login bug'"

            # Use the remaining message as body if available
            body = f"Issue created via Shanbot\n\nFrom: {datetime.now().isoformat()}\n\nDescription: {message_text}"

            # Check for labels
            labels = []
            if "bug" in message_text.lower():
                labels.append("bug")
            if "enhancement" in message_text.lower() or "feature" in message_text.lower():
                labels.append("enhancement")
            if "question" in message_text.lower():
                labels.append("question")

            # Create the issue
            result = self.github_manager.create_issue(
                title=title,
                body=body,
                labels=labels
            )

            response = f"✅ Issue Created Successfully!\n\n"
            response += f"🐛 **Issue #{result['number']}**\n"
            response += f"📝 {result['title']}\n"
            response += f"🏷️ State: {result['state']}\n"
            if result['labels']:
                response += f"🏷️ Labels: {', '.join(result['labels'])}\n"
            response += f"📅 Created: {result['created_at'][:10]}\n"
            response += f"🔗 URL: {result['html_url']}\n"

            return True, response

        except Exception as e:
            return False, f"❌ Failed to create issue: {str(e)}"

    async def _handle_commit_history(self) -> Tuple[bool, str]:
        """Handle commit history request."""
        try:
            if not Config.GITHUB_REPO:
                return False, "❌ No repository configured. Set GITHUB_REPO environment variable."

            commits = self.github_manager.get_commit_history(limit=5)

            if not commits:
                return True, "📝 No commits found."

            response = f"📝 Recent Commits (last {len(commits)}):\n\n"

            for i, commit in enumerate(commits, 1):
                response += f"{i}. **{commit['sha'][:8]}**\n"
                commit_message = commit['message'].split('\n')[0][:80]
                response += f"   💬 {commit_message}...\n"
                response += f"   👤 {commit['author']['name']}\n"
                response += f"   📅 {commit['author']['date'][:10]}\n"
                response += f"   🔗 {commit['html_url']}\n\n"

            return True, response

        except Exception as e:
            return False, f"❌ Failed to get commit history: {str(e)}"

    async def _handle_search_code(self, message_text: str) -> Tuple[bool, str]:
        """Handle code search request."""
        try:
            if not Config.GITHUB_REPO:
                return False, "❌ No repository configured. Set GITHUB_REPO environment variable."

            # Extract search query from message
            search_patterns = [
                r"search.*for\s+['\"]([^'\"]+)['\"]",
                r"find.*code\s+['\"]([^'\"]+)['\"]",
                r"look.*for\s+['\"]([^'\"]+)['\"]",
                r"search\s+['\"]([^'\"]+)['\"]"
            ]

            query = None
            for pattern in search_patterns:
                match = re.search(pattern, message_text, re.IGNORECASE)
                if match:
                    query = match.group(1).strip()
                    break

            if not query:
                # Fallback: use words after "search" or "find"
                words = message_text.lower().split()
                if "search" in words:
                    idx = words.index("search")
                    if idx + 1 < len(words):
                        query = " ".join(words[idx + 1:])
                elif "find" in words:
                    idx = words.index("find")
                    if idx + 1 < len(words):
                        query = " ".join(words[idx + 1:])

            if not query:
                return False, "❌ Please specify what to search for. Example: 'search for \"function name\"'"

            # Perform the search
            results = self.github_manager.search_code(
                query)[:5]  # Limit to top 5

            if not results:
                return True, f"🔍 No code found matching '{query}'"

            response = f"🔍 Code Search Results for '{query}' (showing {len(results)}):\n\n"

            for i, result in enumerate(results, 1):
                response += f"{i}. **{result['name']}**\n"
                response += f"   📁 {result['path']}\n"
                response += f"   📊 Score: {result['score']:.2f}\n"
                response += f"   🔗 {result['html_url']}\n\n"

            return True, response

        except Exception as e:
            return False, f"❌ Failed to search code: {str(e)}"


# Factory function for integration with existing webhook system
def create_github_handler() -> GitHubActionHandler:
    """Create a GitHub action handler instance."""
    return GitHubActionHandler()
