from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.responses import TokenResponse
import jwt
from datetime import datetime, timedelta
from app.constants import settings
from app.db.supabase_auth import get_supabase_client

router = APIRouter()
security = HTTPBearer()

@router.get("/generate-token/", response_model=TokenResponse)
async def generate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Authenticate user with Supabase and generate a JWT token.
    
    Requires a valid Supabase token in the Authorization header.
    Returns a JWT token for API authentication if valid.
    """
    try:
        # Extract token from authorization header
        supabase_token = credentials.credentials
        
        # Initialize Supabase client
        supabase = get_supabase_client()
        
        # Verify the token with Supabase
        user = supabase.auth.get_user(supabase_token)
        
        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        
        # Create payload for JWT token
        payload = {
            "user_id": user.user.id,
            "email": user.user.email,
            "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        
        # Generate JWT token
        token = jwt.encode(
            payload, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        return {"access_token": token, "token_type": "bearer"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )