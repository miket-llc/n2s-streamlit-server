#!/usr/bin/env python3
"""
GitHub Repository Monitor
Polls GitHub repositories for changes and triggers updates
Much more secure than push-based webhooks
"""

import json
import os
import subprocess
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests

# Configuration
CONFIG_FILE = "/mnt/storage/streamlit-server/config/monitor-config.json"
LOG_FILE = "/mnt/storage/streamlit-server/logs/github-monitor.log"
POLL_INTERVAL = 300  # 5 minutes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GitHubMonitor:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = self.load_config()
        self.last_commits = {}
        
    def load_config(self) -> Dict:
        """Load monitoring configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_file} not found, using defaults")
            return {
                "repositories": [
                    {
                        "name": "n2s-tmmi-tracker",
                        "owner": "miket-llc",
                        "branch": "main",
                        "path": "/mnt/storage/streamlit-server/apps/n2s-tmmi-tracker"
                    },
                    {
                        "name": "n2s-impact-model", 
                        "owner": "miket-llc",
                        "branch": "main",
                        "path": "/mnt/storage/streamlit-server/apps/n2s-impact-model"
                    }
                ],
                "poll_interval": 300,
                "max_retries": 3
            }
    
    def get_latest_commit(self, owner: str, repo: str, branch: str) -> Optional[Dict]:
        """Get the latest commit from GitHub API"""
        url = f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}"
        
        try:
            headers = {}
            # Add GitHub token if available (for higher rate limits)
            github_token = os.getenv('GITHUB_TOKEN')
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            commit_data = response.json()
            return {
                'sha': commit_data['sha'],
                'short_sha': commit_data['sha'][:7],
                'message': commit_data['commit']['message'].split('\n')[0],
                'author': commit_data['commit']['author']['name'],
                'date': commit_data['commit']['author']['date']
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to get latest commit for {owner}/{repo}: {e}")
            return None
    
    def get_local_commit(self, repo_path: str) -> Optional[str]:
        """Get the current local commit SHA"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout getting local commit for {repo_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to get local commit for {repo_path}: {e}")
            return None
    
    def update_repository(self, repo_config: Dict) -> bool:
        """Update a repository and restart its container"""
        repo_name = repo_config['name']
        repo_path = repo_config['path']
        
        logger.info(f"Updating {repo_name}...")
        
        try:
            # Pull latest changes
            result = subprocess.run(
                ['git', 'pull', 'origin', repo_config['branch']],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Git pull failed for {repo_name}: {result.stderr}")
                return False
            
            # Restart container
            subprocess.run([
                '/mnt/storage/streamlit-server/scripts/webhook/update-app.sh',
                repo_name
            ], timeout=120)
            
            logger.info(f"Successfully updated {repo_name}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout updating {repo_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to update {repo_name}: {e}")
            return False
    
    def check_repository(self, repo_config: Dict) -> bool:
        """Check if a repository needs updating"""
        owner = repo_config['owner']
        name = repo_config['name']
        branch = repo_config['branch']
        path = repo_config['path']
        
        # Get remote latest commit
        latest_commit = self.get_latest_commit(owner, name, branch)
        if not latest_commit:
            return False
        
        # Get local commit
        local_commit = self.get_local_commit(path)
        if not local_commit:
            logger.warning(f"Could not get local commit for {name}")
            return False
        
        # Check if update needed
        if latest_commit['sha'] != local_commit:
            logger.info(f"Update needed for {name}")
            logger.info(f"  Remote: {latest_commit['short_sha']} - {latest_commit['message']}")
            logger.info(f"  Local:  {local_commit[:7]}")
            
            return self.update_repository(repo_config)
        else:
            logger.debug(f"No update needed for {name}")
            return True
    
    def run_once(self):
        """Run one check cycle"""
        logger.info("Starting repository check cycle")
        
        for repo_config in self.config['repositories']:
            try:
                self.check_repository(repo_config)
            except Exception as e:
                logger.error(f"Error checking {repo_config['name']}: {e}")
        
        logger.info("Repository check cycle complete")
    
    def run_continuous(self):
        """Run continuous monitoring"""
        logger.info("Starting GitHub repository monitor")
        logger.info(f"Monitoring {len(self.config['repositories'])} repositories")
        logger.info(f"Poll interval: {self.config.get('poll_interval', POLL_INTERVAL)} seconds")
        
        while True:
            try:
                self.run_once()
                time.sleep(self.config.get('poll_interval', POLL_INTERVAL))
            except KeyboardInterrupt:
                logger.info("Stopping monitor")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    import sys
    
    # Ensure directories exist
    os.makedirs("/mnt/storage/streamlit-server/logs", exist_ok=True)
    os.makedirs("/mnt/storage/streamlit-server/config", exist_ok=True)
    
    monitor = GitHubMonitor(CONFIG_FILE)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        monitor.run_once()
    else:
        monitor.run_continuous()
