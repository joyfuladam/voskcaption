#!/usr/bin/env python3
"""
GitHub Update Checker for Caption5
Checks for updates and performs automatic updates from GitHub
"""

import os
import sys
import subprocess
import json
import requests
from datetime import datetime
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GitHubUpdater:
    def __init__(self, repo_owner="joyfuladam", repo_name="caption", branch="main"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.github_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{branch}"
        self.local_git_path = os.path.dirname(os.path.abspath(__file__))
        
        # Get GitHub token from environment variable
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.auth_headers = {}
        if self.github_token:
            self.auth_headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            print("Using GitHub token for authentication")
        else:
            print("No GitHub token found, using unauthenticated requests")
        
    def get_latest_commit_info(self):
        """Get the latest commit information from GitHub"""
        try:
            print(f"Fetching from GitHub API: {self.github_api_url}")
            response = requests.get(self.github_api_url, headers=self.auth_headers, timeout=10)
            print(f"GitHub API response status: {response.status_code}")
            
            if response.status_code == 200:
                commit_data = response.json()
                return {
                    'sha': commit_data['sha'][:7],
                    'message': commit_data['commit']['message'],
                    'date': commit_data['commit']['author']['date'],
                    'author': commit_data['commit']['author']['name']
                }
            elif response.status_code == 403:
                print("GitHub API rate limit exceeded or access denied")
                return None
            elif response.status_code == 404:
                print("Repository not found or access denied")
                return None
            else:
                print(f"GitHub API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error fetching GitHub info: {e}")
            return None
    
    def get_local_commit_info(self):
        """Get the current local commit information"""
        try:
            # Change to the project directory
            os.chdir(self.local_git_path)
            
            # Get current commit hash
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                local_sha = result.stdout.strip()[:7]
                
                # Get current commit message
                result = subprocess.run(
                    ['git', 'log', '-1', '--pretty=format:%s'],
                    capture_output=True, text=True, timeout=10
                )
                local_message = result.stdout.strip() if result.returncode == 0 else "Unknown"
                
                return {
                    'sha': local_sha,
                    'message': local_message
                }
            else:
                return None
        except Exception as e:
            print(f"Error getting local commit info: {e}")
            return None
    
    def check_for_updates(self):
        """Check if there are updates available"""
        try:
            local_info = self.get_local_commit_info()
            remote_info = self.get_latest_commit_info()
            
            if not local_info or not remote_info:
                return {
                    'status': 'error',
                    'message': 'Unable to check for updates',
                    'local_commit': local_info,
                    'remote_commit': remote_info
                }
            
            if local_info['sha'] == remote_info['sha']:
                return {
                    'status': 'up_to_date',
                    'message': 'Version Up To Date',
                    'local_commit': local_info,
                    'remote_commit': remote_info,
                    'last_check': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'update_available',
                    'message': 'Update Available',
                    'local_commit': local_info,
                    'remote_commit': remote_info,
                    'last_check': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error checking for updates: {str(e)}',
                'last_check': datetime.now().isoformat()
            }
    
    def perform_update(self):
        """Perform the update from GitHub"""
        try:
            # Change to the project directory
            os.chdir(self.local_git_path)
            
            # Fetch latest changes
            result = subprocess.run(
                ['git', 'fetch', 'origin'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                return {
                    'status': 'error',
                    'message': f'Failed to fetch updates: {result.stderr}'
                }
            
            # Pull latest changes
            result = subprocess.run(
                ['git', 'pull', 'origin', self.branch],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                return {
                    'status': 'error',
                    'message': f'Failed to pull updates: {result.stderr}'
                }
            
            # Check if requirements.txt changed and update dependencies
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0 and 'requirements.txt' in result.stdout:
                # Update dependencies in virtual environment
                if os.path.exists('venv'):
                    if os.name == 'nt':  # Windows
                        activate_script = os.path.join('venv', 'Scripts', 'activate.bat')
                        pip_cmd = os.path.join('venv', 'Scripts', 'pip')
                    else:  # macOS/Linux
                        activate_script = os.path.join('venv', 'bin', 'activate')
                        pip_cmd = os.path.join('venv', 'bin', 'pip')
                    
                    # Install updated dependencies
                    subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], timeout=120)
            
            return {
                'status': 'success',
                'message': 'Update completed successfully',
                'new_commit': self.get_local_commit_info(),
                'update_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error during update: {str(e)}'
            }
    
    def get_update_status_display(self):
        """Get formatted status for dashboard display"""
        update_info = self.check_for_updates()
        
        if update_info['status'] == 'up_to_date':
            return {
                'status': 'success',
                'message': 'Version Up To Date',
                'icon': '✅',
                'color': 'success',
                'show_update_button': False,
                'last_check': update_info.get('last_check', ''),
                'local_commit': update_info.get('local_commit', {}),
                'remote_commit': update_info.get('remote_commit', {})
            }
        elif update_info['status'] == 'update_available':
            return {
                'status': 'warning',
                'message': 'Update Available',
                'icon': '🔄',
                'color': 'warning',
                'show_update_button': True,
                'last_check': update_info.get('last_check', ''),
                'local_commit': update_info.get('local_commit', {}),
                'remote_commit': update_info.get('remote_commit', {})
            }
        else:
            return {
                'status': 'error',
                'message': 'Unable to Check Updates',
                'icon': '❌',
                'color': 'danger',
                'show_update_button': False,
                'last_check': update_info.get('last_check', ''),
                'error': update_info.get('message', 'Unknown error')
            }

# Test the updater if run directly
if __name__ == "__main__":
    updater = GitHubUpdater()
    print("Checking for updates...")
    status = updater.get_update_status_display()
    print(json.dumps(status, indent=2))
