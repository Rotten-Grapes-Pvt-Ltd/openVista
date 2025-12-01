import boto3
from config import settings
from botocore.client import Config

from fastapi import Request
import httpx
import urllib.parse

def get_object_size( key: str) -> int:
    
    s3 = boto3.client(
    "s3",
    endpoint_url=f"{settings.AWS_S3_PROTOCOL}://{settings.AWS_S3_ENDPOINT}",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
     config=Config(signature_version="s3v4"),
        region_name=settings.S3_REGION,
)
    info = s3.head_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
    
    return info["ContentLength"] /1024/1024


async def get_object_pixels(request: Request,file_path:str) -> int :
    base = str(request.base_url).rstrip("/")
    encoded = urllib.parse.quote(file_path, safe="")
        
    async with httpx.AsyncClient() as client:
        r = await client.get(f'{base}/cog/statistics?url={encoded}')
        print(r.json())
        return r.json()['b1']['count']