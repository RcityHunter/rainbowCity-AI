"""
Simplified OAuth callback handlers to fix the authentication issues
"""
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging
import uuid
from datetime import datetime

from app.utils.oauth_utils import get_google_token, get_google_user_info
from app.utils.auth_utils import create_access_token
from app.db import USE_MOCK_MODE
from app.utils.mock_oauth import create_mock_google_user, get_mock_user, get_all_mock_users

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/oauth", tags=["OAuth Callbacks"])

@router.post("/google/callback")
async def google_callback(request: Request):
    """
    Handle Google OAuth callback - simplified version
    """
    logger.info("Received Google OAuth callback")
    
    try:
        # Get authorization code from request body
        body = await request.json()
        code = body.get("code")
        
        if not code:
            logger.error("No authorization code found in request")
            raise HTTPException(status_code=400, detail="Authorization code is required")
        
        logger.info(f"Received Google authorization code: {code[:5]}...")
        
        # If in mock mode, create a mock user
        if USE_MOCK_MODE:
            logger.info("Using mock mode for Google OAuth")
            
            # Create a mock user with the email from the request
            email = body.get("email", "mock_user@example.com")
            name = body.get("name", "Mock User")
            picture = body.get("picture", "")
            
            # Create or get the mock user
            user = get_mock_user(email)
            if not user:
                logger.info(f"Creating new mock user with email: {email}")
                user = create_mock_google_user(email, name, picture)
            else:
                logger.info(f"Found existing mock user with email: {email}")
            
            # Create access token
            user_id = user.get('id')
            token_data = {"sub": f"users:{user_id}"}
            access_token = create_access_token(token_data)
            
            # Remove sensitive information
            if 'password_hash' in user:
                del user['password_hash']
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": user
            }
        
        # Get access token
        token_data = await get_google_token(code)
        if not token_data:
            logger.error("Failed to get Google access token - token_data is None")
            raise HTTPException(status_code=400, detail="Failed to get access token - no response from Google")
        
        if "access_token" not in token_data:
            logger.error(f"Failed to get Google access token - missing access_token in response: {token_data}")
            raise HTTPException(status_code=400, detail="Failed to get access token - invalid response from Google")
        
        access_token = token_data["access_token"]
        logger.info("Successfully obtained Google access token")
        
        # Get user info
        user_info = await get_google_user_info(access_token)
        if not user_info:
            logger.error("Failed to get Google user info")
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        # Extract user data
        email = user_info.get('email')
        if not email:
            logger.error("No email found in Google user info")
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Check if user exists
        user = get_mock_user(email)
        
        if user:
            # Update existing user
            user_id = user.get('id')
            logger.info(f"Found existing user with email {email}, ID: {user_id}")
            
            # Update OAuth info
            user['oauth_info'] = {
                'google': {
                    'id': user_info.get('sub', 'unknown'),
                    'name': user_info.get('name', user.get('display_name')),
                    'picture': user_info.get('picture', ''),
                    'last_login': datetime.utcnow().isoformat(),
                    'access_token': access_token
                }
            }
        else:
            # Create new user
            user_id = str(uuid.uuid4())
            username = f"google_{email.split('@')[0]}"
            display_name = user_info.get('name', username)
            
            logger.info(f"Creating new user with ID: {user_id}, username: {username}")
            
            # Create user
            user = create_mock_google_user(email, display_name, user_info.get('picture', ''))
        
        # Create access token
        token_data = {"sub": f"users:{user_id}"}
        access_token = create_access_token(token_data)
        logger.info(f"Created access token for user: {user_id}")
        
        # Remove sensitive information
        if 'password_hash' in user:
            del user['password_hash']
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Google callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process Google callback: {str(e)}")
