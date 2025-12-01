from fastapi import APIRouter, HTTPException, Query,Depends
from fastapi.responses import JSONResponse
import boto3
import os
from botocore.client import Config
from uuid import uuid4
from config import settings
from core.keycloak import keycloak_openid
from models.database import get_db
from core.analysis import deduct_credits
from core.keycloak import oauth2_scheme
from core.deps  import get_user_by_kc_id
router = APIRouter( tags=["assets"])


def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.AWS_S3_ENDPOINT}",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name=settings.S3_REGION,
    )


@router.get("/generate-link")
async def generate_presigned_put_url(
    object_ext: str | None = Query(None, description="Object/key extension to upload"),
    credentials = Depends(oauth2_scheme),
    session = Depends(get_db)
):
    """
    Generate a S3 presigned URL for uploading files directly.

    Example call:
    /r2/presigned-put?bucket=my-bucket&object_ext=test.png
    """

    try:
        r2 = get_r2_client()
        token = credentials.credentials
        userinfo = keycloak_openid.userinfo(token)
        # auto-generate filename if not provided
        
        object_name = f"{uuid4()}.{object_ext}"
        
        user = await get_user_by_kc_id(session, userinfo['sub'])
        print(user)
        print(type(user))
        presigned_url = r2.generate_presigned_url(
            "put_object",
            Params={
                "Bucket":settings.S3_BUCKET_NAME,
                "Key":  f"{user['id']}/{object_ext}/{object_name}"
            },
            ExpiresIn=3600,  # 1 hour
        )

        return JSONResponse(
            {
                "upload_url": presigned_url,
                "bucket": settings.S3_BUCKET_NAME,
                "key" : f"{user['id']}/{object_ext}/{object_name}",
                "full_path": f"s3://{settings.S3_BUCKET_NAME}/{user['id']}/{object_ext}/{object_name}",
                "expires_in": 3600,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify-upload")
async def verify_upload(key: str, session = Depends(get_db), credentials = Depends(oauth2_scheme)):
    r2 = get_r2_client()

    try:
        res = r2.head_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
        
        return {
            "exists": True,
            "size": res.get("ContentLength"),
            "last_modified": res.get("LastModified").isoformat()
        }
        
        
    except Exception:
        return {"exists": False}
    

