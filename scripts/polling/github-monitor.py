#!/usr/bin/env python3
"""
GitHub Repository Monitor
Monitors GitHub repositories for changes and updates local containers accordingly.
"""

import json
import subprocess
import time
import logging
import argparse
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/mnt/storage/streamlit-server/logs/github-monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from JSON file"""
    config_path = Path('/mnt/storage/streamlit-server/config/monitor-config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            logger.info(f"Loaded configuration for {len(config['repositories'])} repositories")
            return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return None

def get_remote_commit_hash(repo_path, branch):
    """Get the latest commit hash from remote"""
    try:
        # Fetch latest changes
        result = subprocess.run(
            ['git', 'fetch', 'origin'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"Git fetch failed: {result.stderr}")
            return None
            
        # Get remote commit hash
        result = subprocess.run(
            ['git', 'rev-parse', f'origin/{branch}'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            logger.error(f"Failed to get remote commit hash: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting remote commit hash: {e}")
        return None

def get_local_commit_hash(repo_path, branch):
    """Get the current local commit hash"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            logger.error(f"Failed to get local commit hash: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting local commit hash: {e}")
        return None

def update_repository(repo_name, repo_config):
    """Update a repository and restart its container"""
    repo_path = Path(repo_config['path'])
    
    if not repo_path.exists():
        logger.error(f"Repository path does not exist: {repo_path}")
        return False
    
    try:
        # Get current local commit
        local_hash = get_local_commit_hash(repo_path, repo_config['branch'])
        if not local_hash:
            logger.error(f"Could not determine local commit for {repo_name}")
            return False
        
        # Get remote commit hash
        remote_hash = get_remote_commit_hash(repo_path, repo_config['branch'])
        if not remote_hash:
            logger.error(f"Could not determine remote commit for {repo_name}")
            return False
        
        # Check if update is needed
        if local_hash == remote_hash:
            logger.info(f"No updates for {repo_name} (already at {local_hash[:8]})")
            return True
        
        logger.info(f"Updating {repo_name}: {local_hash[:8]} -> {remote_hash[:8]}")
        
        # Force update to remote version (this avoids merge conflicts)
        result = subprocess.run(
            ['git', 'reset', '--hard', f'origin/{repo_config["branch"]}'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.error(f"Git reset failed for {repo_name}: {result.stderr}")
            return False
        
        logger.info(f"Successfully updated {repo_name} to {remote_hash[:8]}")
        
        # Restart container
        logger.info(f"Restarting container for {repo_name}")
        result = subprocess.run(
            ['/mnt/storage/streamlit-server/scripts/webhook/update-app.sh', repo_name],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully restarted container for {repo_name}")
            return True
        else:
            logger.error(f"Failed to restart container for {repo_name}: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating {repo_name}: {e}")
        return False

def monitor_repositories(config, once=False):
    """Monitor repositories for changes"""
    repositories = config['repositories']
    poll_interval = config.get('poll_interval', 300)  # Default 5 minutes
    
    while True:
        logger.info("=== Starting repository check ===")
        
        for repo in repositories:
            repo_name = repo['name']
            logger.info(f"Checking {repo_name}...")
            
            try:
                update_repository(repo_name, repo)
            except Exception as e:
                logger.error(f"Error processing {repo_name}: {e}")
        
        logger.info("=== Repository check complete ===")
        
        if once:
            break
            
        logger.info(f"Waiting {poll_interval} seconds until next check...")
        time.sleep(poll_interval)

def main():
    parser = argparse.ArgumentParser(description='GitHub Repository Monitor')
    parser.add_argument('--once', action='store_true', 
                       help='Run once and exit (don\'t loop)')
    args = parser.parse_args()
    
    # Ensure log directory exists
    Path('/mnt/storage/streamlit-server/logs').mkdir(exist_ok=True)
    
    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration, exiting")
        sys.exit(1)
    
    logger.info("GitHub Repository Monitor starting...")
    
    try:
        monitor_repositories(config, once=args.once)
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Monitor crashed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
