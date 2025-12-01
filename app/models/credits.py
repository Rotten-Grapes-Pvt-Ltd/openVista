from sqlalchemy import Column, String, Integer, UUID, ForeignKey, Float,Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

jsonb_type = MutableDict.as_mutable(JSONB())
from models.database import Base




class Credits(Base):
    __tablename__ = "credits"

    id = Column(Integer, primary_key=True)       # internal PK
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    credits_allocated = Column(Float, nullable=False)
    available_credits = Column(Float, nullable=False)
    storage_allocated = Column(Float, nullable=False, default=2000)
    storage_available = Column(Float, nullable=False, default=2000)
    created_at = Column(DateTime, default=datetime.utcnow)

    

class Transactions(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)       # internal PK
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    credits = Column(Float, nullable=True)
    algorithm = Column(String, nullable=True)
    storage = Column(Float, nullable=True)
    params = Column(jsonb_type, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    
    
