from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from backend.db.session import get_db
from backend.db.models import Organization

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


def hash_api_key(api_key: str) -> str:
    """Hash an API key using bcrypt"""
    return pwd_context.hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    return pwd_context.verify(plain_key, hashed_key)


async def get_current_org(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Organization:
    """
    Dependency to get the current authenticated organization.
    Validates the API key from the Authorization header.
    """
    api_key = credentials.credentials
    
    # Look up organization by API key
    orgs = db.query(Organization).all()
    for org in orgs:
        if verify_api_key(api_key, org.api_key_hash):
            return org
    
    # No matching organization found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_org_id(org: Organization = Depends(get_current_org)) -> str:
    """Dependency to get just the org_id"""
    return org.id
