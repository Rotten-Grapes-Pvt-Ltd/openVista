from fastapi import APIRouter, HTTPException, Depends
from keycloak.exceptions import KeycloakGetError
from core.keycloak import keycloak_admin, keycloak_openid,get_userinfo_from_keycloak,oauth2_scheme
from schemas.auth import SignupRequest, LoginRequest, TokenResponse,NewUserAfterSignUp,SignupResponse
from models.auth import User
from models.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.deps import get_bearer_token,get_user_by_kc_id

router = APIRouter()

@router.post("/signup", response_model=SignupResponse)
async def signup(data: SignupRequest,session: AsyncSession = Depends(get_db)):
    try:
        # 🔹 Create user in Keycloak
        user_id = keycloak_admin.create_user({
            "email": data.email,
            "username": data.email,
            "enabled": True,
            "firstName": data.first_name,
            "lastName": data.last_name,
            "credentials": [{
                "type": "password",
                "value": data.password,
                "temporary": False
            }],
            "attributes": {
                "account_type": data.account_type,
                "role" : data.role
            }
        })

        # Keycloak sometimes returns no user_id → fetch using email
        if not user_id:
            user_id = keycloak_admin.get_user_id(data.email)
            # Add entry to DB as well
        db_user = User(kc_user_id=user_id, email=data.email, type=data.account_type, role=data.role)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        # 3. Return success
        return SignupResponse(
            id=db_user.id,
            kc_user_id=db_user.kc_user_id,
            email=db_user.email,
            type=db_user.type,
            
        )   
        # return {"status": "success", "user_id": user_id}

    except KeycloakGetError as e:
        return {"status": "fail", "message": e}
        # raise (status_code=400, detail=str(e))


@router.post("/login")
def login(data: LoginRequest):
    # try:
        token = keycloak_openid.token(
            username=data.username,
            password=data.password,
            grant_type="password"
        )
        return token
    # except Exception:
    #     raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/profile")
async def get_profile(
    token: str = Depends(oauth2_scheme),
    session = Depends(get_db)
):
    userinfo = keycloak_openid.userinfo(token)
    user_postgis = await get_user_by_kc_id(session, userinfo["sub"])
    return {"user": userinfo, "user_postgis": user_postgis}