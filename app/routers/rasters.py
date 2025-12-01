from fastapi import APIRouter, HTTPException, Query,Depends
from fastapi.responses import JSONResponse
import boto3
import os
from botocore.client import Config
from uuid import uuid4
from config import settings
from core.keycloak import keycloak_openid
from models.database import get_db
from core.deps import get_user_by_kc_id
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import urllib.parse
from fastapi import Request
from schemas.records import AddRecord
from models.assets import Records
from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from core.keycloak import oauth2_scheme
from core.storage import get_object_size
from core.analysis import deduct_credits
router = APIRouter( tags=["rasters"])


def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.AWS_S3_ENDPOINT}",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name=settings.S3_REGION,
    )


@router.get("/info")
async def get_info(
    request: Request,
    file_path: str | None = Query(None, description="Path of the raster file"),
    stats : bool = Query(False, description="Get raster statistics"),
    credentials = Depends(oauth2_scheme),
    session = Depends(get_db),
    
):
    """
    Get info of raster using Titiler endpoint

    Example call:
    /cog/info?url=s3://<bucket>/<user>/<file>
    """

    try:
        # httpx async code
        token = credentials.credentials
        userinfo = keycloak_openid.userinfo(token)
        base = str(request.base_url).rstrip("/")
        encoded = urllib.parse.quote(file_path, safe="")
        
        result = {}
        async with httpx.AsyncClient() as client:
            r = await client.get(f'{base}/cog/info.geojson?url={encoded}')
            result['info'] = r.json()
        if stats:
            async with httpx.AsyncClient() as client:
                r = await client.get(f'{base}/cog/statistics?url={encoded}')
                result['stats'] = r.json()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add_record")
async def add_record(records:AddRecord, credentials = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)):
    
    """
    Add new Record based on data 
    """
    
    # try:
    token = credentials.credentials
    userinfo = keycloak_openid.userinfo(token)
    kc_user_id = userinfo['sub']
    
    
    user = await get_user_by_kc_id(session, kc_user_id)
    
    
    
    # Convert GeoJSON to WKT if geometry is provided
    geometry_wkt = None
    if records.geometry:
        
        geometry_wkt = from_shape(shape(records.geometry))
    
    asset_size = get_object_size(records.identifier)
    records.extra_props['asset_size'] = asset_size
    new_record = Records(
        title=records.title,
        description=records.description,
        tags=records.tags,
        bbox=records.bbox,
        keywords=records.keywords,
        temporal_start=records.temporal_start,
        temporal_end=records.temporal_end,
        user_id=user.id,
        extra_props=records.extra_props,
        record_type='raster',
        geometry=geometry_wkt,
        identifier=records.identifier
    )
    session.add(new_record)
    await session.commit()
    await deduct_credits(session, user.id, storage=asset_size, params={'identifier': records.identifier,'record_type': 'raster'})
    
    return {"message": str(new_record.id)}
    # except Exception as e:
    #     await session.rollback()
    #     raise HTTPException(status_code=500, detail=str(e))