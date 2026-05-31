from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from typing import List
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        # In a real app we fetch user object from DB using user_id
        # For performance and decoupling, we trust the JWT roles explicitly embedded.
        user_role: str = payload.get("role", "PATIENT")
        if user_id is None:
            raise credentials_exception
        
        # Simulating User Object 
        return {"id": user_id, "role": user_role}
    except jwt.PyJWTError:
        raise credentials_exception

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)):
        # Bác sĩ hoặc nhân viên sẽ có Role tương ứng. ADMIN có quyền Root Override
        if current_user.get("role") == "ADMIN":
            return True
            
        if current_user.get("role") not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System Restriction: You do not have permission to perform this action. Required roles: " + ", ".join(self.allowed_roles)
            )
        return True
