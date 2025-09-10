#!/usr/bin/env python3
"""
GitHub Updater for Vosk Caption App
Handles automatic updates from GitHub repository
Integrates with dashboard system updates section
"""

import os
import json
import logging
import subprocess
import requests
import time
from datetime import datetime

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    return logging.getLogger(__name__)

class GitHubUpdater:
    """GitHub Updater class for dashboard integration"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.current_commit = None
        self.latest_commit = None
        self.update_available = False
        self.update_info = {}
    
    def get_current_commit(self):
        """Get current commit hash"""
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Error getting current commit: {e}")
            return None
    
    def get_latest_commit(self):
        """Get latest commit hash from origin"""
        try:
            # Fetch latest from origin
            subprocess.run(['git', 'fetch', 'origin'], cwd=os.getcwd())
            
            # Get latest commit hash
            result = subprocess.run(['git', 'rev-parse', 'origin/main'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Error getting latest commit: {e}")
            return None
    
    def check_for_updates(self):
        """Check for updates and return status"""
        self.current_commit = self.get_current_commit()
        self.latest_commit = self.get_latest_commit()
        
        if not self.current_commit or not self.latest_commit:
            return {
                'status': 'error',
                'message': 'Unable to check for updates'
            }
        
        self.update_available = self.current_commit != self.latest_commit
        
        if self.update_available:
            self.update_info = self.get_update_info()
            return {
                'status': 'update_available',
                'current_commit': self.current_commit[:8],
                'latest_commit': self.latest_commit[:8],
                'commit_count': self.update_info.get('commit_count', 0),
                'commits': self.update_info.get('commits', [])[:5],  # Last 5 commits
                'changes': self.update_info.get('changes', [])
            }
        else:
            return {
                'status': 'up_to_date',
                'current_commit': self.current_commit[:8],
                'message': 'No updates available'
            }
    
    def get_update_info(self):
        """Get information about available updates"""
        try:
            # Get commit messages since current commit
            result = subprocess.run(['git', 'log', '--oneline', 'HEAD..origin/main'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            commits = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # Get file changes
            result = subprocess.run(['git', 'diff', '--name-status', 'HEAD..origin/main'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            return {
                'commits': commits,
                'changes': changes,
                'commit_count': len(commits)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting update info: {e}")
            return {'commits': [], 'changes': [], 'commit_count': 0}
    
    def get_update_status_display(self):
        """Get update status for dashboard display"""
        return self.check_for_updates()
    
    def apply_update(self):
        """Apply the update from GitHub"""
        try:
            self.logger.info("Applying update...")
            
            # Stash any local changes
            subprocess.run(['git', 'stash'], cwd=os.getcwd())
            
            # Pull latest changes
            result = subprocess.run(['git', 'pull', 'origin', 'main'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                self.logger.info("Update applied successfully")
                
                # Check if requirements.txt changed
                if os.path.exists('requirements.txt'):
                    self.logger.info("Updating Python dependencies...")
                    subprocess.run(['pip', 'install', '-r', 'requirements.txt'], 
                                 cwd=os.getcwd())
                
                return True
            else:
                self.logger.error(f"Failed to apply update: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error applying update: {e}")
            return False
    
    def backup_current_version(self):
        """Create a backup of the current version"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"backup_{timestamp}"
            
            # Create backup directory
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copy essential files
            essential_files = [
                'captionStable.py',
                'vosk_speech_recognizer.py',
                'config.json',
                'dictionary.json',
                'requirements.txt'
            ]
            
            for file in essential_files:
                if os.path.exists(file):
                    subprocess.run(['cp', file, backup_dir])
            
            self.logger.info(f"Backup created: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return None

    def restart_application(self):
        """Restart the application after update"""
        try:
            self.logger.info("Restarting application...")
            
            # Kill existing process
            subprocess.run(['pkill', '-f', 'python3 captionStable.py'], 
                          capture_output=True)
            
            # Wait a moment
            time.sleep(2)
            
            # Start new process
            subprocess.Popen(['python3', 'captionStable.py'], 
                            cwd=os.getcwd())
            
            self.logger.info("Application restarted")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restarting application: {e}")
            return False

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def check_for_updates():
    """Check for updates on GitHub (legacy function)"""
    updater = GitHubUpdater()
    return updater.check_for_updates()

def get_update_info():
    """Get information about available updates (legacy function)"""
    updater = GitHubUpdater()
    return updater.get_update_info()

def apply_update():
    """Apply the update from GitHub (legacy function)"""
    updater = GitHubUpdater()
    return updater.apply_update()

def backup_current_version():
    """Create a backup of the current version (legacy function)"""
    updater = GitHubUpdater()
    return updater.backup_current_version()

def restart_application():
    """Restart the application after update (legacy function)"""
    updater = GitHubUpdater()
    return updater.restart_application()

def main():
    """Main update process"""
    logger = setup_logging()
    
    logger.info("🔄 GitHub Updater Started")
    
    try:
        updater = GitHubUpdater()
        
        # Check for updates
        status = updater.check_for_updates()
        
        if status['status'] != 'update_available':
            logger.info("✅ No updates available")
            return
        
        logger.info(f"📦 Update available with {status['commit_count']} commits")
        
        # Show what will be updated
        if status.get('commits'):
            logger.info("📝 Recent commits:")
            for commit in status['commits'][:5]:  # Show last 5
                logger.info(f"   - {commit}")
        
        # Create backup
        backup_dir = updater.backup_current_version()
        if not backup_dir:
            logger.error("Failed to create backup, aborting update")
            return
        
        # Apply update
        if updater.apply_update():
            logger.info("✅ Update applied successfully")
            
            # Restart application
            if updater.restart_application():
                logger.info("🎉 Update complete! Application restarted.")
            else:
                logger.warning("⚠️  Update applied but failed to restart application")
        else:
            logger.error("❌ Failed to apply update")
            
            # Restore from backup
            logger.info("Restoring from backup...")
            for file in os.listdir(backup_dir):
                subprocess.run(['cp', os.path.join(backup_dir, file), '.'], 
                             cwd=os.getcwd())
            
    except Exception as e:
        logger.error(f"Error in update process: {e}")

if __name__ == "__main__":
    main()
