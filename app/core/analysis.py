import requests
from datetime import datetime

from config import settings
from models.credits import Credits,Transactions
# Function to deduct credits from user's account
from sqlalchemy import select
from fastapi import HTTPException
AIRFLOW_API_BASE_URL = settings.AIRFLOW_API_BASE_URL
AIRFLOW_USER_PASSWORD = settings.AIRFLOW_USER_PASSWORD
AIRFLOW_USER_USERNAME = settings.AIRFLOW_USER_USERNAME


def trigger_dag(dag_id: str, conf: dict):
    r = requests.post(
        f"{AIRFLOW_API_BASE_URL}/api/v1/dags/{dag_id}/dagRuns",
        auth=(AIRFLOW_USER_USERNAME, AIRFLOW_USER_PASSWORD),
        json={
            "conf": conf,
            "dag_run_id": f"run_{datetime.utcnow().timestamp()}"
        }
    )
    r.raise_for_status()
    return r.json()




async def deduct_credits(session, user_id: int, credits_to_deduct: float | None =None, algorithm: str | None =None, params: dict| None=None, storage: float | None =None):
    
    # Find user based on user_id in Credits and then reduce the `available_credits` by credits_to_deduct value
    result = await session.execute(select(Credits).where(Credits.user_id == user_id))
    user_credits = result.scalar_one_or_none()
    if credits_to_deduct : 
        if user_credits and user_credits.available_credits >= credits_to_deduct:
            user_credits.available_credits -= credits_to_deduct
            
            # Add entry to transaction 
            transaction = Transactions(
                user_id=user_id,
                credits=credits_to_deduct,
                algorithm=algorithm,  # You may need to get actual algorithm_id
                params=params,
                storage=None
            )
            session.add(transaction)
            await session.commit()
            return True
        else:
            return HTTPException(status_code=400, detail="Insufficient credits")
    else : 
        if user_credits and user_credits.storage_available >= storage:
            user_credits.storage_available -= storage
            
            # Add entry to transaction 
            transaction = Transactions(
                user_id=user_id,
                credits=None,
                algorithm=None, 
                params=params,
                storage=storage
            )
            session.add(transaction)
            await session.commit()
            return True
        else:
            return HTTPException(status_code=400, detail="Insufficient storage")