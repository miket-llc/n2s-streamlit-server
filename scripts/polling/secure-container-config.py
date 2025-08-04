#!/usr/bin/env python3
"""
Generate secure Docker Compose configuration with proper sandboxing
"""

import json
import yaml
from pathlib import Path

def generate_secure_compose():
    """Generate a secure docker-compose configuration"""
    
    base_config = {
        'version': '3.8',
        'services': {
            'nginx': {
                'image': 'nginx:alpine',
                'container_name': 'streamlit-nginx',
                'ports': ['80:80', '443:443'],
                'volumes': [
                    './nginx/conf.d:/etc/nginx/conf.d:ro',
                    './nginx/nginx.conf:/etc/nginx/nginx.conf:ro',
                    './logs/nginx:/var/log/nginx',
                    './ssl:/etc/nginx/ssl:ro'
                ],
                'networks': ['streamlit-network'],
                'restart': 'unless-stopped',
                'security_opt': ['no-new-privileges:true'],
                'read_only': True,
                'tmpfs': ['/tmp', '/var/cache/nginx', '/var/run'],
                'depends_on': ['sample-app']
            }
        },
        'networks': {
            'streamlit-network': {
                'driver': 'bridge',
                'driver_opts': {
                    'com.docker.network.bridge.enable_icc': 'false'
                }
            }
        }
    }
    
    # App template with security hardening
    app_template = {
        'image': 'python:3.11-slim',
        'working_dir': '/app',
        'networks': ['streamlit-network'],
        'restart': 'unless-stopped',
        'security_opt': [
            'no-new-privileges:true'
        ],
        'cap_drop': ['ALL'],
        'cap_add': ['SETGID', 'SETUID'],  # Minimal caps for Python
        'read_only': True,
        'tmpfs': [
            '/tmp:rw,noexec,nosuid,size=100m',
            '/app/.streamlit:rw,noexec,nosuid,size=10m',
            '/home/nobody:rw,noexec,nosuid,size=10m'
        ],
        'user': 'nobody:nogroup',
        'environment': {
            'PYTHONPATH': '/app',
            'STREAMLIT_SERVER_HEADLESS': 'true',
            'STREAMLIT_BROWSER_GATHER_USAGE_STATS': 'false'
        },
        'deploy': {
            'resources': {
                'limits': {
                    'cpus': '1.0',
                    'memory': '512M'
                },
                'reservations': {
                    'cpus': '0.25',
                    'memory': '128M'
                }
            }
        },
        'healthcheck': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:8501/_stcore/health'],
            'interval': '30s',
            'timeout': '10s',
            'retries': 3,
            'start_period': '40s'
        },
        'expose': ['8501']
    }
    
    # Add apps
    apps = [
        {
            'name': 'sample-app',
            'path': './apps/sample-app',
            'command': 'sh -c "pip install --no-cache-dir streamlit pandas numpy matplotlib seaborn && streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true"'
        },
        {
            'name': 'n2s-tmmi-tracker',
            'path': './apps/n2s-tmmi-tracker',
            'command': 'sh -c "pip install --no-cache-dir -r requirements.txt && streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true"'
        },
        {
            'name': 'n2s-impact-model',
            'path': './apps/n2s-impact-model',
            'command': 'sh -c "pip install --no-cache-dir -r requirements.txt && streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true"'
        }
    ]
    
    for app in apps:
        app_config = app_template.copy()
        app_config['container_name'] = f"streamlit-{app['name']}"
        app_config['volumes'] = [f"{app['path']}:/app:ro"]
        app_config['command'] = app['command']
        
        base_config['services'][app['name']] = app_config
    
    return base_config

if __name__ == "__main__":
    config = generate_secure_compose()
    
    # Write to file
    with open('/mnt/storage/streamlit-server/docker-compose.secure.yml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print("✅ Generated secure docker-compose.secure.yml")
