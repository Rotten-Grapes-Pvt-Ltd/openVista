from fastapi import FastAPI
from contextlib import asynccontextmanager
from routers import auth as auth_router # import router # add router
from routers import assets as assets_router # import router # add router
from routers import rasters as rasters_router # import router # add router
from routers import raster_workflows as raster_workflows_router # import router # add router
from routers import workflows as workflows_router # import router # add router
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.database import engine, Base
from config import settings

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import TilerFactory
from titiler.core.middleware import LoggerMiddleware, TotalTimeMiddleware

from titiler.extensions import cogValidateExtension
import boto3
import os
os.environ["CPL_VSIL_CURL_USE_S3"] = "YES"
os.environ["AWS_VIRTUAL_HOSTING"] = "FALSE"
os.environ["AWS_HTTPS"] = "NO"
os.environ["AWS_NO_SIGN_REQUEST"] = "NO"
os.environ["AWS_SECRET_ACCESS_KEY"] = settings.AWS_SECRET_ACCESS_KEY
os.environ['AWS_ACCESS_KEY_ID'] = settings.AWS_ACCESS_KEY_ID
os.environ['AWS_S3_ENDPOINT'] = settings.AWS_S3_ENDPOINT
from rasterio.session import AWSSession
cog = TilerFactory(
    environment_dependency=lambda: {
        "session": AWSSession(
            boto3.Session()
        )
    },
    extensions=[
        cogValidateExtension()  # the cogeoExtension will add a rio-cogeo /validate endpoint
    ]
)
# Bearer token scheme for Swagger UI
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    


app = FastAPI(
    title="OpenVista API",
    description="Backend API",
    lifespan=lifespan,
    version="1.0.0",
)
app.include_router(auth_router.router, prefix="/auth", tags=["auth"]) # include router
app.include_router(assets_router.router, prefix="/assets", tags=["assets"]) # include router
app.include_router(rasters_router.router, prefix="/rasters", tags=["rasters"]) # include router
app.include_router(workflows_router.router, prefix="/workflows", tags=["workflows"]) # include router
app.include_router(raster_workflows_router.router, prefix="/rasters", tags=["raster-workflows"]) # include router
app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"], prefix="/cog")

@app.get("/")
def read_root():
    return {"Hello": "World"}
