"""
Authentication Helper Functions
Provides consistent JWT identity handling and user retrieval
"""

from flask_jwt_extended import get_jwt_identity
from app.models import User
import logging

logger = logging.getLogger(__name__)


def get_current_user_id():
    """
    Get user_id consistently from JWT identity
    
    JWT identity can be either int (user_id) or str (username)
    This function handles both cases and returns user_id
    
    Returns:
        int: User ID if found, None otherwise
    """
    try:
        identity = get_jwt_identity()
        
        if identity is None:
            return None
        
        # If identity is already an integer (user_id)
        if isinstance(identity, int):
            return identity
        
        # If identity is a string (username)
        if isinstance(identity, str):
            user = User.query.filter_by(username=identity).first()
            if user:
                return user.id
            else:
                logger.warning(f"User with username '{identity}' not found in database")
                return None
        
        # Unexpected type
        logger.error(f"Unexpected JWT identity type: {type(identity)}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting current user ID: {e}")
        return None


def get_current_user():
    """
    Get complete User object from JWT identity
    
    Returns:
        User: User object if found, None otherwise
    """
    user_id = get_current_user_id()
    if user_id:
        return User.query.get(user_id)
    return None


def get_current_username():
    """
    Get username from JWT identity or User object
    
    Returns:
        str: Username if found, None otherwise
    """
    user = get_current_user()
    return user.username if user else None


def require_role(allowed_roles):
    """
    Decorator to check if current user has required role
    
    Usage:
        @require_role(['admin', 'manager'])
        def my_function():
            pass
    
    Args:
        allowed_roles: List of allowed role names
    
    Returns:
        Decorator function
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            
            if not user:
                from flask import jsonify
                return jsonify({'error': 'User not authenticated'}), 401
            
            if user.role not in allowed_roles:
                from flask import jsonify
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
