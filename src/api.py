from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import shutil
import tempfile
import os
import uuid
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from prusa_slicer import PrusaSlicer

app = FastAPI(title="3D Printing API", description="API for slicing 3D models")

# Create directories for file storage
UPLOAD_DIR = Path("/app/uploads")
OUTPUT_DIR = Path("/app/outputs")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

class SliceResponse(BaseModel):
    job_id: str
    file_name: str
    status: str
    gcode_path: Optional[str] = None
    
class QuoteResponse(BaseModel):
    job_id: str
    file_name: str
    estimated_time: Optional[str] = None
    filament_length: Optional[float] = None
    filament_weight: Optional[float] = None
    price: Optional[float] = None
    status: str

@app.post("/upload-stl/", response_model=SliceResponse)
async def upload_stl(file: UploadFile = File(...)):
    """Upload an STL file"""
    if not file.filename.lower().endswith('.stl'):
        raise HTTPException(status_code=400, detail="File must be an STL")
    
    job_id = str(uuid.uuid4())
    job_output_dir = UPLOAD_DIR / job_id
    job_output_dir.mkdir(parents=True, exist_ok=True)

    file_path = UPLOAD_DIR / job_id / file.filename
    
    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return SliceResponse(
        job_id=job_id,
        file_name=file.filename,
        status="uploaded"
    )

@app.post("/slice/", response_model=SliceResponse)
async def slice_model(
    background_tasks: BackgroundTasks,
    job_id: str = Form(...),
    file_name: str = Form(...),
    config_path: Optional[str] = Form(None),
    printer_profile: Optional[str] = Form(None)
):
    """Slice an uploaded STL file"""
    # Reconstruct the file path
    file_path = UPLOAD_DIR / job_id / file_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Create output directory for this job
    job_output_dir = OUTPUT_DIR / job_id
    job_output_dir.mkdir(exist_ok=True)
    
    # Generate output file path
    output_name = file_name.rsplit('.', 1)[0] + '.gcode'
    output_path = job_output_dir / output_name

    slicer = PrusaSlicer(
        stl_file_path=job_output_dir / output_name
    )
    
    # Run slicing operation
    success = slicer.slice(
        stl_file_path=str(file_path),
        output_gcode_path=str(job_output_dir),
        config_path=config_path,
        printer_profile=printer_profile
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Slicing failed")
    
    return SliceResponse(
        job_id=job_id,
        file_name=file_name,
        status="sliced",
        gcode_path=str(job_output_dir / output_name)
    )

@app.post("/quote/", response_model=QuoteResponse)
async def quote_model(
    job_id: str = Form(...),
    file_name: str = Form(...)
):
    """Get print details for a sliced model"""
    # Check if the sliced file exists
    gcode_name = file_name.rsplit('.', 1)[0] + '.gcode'
    gcode_path = OUTPUT_DIR / job_id / gcode_name
    
    if not gcode_path.exists():
        raise HTTPException(status_code=404, detail="G-code file not found. Slice the model first.")
    
    slicer = PrusaSlicer(
        stl_file_path=OUTPUT_DIR / job_id / file_name
    )
    
    # Get print details
    details = slicer.quote_price_basic(
        gcode_file_path=gcode_path
    )
    
    return QuoteResponse(
        job_id=job_id,
        file_name=file_name,
        estimated_time=details['estimated_time'],
        filament_length=details['filament_length'],
        filament_weight=details['filament_weight'],
        status="quoted"
    )

@app.get("/download/{job_id}/{filename}")
async def download_gcode(job_id: str, filename: str):
    """Download a generated G-code file"""
    file_path = OUTPUT_DIR / job_id / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

@app.get("/")
async def root():
    return {"message": "3D Printing Slicer API"}