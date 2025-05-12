from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import shutil
import uuid
from typing import Optional
from pathlib import Path
from app.utils.utilities import convert_path_to_upload_file
from app.schemas.responses import STLResponse ,SliceResponse, QuoteResponse, InstantQuoteResponse
from app.constants import LOCAL_DIR, BUCKET_STL_FILES, BUCKET_GCODE_FILES
from app.services.prusa_slicer import PrusaSlicer
from app.db.supabase_handler import upload_file, delete_file, download_file

router = APIRouter()

@router.post("/upload-stl/", response_model=STLResponse)
async def upload_stl(
        file: UploadFile = File(...),
        folder_name: str = Form(None),
    ):
    """Upload an STL file"""
    if not file.filename.lower().endswith('.stl'):
        raise HTTPException(status_code=400, detail="File must be an STL")
    
    user_id = "test_user"  # Replace with actual user ID from authentication context

    response = await upload_file(
        user_id=user_id,
        folder_name=folder_name,
        bucket_name="stl-files",
        file=file
    )

    return STLResponse(
        status=response['status'],
        user_id=user_id,
        file_name=file.filename,
        file_path=response['file_path']
    )

@router.post("/slice/", response_model=SliceResponse)
async def slice_model(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    file_path: str = Form(...),
    remove_local: bool = Form(True),
    save_file: bool = Form(True),
    config_path: Optional[str] = Form(None),
    printer_profile: Optional[str] = Form(None)
):
    """Slice the uploaded STL file"""
    # Generate output file path
    file_path_parts = file_path.split('/')
    output_name = file_path_parts[-1].rsplit('.', 1)[0] + '.gcode'
    output_path = file_path.rsplit('.', 1)[0] + '.gcode'

    # get file from supabase and write to local
    download_file_response = download_file(
        bucket_name=BUCKET_STL_FILES,
        file_path=file_path
    )
    job_output_dir = LOCAL_DIR / user_id
    job_output_dir.mkdir(parents=True, exist_ok=True)

    with open(job_output_dir / file_path_parts[-1], 'wb') as f:
        f.write(download_file_response['data'])

    slicer = PrusaSlicer(
        stl_file_path=file_path
    )
    
    # Run slicing operation
    success = slicer.slice(
        stl_file_path=Path(job_output_dir / file_path_parts[-1]),
        output_gcode_path=job_output_dir / output_name,
        printer_profile=printer_profile
    )
    
    if save_file:
        file = await convert_path_to_upload_file(
            file_path=job_output_dir / file_path_parts[-1]
        )

        # Upload the sliced G-code file to Supabase
        upload_response = await upload_file(
            user_id=user_id,
            overwrite=True,
            folder_name='gcode-files',
            bucket_name=BUCKET_GCODE_FILES,
            file=file
        )
        
        if upload_response['status'] != 'successful':
            raise HTTPException(status_code=500, detail="Failed to upload G-code file")
        
        #Remove local stl and gcode file after upload for cleanup
        if remove_local:
            shutil.rmtree(job_output_dir)
            
    if not success:
        raise HTTPException(status_code=500, detail="Slicing failed")
    
    return SliceResponse(
        status="success",
        user_id=user_id,
        file_name=output_name,
        gcode_path=output_path
    )

@router.post("/quote/", response_model=QuoteResponse)
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
        total_price=details['total_price'],
        currency=details['currency'],
        estimated_time=details['estimated_time'],
        filament_weight=details['filament_weight'],
        filament_cost=details['filament_cost'],
        estimated_time_seconds=details['estimated_time_seconds'],
        status="quoted"
    )

@router.get("/download/{job_id}/{filename}")
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
