from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse

import shutil
from pathlib import Path

from app.utils.utilities import convert_path_to_upload_file, cleanup_files, cleanup_after_download
from app.schemas.responses import STLResponse ,SliceResponse, QuoteResponse
from app.constants import LOCAL_DIR, BUCKET_STL_FILES, BUCKET_GCODE_FILES
from app.services.prusa_slicer import PrusaSlicer
from app.db.supabase_handler import upload_file, download_file

router = APIRouter()

@router.post(
    "/stl/", 
    response_model=STLResponse,
    description="Upload an STL file to the database"
    )
async def upload_stl(
        user_id: str = Form(...),
        file: UploadFile = File(...),
        folder_name: str = Form(None),
        local_upload: bool = False
    ):
    """Upload an STL file"""
    if not file.filename.lower().endswith('.stl'):
        raise HTTPException(status_code=400, detail="File must be an STL")

    if local_upload:
        job_output_dir = Path(LOCAL_DIR / user_id)
        job_output_dir.mkdir(parents=True, exist_ok=True)

        file_path = LOCAL_DIR / user_id / file.filename

        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return STLResponse(
            status="success",
            user_id=user_id,
            file_name=file.filename,
            file_path=str(job_output_dir)
        )

    else:
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

@router.post(
    "/stl/slice/",
    response_model=SliceResponse,
    description="Slice the uploaded STL file and generate the G-code"
    )
async def slice_model(
    user_id: str = Query(..., description="User ID for the print job"),
    file_path: str = Query(..., description="Path to the STL file (this can be found in the upload response)"),
    config_path: str = Query(None, description="Path to the slicing configuration file (still in development...)"),
):
    # Generate output file path
    file_path_parts = file_path.split('/')
    output_name = file_path_parts[-1].rsplit('.', 1)[0] + '.gcode'
    output_path = file_path.rsplit('.', 1)[0] + '.gcode'

    # Get file from supabase and write to local
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
        stl_file_path=job_output_dir / file_path_parts[-1],
        output_gcode_path=job_output_dir / output_name
    )
    
    file = await convert_path_to_upload_file(
        file_path=job_output_dir / output_name
    )

    trimmed_folder_path = '/'.join(output_path.split('/')[2:][:-1])

    # Upload the sliced G-code file to Supabase
    upload_response = await upload_file(
        user_id=user_id,
        overwrite=True,
        folder_name=trimmed_folder_path,
        bucket_name=BUCKET_GCODE_FILES,
        file=file
    )
    
    if upload_response['status'] != 'successful':
        raise HTTPException(status_code=500, detail="Failed to upload G-code file")
    
    #Remove local stl and gcode file after upload for cleanup
    cleanup_files(user_id=user_id)
            
    if not success:
        raise HTTPException(status_code=500, detail="Slicing failed")
    
    return SliceResponse(
        status="success",
        user_id=user_id,
        file_name=output_name,
        gcode_path=output_path
    )

@router.post(
    "/quote/", 
    response_model=QuoteResponse,
    description="Calculate the cost of printing a sliced model"
    )
async def quote_model(
    user_id: str = Query(..., description="User ID for the print job"),
    gcode_path: str = Query(..., description="Path to the G-code file (this can be found in the slice response)"),
):  
    # Check if the sliced file exists
    gcode_path = LOCAL_DIR / user_id / gcode_path.split('/')[-1]

    # Download the G-code file from Supabase
    download_response = download_file(
        bucket_name=BUCKET_GCODE_FILES,
        file_path=gcode_path
    )
    
    if download_response['status'] != 200:
        raise HTTPException(status_code=404, detail="Failed to download G-code file")
    
    # Write the downloaded file to local storage
    job_output_dir = LOCAL_DIR / user_id
    job_output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(job_output_dir / gcode_path.split('/')[-1], 'wb') as f:
        f.write(download_response['data'])

    slicer = PrusaSlicer(
        stl_file_path= '' # Not used in this context
    )
    
    # Get print details
    details = slicer.quote_price_basic(
        gcode_file_path=gcode_path
    )

    # Clean up local files
    cleanup_files(user_id=user_id)
    
    return QuoteResponse(
        user_id=user_id,
        gcode_path=gcode_path,
        total_price=details['total_price'],
        currency=details['currency'],
        estimated_time=details['estimated_time'],
        filament_weight=details['filament_weight'],
        filament_cost=details['filament_cost'],
        estimated_time_seconds=details['estimated_time_seconds'],
        status="quoted"
    )

@router.get(
    "/gcode/",
    description="Download the generated G-code file"
    )
async def download_gcode(
        background_tasks: BackgroundTasks,
        user_id: str = Query(..., description="User ID for the print job"),
        gcode_path: str = Query(..., description="Path to the G-code file (this can be found in the slice response)"),
    ):
    download_response = download_file(
        bucket_name=BUCKET_GCODE_FILES,
        file_path=gcode_path
    )

    if download_response['status'] != 200:
        raise HTTPException(status_code=404, detail="Failed to download G-code file")
        
    # Write the downloaded file to local storage
    gcode_filename = gcode_path.split('/')[-1]
    job_output_dir = LOCAL_DIR / user_id
    job_output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(job_output_dir / gcode_path.split('/')[-1], 'wb') as f:
        f.write(download_response['data'])
    
    # Add cleanup task to run after response is sent by running it in the background
    background_tasks.add_task(cleanup_after_download, user_id=user_id)

    # Construct the file response before cleaning
    return FileResponse(
        path=job_output_dir / gcode_filename,
        filename=gcode_filename,
        media_type="application/octet-stream"
    )
