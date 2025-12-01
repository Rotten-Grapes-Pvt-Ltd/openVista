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
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Convert SQLAlchemy model to dict automatically
    user_dict = {c.name: getattr(user, c.name) for c in user.__table__.columns}
    # Convert UUID to string for JSON serialization
    if 'kc_user_id' in user_dict:
        user_dict['kc_user_id'] = str(user_dict['kc_user_id'])
    
    return user_dict
