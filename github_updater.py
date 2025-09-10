#!/usr/bin/env python3
"""
GitHub Updater for Vosk Caption App
Handles automatic updates from GitHub repository
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

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def check_for_updates():
    """Check for updates on GitHub"""
    logger = setup_logging()
    
    try:
        # Get current commit hash
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        current_commit = result.stdout.strip()
        
        # Fetch latest from origin
        subprocess.run(['git', 'fetch', 'origin'], cwd=os.getcwd())
        
        # Get latest commit hash
        result = subprocess.run(['git', 'rev-parse', 'origin/main'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        latest_commit = result.stdout.strip()
        
        if current_commit != latest_commit:
            logger.info(f"Update available: {current_commit[:8]} -> {latest_commit[:8]}")
            return True, latest_commit
        else:
            logger.info("No updates available")
            return False, current_commit
            
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return False, None

def get_update_info():
    """Get information about available updates"""
    logger = setup_logging()
    
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
        logger.error(f"Error getting update info: {e}")
        return {'commits': [], 'changes': [], 'commit_count': 0}

def apply_update():
    """Apply the update from GitHub"""
    logger = setup_logging()
    
    try:
        logger.info("Applying update...")
        
        # Stash any local changes
        subprocess.run(['git', 'stash'], cwd=os.getcwd())
        
        # Pull latest changes
        result = subprocess.run(['git', 'pull', 'origin', 'main'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            logger.info("Update applied successfully")
            
            # Check if requirements.txt changed
            if os.path.exists('requirements.txt'):
                logger.info("Updating Python dependencies...")
                subprocess.run(['pip', 'install', '-r', 'requirements.txt'], 
                             cwd=os.getcwd())
            
            return True
        else:
            logger.error(f"Failed to apply update: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error applying update: {e}")
        return False

def backup_current_version():
    """Create a backup of the current version"""
    logger = setup_logging()
    
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
        
        logger.info(f"Backup created: {backup_dir}")
        return backup_dir
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return None

def restart_application():
    """Restart the application after update"""
    logger = setup_logging()
    
    try:
        logger.info("Restarting application...")
        
        # Kill existing process
        subprocess.run(['pkill', '-f', 'python3 captionStable.py'], 
                      capture_output=True)
        
        # Wait a moment
        time.sleep(2)
        
        # Start new process
        subprocess.Popen(['python3', 'captionStable.py'], 
                        cwd=os.getcwd())
        
        logger.info("Application restarted")
        return True
        
    except Exception as e:
        logger.error(f"Error restarting application: {e}")
        return False

def main():
    """Main update process"""
    logger = setup_logging()
    
    logger.info("🔄 GitHub Updater Started")
    
    try:
        # Check for updates
        has_update, commit_hash = check_for_updates()
        
        if not has_update:
            logger.info("✅ No updates available")
            return
        
        # Get update information
        update_info = get_update_info()
        
        logger.info(f"📦 Update available with {update_info['commit_count']} commits")
        
        # Show what will be updated
        if update_info['commits']:
            logger.info("📝 Recent commits:")
            for commit in update_info['commits'][:5]:  # Show last 5
                logger.info(f"   - {commit}")
        
        # Create backup
        backup_dir = backup_current_version()
        if not backup_dir:
            logger.error("Failed to create backup, aborting update")
            return
        
        # Apply update
        if apply_update():
            logger.info("✅ Update applied successfully")
            
            # Restart application
            if restart_application():
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
