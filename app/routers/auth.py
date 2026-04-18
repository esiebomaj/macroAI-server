from fastapi import APIRouter, HTTPException, Depends
from app.schemas import UserRegister, UserLogin, TokenResponse
from app.database import get_anon_client
from app.auth_utils import get_current_user

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: UserRegister):
    """Supabase Auth handles hashing, storage, and email confirmation."""
    sb = get_anon_client()
    try:
        response = sb.auth.sign_up({
            "email": body.email,
            "password": body.password
        })
        if not response.user:
            raise HTTPException(status_code=400, detail="Registration failed")

        # Seed default goals for new user
        from app.database import get_service_client
        get_service_client().table("goals").insert({
            "user_id": response.user.id,
            "cal": 2000, "pro": 160, "carb": 180, "fat": 71
        }).execute()

        return TokenResponse(
            access_token=response.session.access_token,
            user_id=response.user.id,
            email=response.user.email
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin):
    """Supabase Auth verifies the password and returns a signed JWT."""
    sb = get_anon_client()
    try:
        response = sb.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password
        })
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        return TokenResponse(
            access_token=response.session.access_token,
            user_id=response.user.id,
            email=response.user.email
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    sb = get_anon_client()
    sb.auth.sign_out()
    return {"message": "Logged out"}


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["user_id"], "email": current_user["email"]}
