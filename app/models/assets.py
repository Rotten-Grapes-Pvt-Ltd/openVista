import uuid
from sqlalchemy import Column, String, Float, ARRAY,ForeignKey,Integer
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from models.database import Base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
class RasterAssets(Base):
    __tablename__ = "raster_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    bbox = Column(ARRAY(Float))
    footprint = Column(Geometry("POLYGON"))
    s3_link = Column(String)


class VectorAssets(Base):
    __tablename__ = "vector_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    bbox = Column(ARRAY(Float))
    footprint = Column(Geometry("POLYGON"))
    table_name = Column(String)


class ImageAssets(Base):
    __tablename__ = "image_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    location = Column(Geometry("POINT"))
    s3_link = Column(String)
    
jsonb_type = MutableDict.as_mutable(JSONB())

class Records(Base):
    __tablename__ = "records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    tags = Column(ARRAY(String))
    bbox = Column(ARRAY(Float))
    keywords = Column(ARRAY(String))
    temporal_start = Column(String)
    temporal_end = Column(String)
    user_id =Column(Integer, ForeignKey("users.id"), nullable=True)
    extra_props = Column(jsonb_type, nullable=True, default=dict)
    
    user = relationship("User", back_populates="records")