"""
Configuration settings for the Office Room Allocation System
"""
import os
from datetime import datetime

# Create directories if they don't exist
os.makedirs('data', exist_ok=True)
os.makedirs('data/backup', exist_ok=True)

# File paths
DEFAULT_EXCEL_PATH = 'data/MP_Office_Allocation.xlsx'
CAPACITY_CONFIG_PATH = 'data/room_capacities.json'
BACKUP_DIR = 'data/backup'

# Authentication
DEFAULT_PASSWORD = "kluth2025"  # Would be better stored securely
SESSION_TIMEOUT_MINUTES = 60

# UI Configuration
PAGE_TITLE = "Office Room Allocation System"
PAGE_ICON = "🏢"
SIDEBAR_ICON = "https://cdn-icons-png.flaticon.com/512/2329/2329140.png"
APP_VERSION = "3.0"

# Room status colors
ROOM_STATUS_COLORS = {
    'vacant': {
        'class': 'room-vacant',
        'bg_color': '#d4edda',
        'border_color': '#28a745'
    },
    'low': {
        'class': 'room-low',
        'bg_color': '#e6f7e1',
        'border_color': '#5cb85c'
    },
    'medium': {
        'class': 'room-medium',
        'bg_color': '#fff3cd',
        'border_color': '#ffc107'
    },
    'high': {
        'class': 'room-high',
        'bg_color': '#ffe5d9',
        'border_color': '#fd7e14'
    },
    'full': {
        'class': 'room-full',
        'bg_color': '#f8d7da',
        'border_color': '#dc3545'
    },
    'storage': {
        'class': 'room-storage',
        'bg_color': '#e2e3e5',
        'border_color': '#6c757d'
    },
    'overfilled': {  # Added overfilled status for rooms exceeding capacity
        'class': 'room-overfilled',
        'bg_color': '#f5c6cb',
        'border_color': '#b21f2d'
    }
}

# CSV Column Names
REQUIRED_COLUMNS = ['Name', 'Status', 'Email address', 'Position', 'Office', 'Building']
COLUMN_MAPPING = {
    'Office': 'Office',
    'Office    ': 'Office',
    'Room': 'Office',
    'Room Number': 'Office',
    'Building': 'Building',
    'Building    ': 'Building',
    'Location': 'Building',
    'Email': 'Email address'
}

# Function to get current timestamp for file naming
def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")