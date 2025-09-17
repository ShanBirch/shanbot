# GitHub Integration Setup Guide

This guide will help you connect your Shanbot webhook system to GitHub.

## 🚀 Quick Start

### 1. Install Dependencies

The GitHub package has been added to your requirements.txt. Install it:

```bash
pip install -r requirements.txt
```

### 2. Get a GitHub Token

1. Go to [GitHub Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a descriptive name like "Shanbot Webhook"
4. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `public_repo` (Access public repositories)
   - `read:user` (Read user profile data)
   - `user:email` (Access user email addresses)

### 3. Set Environment Variables

Set these environment variables in your system:

```bash
# Required
export GITHUB_TOKEN="your_github_token_here"

# Optional but recommended
export GITHUB_USERNAME="your_github_username"
export GITHUB_REPO="username/repository-name"  # e.g., "shannon/shanbot"
```

**For Windows (PowerShell):**
```powershell
$env:GITHUB_TOKEN="your_github_token_here"
$env:GITHUB_USERNAME="your_github_username"
$env:GITHUB_REPO="username/repository-name"
```

**For Windows (Command Prompt):**
```cmd
set GITHUB_TOKEN=your_github_token_here
set GITHUB_USERNAME=your_github_username
set GITHUB_REPO=username/repository-name
```

### 4. Test Your Setup

Run the test script to verify everything is working:

```bash
python test_github_connection.py
```

## 📱 Available Commands

Once setup is complete, users can interact with GitHub through your webhook using these natural language commands:

### Repository Management
- `"github status"` - Check connection and account info
- `"list repos"` or `"show my repositories"` - List your repositories
- `"repo info"` or `"about this repo"` - Get current repository information
- `"create repo called my-project"` - Create a new repository
- `"create private repo called my-secret-project"` - Create a private repository

### Issues
- `"create issue: Bug in login system"` - Create a new issue
- `"new issue: Add dark mode feature"` - Create a feature request
- `"report bug: App crashes on startup"` - Report a bug

### Code & History
- `"commit history"` or `"recent commits"` - View recent commits
- `"search code \"function name\""` - Search for code in the repository
- `"find code \"api endpoint\""` - Search for specific code patterns

## 🔧 Configuration Details

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GITHUB_TOKEN` | ✅ Yes | GitHub personal access token | `ghp_xxxxxxxxxxxx` |
| `GITHUB_USERNAME` | ❌ Optional | Your GitHub username | `shannon` |
| `GITHUB_REPO` | ❌ Optional | Default repository (owner/repo) | `shannon/shanbot` |

### Token Permissions

Your GitHub token needs these permissions:
- **repo**: Full access to repositories (required)
- **read:user**: Read user information (required)
- **user:email**: Access email addresses (optional)

## 🛠️ Advanced Usage

### Repository Operations

The integration supports:
- Creating repositories (public/private)
- Reading repository information
- Listing directory contents
- Creating, updating, and deleting files
- Searching code within repositories

### Issue Management

- Create issues with labels
- List open/closed issues
- Search issues by various criteria

### Commit History

- View recent commits
- Get detailed commit information
- Access commit URLs for web viewing

## 🐛 Troubleshooting

### Common Issues

1. **"GitHub token is required" error**
   - Make sure `GITHUB_TOKEN` environment variable is set
   - Verify the token is valid and not expired

2. **"Failed to access repository" error**
   - Check that `GITHUB_REPO` is in format "username/repository"
   - Ensure you have access to the repository
   - Verify the repository exists

3. **"PyGithub is not installed" error**
   - Run `pip install -r requirements.txt`
   - Or manually: `pip install PyGithub==2.1.1`

4. **Rate limiting issues**
   - GitHub API has rate limits (5000 requests/hour for authenticated users)
   - The system handles basic rate limiting automatically

### Test Commands

```bash
# Test basic connection
python -c "from utilities.github_utils import test_github_connection; print(test_github_connection())"

# Test with specific repository
python -c "
import os; 
os.environ['GITHUB_REPO'] = 'your-username/your-repo';
from utilities.github_utils import create_github_manager;
manager = create_github_manager();
print(manager.get_repository_info())
"
```

## 🔒 Security Considerations

1. **Token Security**
   - Never commit your GitHub token to version control
   - Use environment variables or secure secret management
   - Regularly rotate your tokens

2. **Permissions**
   - Only grant necessary permissions to your token
   - Use repository-specific tokens when possible

3. **Access Control**
   - The webhook system will have the same permissions as your token
   - Be careful with public repositories if using organization tokens

## 📚 Integration Details

### File Structure

- `utilities/github_utils.py` - Core GitHub API wrapper
- `action_handlers/github_action_handler.py` - Webhook action handler
- `action_handlers/core_action_handler.py` - Updated to include GitHub actions
- `utilities/config.py` - Updated with GitHub configuration
- `requirements.txt` - Updated with PyGithub dependency

### Message Processing

The system uses natural language processing to detect GitHub-related requests:
1. Message comes in through webhook
2. Core action handler detects GitHub patterns
3. GitHub action handler processes the request
4. Response is sent back through the review queue system

### Response Format

GitHub responses include:
- Success/error status
- Relevant information (repo details, issue numbers, etc.)
- Links to GitHub web interface
- Appropriate emojis and formatting for readability

## 🚀 Next Steps

1. Run the test script: `python test_github_connection.py`
2. Test basic commands through your webhook
3. Set up repository-specific automation
4. Integrate with your existing workflows

For support or questions, check the logs in your webhook system or refer to the [PyGithub documentation](https://pygithub.readthedocs.io/).
