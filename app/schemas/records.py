from pydantic import BaseModel
import uuid

class AddRecord(BaseModel):
    title : str
    description : str | None = None
    tags : list[str] = []
    bbox : list[float] = []
    keywords : list[str] = []
    temporal_start : str | None = None
    temporal_end : str | None = None
    extra_props : dict | None = None
    geometry : dict | None = None
    identifier : str | None = None
    
    