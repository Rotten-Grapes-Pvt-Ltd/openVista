from fastapi import Header, HTTPException, status

from sqlalchemy.future import select
from models.auth import User
def get_bearer_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    return authorization.split(" ")[1]



async def get_user_by_kc_id(session, kc_user_id):
    result = await session.execute(
        select(User).where(User.kc_user_id == kc_user_id)
    )
    return result.scalars().first()
