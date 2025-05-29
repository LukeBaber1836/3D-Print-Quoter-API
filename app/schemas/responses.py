from typing import Optional
from pydantic import BaseModel, Field

# -------------------------- RESPONSE SCHEMAS --------------------------
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

class PrintabilityResponse(BaseModel):
    user_id : str
    fits_printer: bool
    model_dimensions : dict
    printer_dimensions : dict

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# -------------------------- INPUT SCHEMAS --------------------------
class PrinterConfig(BaseModel):
    """Printer configuration settings for slicing"""
    # Printer bed dimensions
    bed_size_x: int = Field(default=210.0, description="X dimension of the print bed in mm")
    bed_size_y: int = Field(default=210.0, description="Y dimension of the print bed in mm")
    bed_size_z: int = Field(default=250.0, description="Z dimension of the print bed in mm")
    
    # Speed settings
    print_speed: int = Field(default=100, description="Default print speed in mm/s")
    first_layer_speed: int = Field(default=50, description="First layer speed in mm/s")
    
    # Default printer settings
    nozzle_diameter: float = Field(default=0.4, description="Nozzle diameter in mm")
    layer_height: float = Field(default=0.2, description="Layer height in mm")
    perimeters: int = Field(default=3, description="Number of perimeters to print")
    top_solid_layers: int = Field(default=3, description="Number of top layers")
    bottom_solid_layers: int = Field(default=3, description="Number of bottom layers")
    fill_density: int = Field(default=20, description="Infill density percentage (0-100)", ge=0, le=100)
    support_material: bool = Field(default=False, description="Whether or not to generate the supports")
    
    # Material settings
    filament_type: str = Field(default="PLA", description="Type of filament to print with (PLA, ABS, PETG)")
    temperature: int = Field(default=210, description="Filament temperature in Celsius")
    bed_temperature: int = Field(default=60, description="Bed temperature in Celsius")

class QuoteConfig(BaseModel):
    """Configuration for instant quote"""
    currency: str = Field(default="USD", description="Currency for the quote")
    cost_per_hour: float = Field(default=2.5, description="Cost per hour of printing")
    cost_per_gram: float = Field(default=0.02, description="Cost per gram of filament used")
    base_price: float = Field(default=5.0, description="Base price for the print job")