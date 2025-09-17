"""
GitHub Utilities
================
GitHub API integration for the Shanbot webhook system.
"""

import os
import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json

try:
    from github import Github, GithubException
    from github.Repository import Repository
    from github.Issue import Issue
    from github.PullRequest import PullRequest
    from github.ContentFile import ContentFile
except ImportError:
    Github = None
    GithubException = Exception
    Repository = None
    Issue = None
    PullRequest = None
    ContentFile = None

from utilities.config import Config

logger = logging.getLogger("shanbot_github")


class GitHubManager:
    """GitHub API manager for repository operations."""

    def __init__(self, token: Optional[str] = None, username: Optional[str] = None, repo_name: Optional[str] = None):
        """Initialize GitHub manager.

        Args:
            token: GitHub personal access token
            username: GitHub username
            repo_name: Repository name (format: "owner/repo")
        """
        if Github is None:
            raise ImportError(
                "PyGithub is not installed. Run: pip install PyGithub")

        self.token = token or Config.GITHUB_TOKEN
        self.username = username or Config.GITHUB_USERNAME
        self.repo_name = repo_name or Config.GITHUB_REPO

        if not self.token:
            raise ValueError(
                "GitHub token is required. Set GITHUB_TOKEN environment variable.")

        self.github = Github(self.token)
        self.user = self.github.get_user()
        self.repo = None

        if self.repo_name:
            try:
                self.repo = self.github.get_repo(self.repo_name)
                logger.info(
                    f"Connected to GitHub repository: {self.repo_name}")
            except GithubException as e:
                logger.error(
                    f"Failed to access repository {self.repo_name}: {e}")
                raise

    def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        try:
            return {
                "login": self.user.login,
                "name": self.user.name,
                "email": self.user.email,
                "public_repos": self.user.public_repos,
                "followers": self.user.followers,
                "following": self.user.following,
                "created_at": self.user.created_at.isoformat() if self.user.created_at else None
            }
        except GithubException as e:
            logger.error(f"Failed to get user info: {e}")
            raise

    def list_repositories(self, type_filter: str = "all") -> List[Dict[str, Any]]:
        """List user repositories.

        Args:
            type_filter: "all", "owner", "public", "private", "member"
        """
        try:
            repos = self.user.get_repos(type=type_filter)
            return [
                {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "private": repo.private,
                    "fork": repo.fork,
                    "language": repo.language,
                    "size": repo.size,
                    "stargazers_count": repo.stargazers_count,
                    "forks_count": repo.forks_count,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                    "html_url": repo.html_url
                }
                for repo in repos
            ]
        except GithubException as e:
            logger.error(f"Failed to list repositories: {e}")
            raise

    def create_repository(self, name: str, description: str = "", private: bool = False) -> Dict[str, Any]:
        """Create a new repository.

        Args:
            name: Repository name
            description: Repository description
            private: Whether repository should be private
        """
        try:
            repo = self.user.create_repo(
                name=name,
                description=description,
                private=private
            )
            logger.info(f"Created repository: {repo.full_name}")
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "ssh_url": repo.ssh_url
            }
        except GithubException as e:
            logger.error(f"Failed to create repository {name}: {e}")
            raise

    def get_repository_info(self) -> Dict[str, Any]:
        """Get current repository information."""
        if not self.repo:
            raise ValueError("No repository configured")

        try:
            return {
                "name": self.repo.name,
                "full_name": self.repo.full_name,
                "description": self.repo.description,
                "private": self.repo.private,
                "fork": self.repo.fork,
                "language": self.repo.language,
                "size": self.repo.size,
                "stargazers_count": self.repo.stargazers_count,
                "forks_count": self.repo.forks_count,
                "open_issues_count": self.repo.open_issues_count,
                "default_branch": self.repo.default_branch,
                "created_at": self.repo.created_at.isoformat() if self.repo.created_at else None,
                "updated_at": self.repo.updated_at.isoformat() if self.repo.updated_at else None,
                "html_url": self.repo.html_url,
                "clone_url": self.repo.clone_url,
                "ssh_url": self.repo.ssh_url
            }
        except GithubException as e:
            logger.error(f"Failed to get repository info: {e}")
            raise

    def create_issue(self, title: str, body: str = "", labels: List[str] = None, assignees: List[str] = None) -> Dict[str, Any]:
        """Create a new issue.

        Args:
            title: Issue title
            body: Issue body/description
            labels: List of label names
            assignees: List of usernames to assign
        """
        if not self.repo:
            raise ValueError("No repository configured")

        try:
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=labels or [],
                assignees=assignees or []
            )
            logger.info(f"Created issue #{issue.number}: {title}")
            return {
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "labels": [label.name for label in issue.labels],
                "assignees": [assignee.login for assignee in issue.assignees],
                "created_at": issue.created_at.isoformat() if issue.created_at else None,
                "html_url": issue.html_url
            }
        except GithubException as e:
            logger.error(f"Failed to create issue: {e}")
            raise

    def get_issues(self, state: str = "open", labels: List[str] = None) -> List[Dict[str, Any]]:
        """Get repository issues.

        Args:
            state: "open", "closed", or "all"
            labels: Filter by label names
        """
        if not self.repo:
            raise ValueError("No repository configured")

        try:
            issues = self.repo.get_issues(state=state, labels=labels or [])
            return [
                {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "labels": [label.name for label in issue.labels],
                    "assignees": [assignee.login for assignee in issue.assignees],
                    "user": issue.user.login if issue.user else None,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                    "html_url": issue.html_url
                }
                for issue in issues
            ]
        except GithubException as e:
            logger.error(f"Failed to get issues: {e}")
            raise

    def create_file(self, path: str, content: str, message: str, branch: str = "main") -> Dict[str, Any]:
        """Create a new file in the repository.

        Args:
            path: File path in repository
            content: File content
            message: Commit message
            branch: Target branch
        """
        if not self.repo:
            raise ValueError("No repository configured")

        try:
            result = self.repo.create_file(
                path, message, content, branch=branch)
            logger.info(f"Created file: {path}")
            return {
                "path": path,
                "sha": result["commit"].sha,
                "message": message,
                "branch": branch,
                "html_url": result["content"].html_url
            }
        except GithubException as e:
            logger.error(f"Failed to create file {path}: {e}")
            raise

    def get_file_content(self, path: str, ref: str = None) -> Dict[str, Any]:
        """Get file content from repository.

        Args:
            path: File path in repository
            ref: Git reference (branch, tag, or commit SHA)
        """
        if not self.repo:
            raise ValueError("No repository configured")

        try:
            file_content = self.repo.get_contents(path, ref=ref)
            if isinstance(file_content, list):
                raise ValueError(f"Path {path} is a directory, not a file")

            return {
                "path": file_content.path,
                "name": file_content.name,
                "content": file_content.decoded_content.decode('utf-8'),
                "size": file_content.size,
                "sha": file_content.sha,
                "download_url": file_content.download_url,
                "html_url": file_content.html_url
            }
        except GithubException as e:
            logger.error(f"Failed to get file content {path}: {e}")
            raise

    def update_file(self, path: str, content: str, message: str, branch: str = "main") -> Dict[str, Any]:
        """Update an existing file in the repository.

        Args:
            path: File path in repository
            content: New file content
            message: Commit message
            branch: Target branch
        """
        if not self.repo:
            raise ValueError("No repository configured")

        try:
            # Get current file to get its SHA
            current_file = self.repo.get_contents(path, ref=branch)
            if isinstance(current_file, list):
                raise ValueError(f"Path {path} is a directory, not a file")

            result = self.repo.update_file(
                path, message, content, current_file.sha, branch=branch
            )
            logger.info(f"Updated file: {path}")
            return {
                "path": path,
                "sha": result["commit"].sha,
                "message": message,
                "branch": branch,
                "html_url": result["content"].html_url
            }
        except GithubException as e:
            logger.error(f"Failed to update file {path}: {e}")
            raise

    def delete_file(self, path: str, message: str, branch: str = "main") -> Dict[str, Any]:
        """Delete a file from the repository.

        Args:
            path: File path in repository
            message: Commit message
            branch: Target branch
        """
        if not self.repo:
            raise ValueError("No repository configured")

        try:
            # Get current file to get its SHA
            current_file = self.repo.get_contents(path, ref=branch)
            if isinstance(current_file, list):
                raise ValueError(f"Path {path} is a directory, not a file")

            result = self.repo.delete_file(
                path, message, current_file.sha, branch=branch)
            logger.info(f"Deleted file: {path}")
            return {
                "path": path,
                "sha": result["commit"].sha,
                "message": message,
                "branch": branch
            }
        except GithubException as e:
            logger.error(f"Failed to delete file {path}: {e}")
            raise

    def list_directory_contents(self, path: str = "", ref: str = None) -> List[Dict[str, Any]]:
        """List contents of a directory in the repository.

        Args:
            path: Directory path (empty string for root)
            ref: Git reference (branch, tag, or commit SHA)
        """
        if not self.repo:
            raise ValueError("No repository configured")

        try:
            contents = self.repo.get_contents(path, ref=ref)
            if not isinstance(contents, list):
                # Single file, not a directory
                return [{
                    "name": contents.name,
                    "path": contents.path,
                    "type": "file",
                    "size": contents.size,
                    "sha": contents.sha,
                    "html_url": contents.html_url
                }]

            return [
                {
                    "name": item.name,
                    "path": item.path,
                    "type": item.type,
                    "size": item.size if item.type == "file" else None,
                    "sha": item.sha,
                    "html_url": item.html_url
                }
                for item in contents
            ]
        except GithubException as e:
            logger.error(f"Failed to list directory contents {path}: {e}")
            raise

    def search_code(self, query: str, language: str = None, filename: str = None) -> List[Dict[str, Any]]:
        """Search for code in the repository.

        Args:
            query: Search query
            language: Programming language filter
            filename: Filename filter
        """
        if not self.repo:
            raise ValueError("No repository configured")

        try:
            search_query = f"{query} repo:{self.repo_name}"
            if language:
                search_query += f" language:{language}"
            if filename:
                search_query += f" filename:{filename}"

            results = self.github.search_code(search_query)
            return [
                {
                    "name": item.name,
                    "path": item.path,
                    "repository": item.repository.full_name,
                    "score": item.score,
                    "html_url": item.html_url
                }
                for item in results
            ]
        except GithubException as e:
            logger.error(f"Failed to search code: {e}")
            raise

    def get_commit_history(self, branch: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get commit history.

        Args:
            branch: Branch name (defaults to default branch)
            limit: Maximum number of commits to return
        """
        if not self.repo:
            raise ValueError("No repository configured")

        try:
            commits = self.repo.get_commits(sha=branch)[:limit]
            return [
                {
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": {
                        "name": commit.commit.author.name,
                        "email": commit.commit.author.email,
                        "date": commit.commit.author.date.isoformat() if commit.commit.author.date else None
                    },
                    "committer": {
                        "name": commit.commit.committer.name,
                        "email": commit.commit.committer.email,
                        "date": commit.commit.committer.date.isoformat() if commit.commit.committer.date else None
                    },
                    "html_url": commit.html_url
                }
                for commit in commits
            ]
        except GithubException as e:
            logger.error(f"Failed to get commit history: {e}")
            raise


def create_github_manager(token: str = None, username: str = None, repo: str = None) -> GitHubManager:
    """Factory function to create a GitHub manager instance."""
    return GitHubManager(token=token, username=username, repo_name=repo)


def test_github_connection() -> Dict[str, Any]:
    """Test GitHub connection and return status."""
    try:
        manager = create_github_manager()
        user_info = manager.get_user_info()
        return {
            "status": "success",
            "message": f"Connected to GitHub as {user_info['login']}",
            "user_info": user_info
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to connect to GitHub: {str(e)}"
        }


if __name__ == "__main__":
    # Test the connection
    result = test_github_connection()
    print(json.dumps(result, indent=2))
