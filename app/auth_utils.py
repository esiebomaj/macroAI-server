from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_anon_client

bearer_scheme = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    Validates the Supabase JWT by calling supabase.auth.get_user().
    Supabase verifies the token signature and expiry internally.
    """
    token = credentials.credentials
    try:
        sb = get_anon_client()
        response = sb.auth.get_user(token)
        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        user = response.user
        return {
            "user_id": user.id,
            "email": user.email,
            "token": token
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
