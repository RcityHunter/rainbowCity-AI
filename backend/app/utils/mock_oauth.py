"""
Mock OAuth utilities for development and testing
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Setup logging
logger = logging.getLogger(__name__)

# In-memory storage for mock users
mock_users = {}

def store_mock_user(user_data: Dict[str, Any]) -> None:
    """
    Store a user in the mock database
    """
    user_id = user_data.get('id')
    email = user_data.get('email')
    
    if not user_id or not email:
        logger.error("Cannot store user without ID and email")
        return
        
    mock_users[user_id] = user_data
    mock_users[email] = user_data
    
    logger.info(f"Stored mock user with ID: {user_id} and email: {email}")
    logger.info(f"Total mock users: {len(mock_users) // 2}")  # Divide by 2 because we store each user twice

def get_mock_user(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Get a user from the mock database by ID or email
    """
    if identifier in mock_users:
        logger.info(f"Found mock user with identifier: {identifier}")
        return mock_users[identifier]
    
    logger.info(f"No mock user found with identifier: {identifier}")
    return None

def get_all_mock_users() -> list:
    """
    Get all users from the mock database
    """
    # Filter out email keys to avoid duplicates
    unique_users = []
    seen_ids = set()
    
    for key, user in mock_users.items():
        user_id = user.get('id')
        if user_id and user_id not in seen_ids:
            unique_users.append(user)
            seen_ids.add(user_id)
    
    return unique_users

def create_mock_google_user(email: str, name: str, picture: str = None) -> Dict[str, Any]:
    """
    Create a mock Google user
    """
    user_id = str(uuid.uuid4())
    username = f"google_{email.split('@')[0]}"
    display_name = name or username
    
    # Generate a random password (user won't need it since they'll use OAuth)
    random_password = str(uuid.uuid4())
    
    # Create OAuth info
    oauth_info = {
        'google': {
            'id': f"mock_google_{user_id[:8]}",
            'name': display_name,
            'picture': picture or '',
            'last_login': datetime.utcnow().isoformat(),
            'access_token': f"mock_token_{user_id[:8]}"
        }
    }
    
    # Create user object
    user = {
        'id': user_id,
        'email': email,
        'username': username,
        'display_name': display_name,
        'password_hash': f"mock_hash_{random_password[:8]}",
        'created_at': datetime.utcnow().isoformat(),
        'is_activated': True,
        'activation_status': 'active',
        'roles': ['user'],
        'vip_level': 'basic',
        'oauth_info': oauth_info,
        'oauth_provider': 'google'
    }
    
    # Store the user
    store_mock_user(user)
    
    return user
