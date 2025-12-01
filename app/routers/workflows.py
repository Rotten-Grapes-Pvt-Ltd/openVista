from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from models.database import get_db

from schemas.algorithms import Algorithm, AlgorithmCreate, InitiateAlgorithmExecution,AlgorithmUpdate, AspectParams
from core.permissions import roles_within
from core.keycloak import oauth2_scheme
from core.analysis import trigger_dag, deduct_credits
from core.keycloak import get_userinfo_from_keycloak
from core.deps import get_user_by_kc_id
import requests
from config import settings
from models.credits import Credits,Transactions
# Function to deduct credits from user's account
from sqlalchemy import select
AIRFLOW_API_BASE_URL = settings.AIRFLOW_API_BASE_URL
AIRFLOW_USER_PASSWORD = settings.AIRFLOW_USER_PASSWORD
AIRFLOW_USER_USERNAME = settings.AIRFLOW_USER_USERNAME

router = APIRouter( prefix="/workflows", tags=["workflows"])


@router.post("/job_status")
async def get_job_status(
    algorithm: str,
   
    job_id: str,
    session: AsyncSession = Depends(get_db),
    credentials = Depends(oauth2_scheme)
):
    """Get job status based on `dag_id` 
    """
    
    # TODO : add authorisation if the dag_id actually belongs to the same user or no
    r = requests.get(
        f"{AIRFLOW_API_BASE_URL}/api/v1/dags/{algorithm}/dagRuns/{job_id}/taskInstances/analysis/xcomEntries/return_value",
        auth=(AIRFLOW_USER_USERNAME, AIRFLOW_USER_PASSWORD),
       
    )
    r.raise_for_status()
    return r.json()
    
    
    
    