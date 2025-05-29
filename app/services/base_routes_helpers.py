from fastapi import HTTPException, Query
import shutil

from app.utils.utilities import convert_path_to_upload_file, cleanup_files
from app.schemas.responses import SliceResponse, QuoteResponse
from app.constants import LOCAL_DIR, BUCKET_GCODE_FILES
from app.services.prusa_slicer import PrusaSlicer
from app.db.supabase_handler import upload_file


async def slice_model(
    user_id: str = Query(..., description="User ID for the print job"),
    file_path: str = Query(..., description="Path to the STL file (this can be found in the upload response)"),
    remove_local: bool = Query(False, description="Remove temporary files after slicing"),
    save_file: bool = True,
    config_path: str = None
):
    """Slice the uploaded STL file"""
    # Generate output file path
    file_path_parts = file_path.split('/')
    output_name = file_path_parts[-1].rsplit('.', 1)[0] + '.gcode'
    output_path = file_path.rsplit('.', 1)[0] + '.gcode'

    # Check if the STL file exists locally
    job_output_dir = LOCAL_DIR / user_id
    if not (job_output_dir / file_path_parts[-1]).exists():
        raise HTTPException(status_code=404, detail="STL file not found. Upload the model first or set use_local to False.")

    slicer = PrusaSlicer(
        stl_file_path=file_path
    )
    
    # Run slicing operation
    success = slicer.slice(
        stl_file_path=job_output_dir / file_path_parts[-1],
        output_gcode_path=job_output_dir / output_name
    )
    
    if save_file:
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

async def quote_model(
    user_id: str = Query(..., description="User ID for the print job"),
    gcode_path: str = Query(..., description="Path to the G-code file (this can be found in the slice response)")
):  
    """Get print details for a sliced model"""
    # Check if the sliced file exists
    gcode_path = LOCAL_DIR / user_id / gcode_path.split('/')[-1]

    if not gcode_path.exists():
        raise HTTPException(status_code=404, detail="G-code file not found. Slice the model first.")

    # Get print details
    details = PrusaSlicer.quote_price_basic(
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