from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class AlgorithmBase(BaseModel):
    name: str
    description: str
    dag_id: str
    credits: float

class AlgorithmCreate(AlgorithmBase):
    pass

class AlgorithmUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dag_id: Optional[str] = None
    credits: Optional[float] = None

class Algorithm(AlgorithmBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
        
class InitiateAlgorithmExecution(BaseModel):
    algorithm: str
    job_id : str
    status: str

# Algorithm-specific parameter schemas
class HillshadeParams(BaseModel):
    input_s3_url: str
    band: Optional[int] = 1
    azimuth: Optional[float] = 315.0
    altitude: Optional[float] = 45.0
    z_factor: Optional[float] = 1.0
    scale: Optional[float] = 1.0

class SlopeParams(BaseModel):
    input_s3_url: str
    band: Optional[int] = 1
    scale: Optional[float] = 1.0
    compute_edges: Optional[bool] = False

class AspectParams(BaseModel):
    input_s3_url: str
    band: Optional[int] = 1
    trigonometric: Optional[bool] = False
    zero_for_flat: Optional[bool] = False

class RoughnessParams(BaseModel):
    input_s3_url: str
    band: Optional[int] = 1
    compute_edges: Optional[bool] = False

class TPIParams(BaseModel):
    input_s3_url: str
    band: Optional[int] = 1
    compute_edges: Optional[bool] = False

class COGValidationParams(BaseModel):
    input_s3_url: str

# Generic algorithm execution schema
class AlgorithmExecution(BaseModel):
    algorithm_id: int
    parameters: Dict[str, Any]

class AlgorithmExecutionResponse(BaseModel):
    job_id: str
    status: str
    algorithm_name: str
    estimated_credits: float
    output_url: Optional[str] = None

