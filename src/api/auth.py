"""Authentication module for the Intelligent MCP Chatbot API."""

import jwt
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from utils.logger import get_logger

# Security scheme
security = HTTPBearer()
logger = get_logger(__name__)


class TokenData(BaseModel):
    """Token data model."""
    user_id: str
    email: Optional[str] = None
    exp: Optional[datetime] = None


class AuthConfig:
    """Authentication configuration."""
    def __init__(self, config: Dict[str, Any]):
        self.secret_key = config.get("secret_key", "your-secret-key-change-in-production")
        self.algorithm = config.get("algorithm", "HS256")
        self.access_token_expire_minutes = config.get("access_token_expire_minutes", 30)
        self.enabled = config.get("enabled", False)


class AuthManager:
    """Authentication manager."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize authentication manager."""
        self.config = AuthConfig(config)
        self.logger = get_logger(__name__)
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.config.secret_key, algorithm=self.config.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify JWT token and return token data."""
        try:
            payload = jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
            user_id: str = payload.get("user_id")
            email: Optional[str] = payload.get("email")
            exp: Optional[datetime] = payload.get("exp")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return TokenData(user_id=user_id, email=email, exp=exp)
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def create_user_token(self, user_id: str, email: Optional[str] = None) -> str:
        """Create token for user."""
        data = {
            "user_id": user_id,
            "email": email,
            "jti": str(uuid.uuid4())  # JWT ID for uniqueness
        }
        return self.create_access_token(data)


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get authentication manager instance."""
    global _auth_manager
    if _auth_manager is None:
        raise RuntimeError("Auth manager not initialized. Call init_auth_manager() first.")
    return _auth_manager


def init_auth_manager(config: Dict[str, Any]):
    """Initialize authentication manager."""
    global _auth_manager
    _auth_manager = AuthManager(config)
    logger.info("Authentication manager initialized")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Get current user from JWT token."""
    auth_manager = get_auth_manager()
    
    if not auth_manager.config.enabled:
        # Return default user when auth is disabled
        return TokenData(user_id="anonymous", email="anonymous@example.com")
    
    token_data = auth_manager.verify_token(credentials.credentials)
    return token_data


def create_access_token(user_id: str, email: Optional[str] = None) -> str:
    """Create access token for user."""
    auth_manager = get_auth_manager()
    return auth_manager.create_user_token(user_id, email)


# Mock user management (replace with database in production)
class MockUserManager:
    """Mock user manager for development."""
    
    def __init__(self):
        self.users = {
            "demo_user": {
                "user_id": "demo_user",
                "email": "demo@example.com",
                "name": "Demo User",
                "created_at": datetime.utcnow(),
                "metadata": {}
            }
        }
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def create_user(self, email: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Create new user."""
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        user = {
            "user_id": user_id,
            "email": email,
            "name": name or email.split("@")[0],
            "created_at": datetime.utcnow(),
            "metadata": {}
        }
        self.users[user_id] = user
        return user


# Global user manager instance
_user_manager = MockUserManager()


def get_user_manager() -> MockUserManager:
    """Get user manager instance."""
    return _user_manager 