import json
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from pydantic import TypeAdapter
from app.utils.utilities import convert_path_to_upload_file, cleanup_files
from app.schemas.responses import SliceResponse, QuoteResponse, STLResponse, PrinterConfig, QuoteConfig
from app.services.prusa_slicer import PrusaSlicer
from app.services.pro_routes_helpers import create_ini_config
from app.db.supabase_handler import download_file
from app.constants import LOCAL_DIR, BUCKET_FILES


async def local_upload_stl(
        user_id: str,
        file: UploadFile,
    ):
    """Upload an STL file"""
    if not file.filename.lower().endswith('.stl'):
        raise HTTPException(status_code=400, detail="File must be an STL")

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
        stl_file_path=str(job_output_dir)
    )

async def local_slice_model(
    user_id: str,
    stl_file_path: str,
    printer_config: PrinterConfig,
    cleanup: bool = False,
):
    # Generate output file path
    stl_file_path_parts = stl_file_path.split('/')
    output_name = stl_file_path_parts[-1].rsplit('.', 1)[0] + '.gcode'
    output_path = stl_file_path.rsplit('.', 1)[0] + '.gcode'

    job_output_dir = LOCAL_DIR / user_id
    job_output_dir.mkdir(parents=True, exist_ok=True)

    response = create_ini_config(
        user_id=user_id,
        stl_file_path=stl_file_path,
        printer_config=printer_config
    )

    # TODO: See if we can avoid writing the config file to disk
    slicer = PrusaSlicer(
        stl_file_path=stl_file_path,
        config_path=response['output_dir'],
    )

    # Run slicing operation
    success = slicer.slice(
        output_gcode_path=job_output_dir / output_name
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Slicing failed")
    
    # Convert the local G-code file to an UploadFile object
    file = await convert_path_to_upload_file(
        file_path=job_output_dir / output_name
    )

    trimmed_folder_path = '/'.join(output_path.split('/')[1:][:-1])
    
    #Remove local stl and gcode file after upload for cleanup
    if cleanup:
        cleanup_files(user_id=user_id)

    return SliceResponse(
        status="success",
        user_id=user_id,
        file_name=output_name,
        gcode_path=output_path
    )

async def local_quote_model(
    user_id: str,
    gcode_path: str,
    quote_config: QuoteConfig,
    cleanup: bool = True,
    
):  
    slicer = PrusaSlicer(
        base_price=quote_config.base_price,
        cost_per_hour=quote_config.cost_per_hour,
        cost_per_gram=quote_config.cost_per_gram,
        currency=quote_config.currency,
    )
    
    # Get print details
    details = slicer.quote_price_basic(
        gcode_file_path= LOCAL_DIR / user_id / gcode_path.split('/')[-1]
    )

    # Clean up local files
    if cleanup:
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

def create_quote_config(
    user_id: str,
    quote_config_file: str,
    quote_config: QuoteConfig,
):
    """
    Create a quote_config json file using the provided QuoteConfig object.
    
    Args:
        user_id: User ID for the print job
        quote_config_file: Path to the quote configuration file
        quote_config: QuoteConfig object with configuration details
    
    Returns:
        Path to the created quote configuration file
    """
    file_path_parts = quote_config_file.split('/')
    output_name = file_path_parts[-1].rsplit('.', 1)[0] + '.json'

    job_output_dir = Path(LOCAL_DIR / user_id)
    job_output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(job_output_dir / output_name, 'w') as f:
        json.dump(quote_config.model_dump(), f, indent=4)
    
    return {
        'output_dir': job_output_dir / output_name
    }

def get_printer_config(
    user_id: str,
    profile_name: str,
):
    """
    Get the printer configuration from an INI file.
    
    Args:
        user_id: User ID for the print job
        quote_config_file: Path to the printer configuration file
    
    Returns:
        PrinterConfig dictionary object with the loaded configuration
    """

    file_path = f"{user_id}/profiles/{profile_name}/{profile_name}.ini"

    printer_config = download_file(
        bucket_name=BUCKET_FILES,
        file_path=file_path,
    )

    return PrinterConfig.model_validate(printer_config)

def get_quote_config(
    user_id: str,
    profile_name: str,
):
    """
    Get the quote configuration from a JSON file.
    
    Args:
        user_id: User ID for the print job
        quote_config_file: Path to the quote configuration file
    
    Returns:
        QuoteConfig dictionary object with the loaded configuration
    """

    file_path = f"{user_id}/profiles/{profile_name}/{profile_name}.json"

    quote_config = download_file(
        bucket_name=BUCKET_FILES,
        file_path=file_path,
    )

    return QuoteConfig.model_validate(quote_config) if quote_config else QuoteConfig.model_validate({})