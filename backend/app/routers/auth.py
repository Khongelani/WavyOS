from fastapi import APIRouter, HTTPException, status
from app.auth import verify_password, create_access_token, hash_password
from app.config import settings
from app.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_hashed_owner_password = hash_password(settings.OWNER_PASSWORD)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    if req.email.lower() != settings.OWNER_EMAIL.lower():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(req.password, _hashed_owner_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": req.email})
    return TokenResponse(access_token=token)
