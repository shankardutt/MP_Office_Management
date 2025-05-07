"""
GitHub integration for Office Room Allocation System using Streamlit Secrets
"""

import base64
import os
import requests
import streamlit as st
import json
from datetime import datetime

def get_github_secrets():
    """
    Get GitHub credentials from Streamlit Secrets or return empty values if not found
    """
    # Check if secrets are available and have the github section
    if hasattr(st, 'secrets') and 'github' in st.secrets:
        return {
            'token': st.secrets.github.get('token', ''),
            'owner': st.secrets.github.get('owner', ''),
            'repo': st.secrets.github.get('repo', ''),
            'branch': st.secrets.github.get('branch', 'main')
        }
    return {
        'token': '',
        'owner': '',
        'repo': '',
        'branch': 'main'
    }

def init_github_integration():
    """Initialize GitHub integration settings"""
    # Initialize with values from secrets if available
    github_secrets = get_github_secrets()
    
    # For UI display and temporary storage (still needed for the UI)
    if 'github_token' not in st.session_state:
        st.session_state.github_token = github_secrets['token']
    if 'github_repo' not in st.session_state:
        st.session_state.github_repo = github_secrets['repo']
    if 'github_owner' not in st.session_state:
        st.session_state.github_owner = github_secrets['owner']
    if 'github_branch' not in st.session_state:
        st.session_state.github_branch = github_secrets['branch']
    if 'use_github' not in st.session_state:
        # Auto-enable if secrets are configured
        st.session_state.use_github = all([
            github_secrets['token'], 
            github_secrets['repo'], 
            github_secrets['owner']
        ])

def save_to_github(filename, content, commit_message=None):
    """
    Save a file to GitHub repository
    
    Args:
        filename: Path to the file in the repository
        content: Content of the file (binary or string)
        commit_message: Message for the commit
        
    Returns:
        (success, message): Tuple with operation result and message
    """
    # Get GitHub credentials from secrets first
    github_secrets = get_github_secrets()
    
    # Use secrets if available, otherwise use session state (UI values)
    token = github_secrets['token'] or st.session_state.github_token
    repo = github_secrets['repo'] or st.session_state.github_repo
    owner = github_secrets['owner'] or st.session_state.github_owner
    branch = github_secrets['branch'] or st.session_state.github_branch
    
    if not token or not repo or not owner:
        return False, "GitHub integration not configured. Please set up GitHub credentials."
    
    # API URL for GitHub content
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}"
    
    # Headers for GitHub API
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get sha if the file exists
    sha = None
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            sha = response.json().get("sha")
    except Exception as e:
        print(f"Error getting file SHA: {str(e)}")
        pass
    
    # Prepare content for API (needs to be base64 encoded)
    if isinstance(content, str):
        content_bytes = content.encode("utf-8")
    else:
        content_bytes = content
        
    encoded_content = base64.b64encode(content_bytes).decode("utf-8")
    
    # Default commit message
    if not commit_message:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"Update {filename} - {timestamp}"
    
    # Prepare data for the API
    data = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch
    }
    
    # Include sha if file exists
    if sha:
        data["sha"] = sha
    
    # Make the request to update or create the file
    try:
        response = requests.put(api_url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            return True, f"Successfully saved {filename} to GitHub"
        else:
            error_detail = f"{response.status_code} - {response.text}"
            # Check for specific error cases
            if response.status_code == 403:
                if "Resource not accessible by personal access token" in response.text:
                    return False, f"Error: Your GitHub token doesn't have sufficient permissions. Please create a new token with 'repo' scope (full control of repositories)."
            
            return False, f"Error saving to GitHub: {error_detail}"
    except Exception as e:
        return False, f"Error connecting to GitHub: {str(e)}"

def load_from_github(filename):
    """
    Load a file from GitHub repository
    
    Args:
        filename: Path to the file in the repository
        
    Returns:
        content: Content of the file or None if not found/error
    """
    # Get GitHub credentials from secrets first
    github_secrets = get_github_secrets()
    
    # Use secrets if available, otherwise use session state (UI values)
    token = github_secrets['token'] or st.session_state.github_token
    repo = github_secrets['repo'] or st.session_state.github_repo
    owner = github_secrets['owner'] or st.session_state.github_owner
    branch = github_secrets['branch'] or st.session_state.github_branch
    
    if not token or not repo or not owner:
        return None
    
    # API URL for GitHub content
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}"
    
    # Headers for GitHub API
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # Get file content
        response = requests.get(
            api_url,
            headers=headers,
            params={"ref": branch}
        )
        
        if response.status_code == 200:
            # Decode content from base64
            content_base64 = response.json().get("content", "")
            content = base64.b64decode(content_base64)
            return content
        else:
            print(f"Error loading from GitHub: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception loading from GitHub: {str(e)}")
        return None

def show_github_settings():
    """Show GitHub integration settings in the app sidebar"""
    with st.sidebar.expander("🔄 GitHub Integration", expanded=False):
        # Get current secrets
        github_secrets = get_github_secrets()
        secrets_configured = all([
            github_secrets['token'],
            github_secrets['repo'],
            github_secrets['owner']
        ])
        
        if secrets_configured:
            st.success("GitHub credentials are configured in Streamlit Secrets!")
            st.info(
                "Repository: " + 
                f"{github_secrets['owner']}/{github_secrets['repo']} " + 
                f"({github_secrets['branch']} branch)"
            )
            
            # Instead of using a nested expander, just show the instructions directly
            st.subheader("How to change GitHub settings")
            st.write("""
            To modify GitHub settings:
            
            **For local development:**
            1. Create or edit `.streamlit/secrets.toml` file
            2. Update the GitHub credentials there
            
            **For Streamlit Cloud:**
            1. Go to your app dashboard
            2. Navigate to 'Advanced Settings' → 'Secrets'
            3. Update the GitHub credentials there
            """)
            
            st.code("""
# Example secrets.toml format
[github]
token = "your_github_token"
owner = "your_github_username"
repo = "your_repository_name"
branch = "main"
            """, language="toml")
        else:
            st.warning("GitHub credentials not found in Streamlit Secrets")
            st.write("Configure GitHub integration for persistent storage:")
            
            # Option to manually configure in UI (temporary, not saved between sessions)
            st.session_state.github_token = st.text_input(
                "GitHub Personal Access Token",
                value=st.session_state.get('github_token', ''),
                type="password",
                help="Create a token with 'repo' scope at https://github.com/settings/tokens",
                key="github_token_input"
            )
            
            st.info("""
            **Important:** Your token must have the **repo** scope to allow full repository access.
            When creating a token, make sure to check the box labeled 'repo' which grants full control
            of private repositories.
            """)
            
            st.session_state.github_owner = st.text_input(
                "GitHub Username/Organization",
                value=st.session_state.get('github_owner', ''),
                help="Your GitHub username or organization name",
                key="github_owner_input"
            )
            
            st.session_state.github_repo = st.text_input(
                "GitHub Repository Name",
                value=st.session_state.get('github_repo', ''),
                help="The name of your GitHub repository",
                key="github_repo_input"
            )
            
            st.session_state.github_branch = st.text_input(
                "Branch Name",
                value=st.session_state.get('github_branch', 'main'),
                help="Branch to save to (usually 'main' or 'master')",
                key="github_branch_input"
            )
            
            # Show instructions for setting up secrets - Avoiding nested expander
            st.subheader("How to set up Streamlit Secrets")
            st.write("""
            For permanent configuration, set up Streamlit Secrets:
            
            **For local development:**
            1. Create `.streamlit/secrets.toml` in your project directory
            2. Add GitHub credentials as shown in the example below
            
            **For Streamlit Cloud:**
            1. Go to your app dashboard
            2. Navigate to 'Advanced Settings' → 'Secrets'
            3. Add GitHub credentials in the same format
            """)
            
            st.code("""
# Add this to your secrets.toml file
[github]
token = "your_github_token"
owner = "your_github_username"
repo = "your_repository_name"
branch = "main"
            """, language="toml")
        
        # Test connection button - Add a unique key
        if st.button("Test GitHub Connection", key="github_test_connection_btn"):
            # Use secrets if available, otherwise use session state
            token = github_secrets['token'] or st.session_state.github_token
            repo = github_secrets['repo'] or st.session_state.github_repo
            owner = github_secrets['owner'] or st.session_state.github_owner
            
            if not token or not repo or not owner:
                st.error("Please configure GitHub credentials in Streamlit Secrets or fill in all fields above")
            else:
                try:
                    # Test API connection
                    api_url = f"https://api.github.com/repos/{owner}/{repo}"
                    headers = {
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                    response = requests.get(api_url, headers=headers)
                    
                    if response.status_code == 200:
                        # Test write permissions by trying to create a temporary file
                        test_content = json.dumps({"test": "This is a test file", "timestamp": str(datetime.now())})
                        success, message = save_to_github(
                            "github_test.json",
                            test_content,
                            "Test file to verify GitHub write access"
                        )
                        
                        if success:
                            st.success("✅ GitHub connection successful! Repository exists and token has write permissions.")
                        else:
                            st.error(f"❌ Connection successful but write test failed: {message}")
                            st.info("Please make sure your token has the 'repo' scope (full control of repositories).")
                    else:
                        st.error(f"❌ Connection failed: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"❌ Connection error: {str(e)}")