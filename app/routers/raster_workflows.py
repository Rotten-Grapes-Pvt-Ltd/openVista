from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from models.assets import Records
from models.database import get_db
from fastapi import Request
from schemas.algorithms import Algorithm, AlgorithmCreate, InitiateAlgorithmExecution,AlgorithmUpdate, AspectParams
from core.permissions import roles_within
from core.keycloak import oauth2_scheme
from core.analysis import trigger_dag, deduct_credits
from core.keycloak import get_userinfo_from_keycloak
from core.deps import get_user_by_kc_id
from core.storage import get_object_pixels
router = APIRouter( prefix="/workflow", tags=["workflows"])


@router.post("/aspect", response_model=InitiateAlgorithmExecution)
async def create_aspect(
    params: AspectParams,
    request:Request,
    session: AsyncSession = Depends(get_db),
    credentials = Depends(oauth2_scheme),
    
):
    """Create a new job id for `aspect` dag"""
    #1 User
    userkeycloak = get_userinfo_from_keycloak(credentials)
    
    user = await get_user_by_kc_id(session, userkeycloak['sub'])
    
    params_dict = params.model_dump()
    #2 Get info about asset
    input_url = params_dict['input_s3_url']
    result = await session.execute(select(Records).where(Records.identifier == input_url))
    if result is None:
        raise HTTPException(status_code=400, detail="Asset not found")
    
    # Get total pixels 
    total_pixels = await get_object_pixels(request,file_path=input_url)
    
    total_credits_to_deduct = total_pixels * 0.0001
    deducted = await deduct_credits(session, user.id, total_credits_to_deduct, 'aspect',params_dict)
    if deducted:
    # 2) Trigger Airflow DAG
        dag_result = trigger_dag("aspect",params_dict)


        return {
            "status": "queued",
            "algorithm" : "aspect",
            "job_id": dag_result["dag_run_id"]
        }
    else : 
        raise HTTPException(status_code=400, detail="Insufficient credits")