from sqlalchemy import Column, String, Integer, UUID, ForeignKey, Float,Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from models.database import Base


class UserType(str, enum.Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"


class UserRole(str, enum.Enum):
    OWNER = "owner"      # Company creator
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    GUEST = "guest"


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)       # internal PK
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship: company -> users
    users = relationship("User", back_populates="company")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)       # internal PK
    kc_user_id = Column(UUID(as_uuid=True), unique=True, nullable=False)  
    email = Column(String, nullable=False)
    type = Column(Enum(UserType), nullable=False, default=UserType.INDIVIDUAL)

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    role = Column(Enum(UserRole), nullable=True)   # Only when part of company

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="users")
    records = relationship("Records", back_populates="user")
