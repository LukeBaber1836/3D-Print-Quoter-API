from typing import Optional
from pydantic import BaseModel

class SliceResponse(BaseModel):
    job_id: str
    file_name: str
    status: str
    gcode_path: Optional[str] = None
    
class QuoteResponse(BaseModel):
    job_id: str
    file_name: str
    total_price: Optional[float] = None
    currency: Optional[str] = None
    estimated_time: Optional[str] = None
    filament_weight: Optional[float] = None
    filament_cost: Optional[float] = None
    estimated_time_seconds: Optional[int] = None
    status: str