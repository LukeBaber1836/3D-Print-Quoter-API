from typing import Optional
from pydantic import BaseModel

class STLResponse(BaseModel):
    status: str
    user_id: str
    file_name: str
    file_path: str

class SliceResponse(BaseModel):
    status: str
    user_id: str
    file_name: str
    gcode_path: Optional[str] = None
    
class QuoteResponse(BaseModel):
    user_id: str
    gcode_path: str
    total_price: Optional[float] = None
    currency: Optional[str] = None
    estimated_time: Optional[str] = None
    filament_weight: Optional[float] = None
    filament_cost: Optional[float] = None
    estimated_time_seconds: Optional[int] = None
    status: str

class InstantQuoteResponse(BaseModel):
    user_id : str
    gcode_path: str
    total_price: Optional[float] = None
    currency: Optional[str] = None
    estimated_time: Optional[str] = None
    estimated_time_seconds: Optional[int] = None
    filament_weight: Optional[float] = None
    filament_cost: Optional[float] = None
    status: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str