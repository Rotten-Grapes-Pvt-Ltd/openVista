import os

from fastapi import FastAPI
from rasterio.session import AWSSession
from rio_tiler.io import Reader, STACReader
from titiler.application.settings import ApiSettings
from titiler.core.factory import MultiBaseTilerFactory, TilerFactory

from titiler.extensions import (
    cogValidateExtension,
    cogViewerExtension,
    stacExtension,
    stacRenderExtension,
    stacViewerExtension,
)

# Assert that AWS_NO_SIGN_REQUEST is not set
assert os.getenv("AWS_NO_SIGN_REQUEST") is None, (
    "test without the AWS_NO_SIGN_REQUEST environment variable"
)

app = FastAPI()


api_settings = ApiSettings()


def environment_dependency():
    aws_session = AWSSession(
        aws_unsigned=True,
    )
    return {"session": aws_session}


class STACReaderWithSession(STACReader):
    """Custom STAC Reader with session support."""

    def _get_asset_info(self, asset: str):
        """Get asset info and inject environment dependency."""
        asset_info = super()._get_asset_info(asset)
        asset_info.setdefault("env", {}).update(environment_dependency())
        return asset_info


# Create a TilerFactory for Cloud-Optimized GeoTIFFs
cog = TilerFactory(
    reader=Reader,
    router_prefix="/cog",
    add_ogc_maps=True,
    extensions=[
        cogValidateExtension(),
        cogViewerExtension(),
        stacExtension(),
    ],
    enable_telemetry=False,
    environment_dependency=environment_dependency,
)

# Register all the COG endpoints automatically
app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])

stac = MultiBaseTilerFactory(
    reader=STACReaderWithSession,
    router_prefix="/stac",
    add_ogc_maps=True,
    extensions=[
        stacViewerExtension(),
        stacRenderExtension(),
    ],
    enable_telemetry=False,
    environment_dependency=environment_dependency,
)

app.include_router(
    stac.router,
    prefix="/stac",
    tags=["SpatioTemporal Asset Catalog"],
)


