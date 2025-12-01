from pydantic import BaseModel, EmailStr
from models.auth import UserType, UserRole
import uuid
# Enum for role

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    account_type : UserType = UserType.INDIVIDUAL
    role: UserRole = UserRole.OWNER  # "individual" or "company"

class LoginRequest(BaseModel):
    username: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class NewUserAfterSignUp(BaseModel):
    kc_user_id: uuid.UUID
    email: EmailStr
    type: UserType
    company_id : int | None = None
    role : UserRole 
    
class SignupResponse(NewUserAfterSignUp):
    id: int
    credits_allocated : int