from fastapi import APIRouter, UploadFile, File, Query
from app.utils.utilities import (
    check_printability, 
    cleanup_files,
    convert_path_to_upload_file
)
from app.schemas.responses import (
    ProfileConfigRepsonse,
    InstantQuoteResponse,
    PrintabilityResponse,
    ProfileConfig,
)
from app.services.base_routes_helpers import (
    local_slice_model, 
    local_quote_model, 
    local_upload_stl, 
    create_quote_config,
    get_printer_config,
    get_quote_config
)
from app.db.supabase_handler import upload_file
from app.services.pro_routes_helpers import create_ini_config
from app.constants import BUCKET_FILES

router = APIRouter()

@router.post("/printability/")
async def check_model_printability(
    user_id: str = Query(..., description="User ID for the print job"),
    x_dimension: float = Query(210.0, description="Printer X dimension in mm"),
    y_dimension: float = Query(210.0, description="Printer Y dimension in mm"),
    z_dimension: float = Query(250.0, description="Printer Z dimension in mm"),
    file: UploadFile = File(..., description="STL file to check printability"),
):
    """Check if an STL model fits on the print bed.  Dimensions are in millimeters (mm)"""
    # TODO: Find way to avoid local upload, handle the file directly from the UploadFile
    upload_response = await local_upload_stl(
        file=file,
        user_id=user_id,
    )
    
    file_path = f"{upload_response.stl_file_path}/{upload_response.file_name}"
    printability_result = check_printability(
        stl_file_path=file_path,
        printer_dimensions=(x_dimension, y_dimension, z_dimension),
    )

    cleanup_files(user_id)
    
    return PrintabilityResponse(
        user_id=user_id,
        fits_printer=bool(printability_result["printable"]),
        model_dimensions=printability_result["model_dimensions"],
        printer_dimensions=printability_result["printer_dimensions"]
    )

@router.post("/quote-profile/", response_model=ProfileConfigRepsonse)
async def create_quote_profile(
    user_id: str = Query(..., description="User ID for the print job"),
    profile_config: ProfileConfig = ProfileConfig(),
):
    """Creates a printer profile and uploads the configuration files to storage"""
    profile_name = profile_config.profile_name
    printer_config = profile_config.printer_config
    quote_config = profile_config.quote_config


    # Create .ini from profile_config
    printer_config_response = create_ini_config(
        user_id=user_id,
        stl_file_path=f"{user_id}/profiles/{profile_name}",
        printer_config=printer_config,
    )

    # Create a json file with the quote configuration
    quote_config_response = create_quote_config(
        user_id=user_id,
        quote_config_file=f"{user_id}/profiles/{profile_name}",
        quote_config=quote_config
    )

    printer_config_file = await convert_path_to_upload_file(
        file_path=printer_config_response['output_dir'],
    )

    quote_config_file = await convert_path_to_upload_file(
        file_path=quote_config_response['output_dir'],
    )

    # Uload the .ini and quote json files to the storage bucket under the user_id/profiles/profile_name directory
    await upload_file(
        user_id=user_id,
        folder_name=f"profiles/{profile_name}",
        bucket_name=BUCKET_FILES,
        file=printer_config_file,
        overwrite=True
    )
    await upload_file(
        user_id=user_id,
        folder_name=f"profiles/{profile_name}",
        bucket_name=BUCKET_FILES,
        file=quote_config_file,
        overwrite=True
    )

    # Cleanup local files after upload
    cleanup_files(user_id)

    return ProfileConfigRepsonse(
        user_id=user_id,
        status=f"success",
        profile_name=profile_name,
        printer_config=profile_config.printer_config,
        quote_config=profile_config.quote_config,
    )

@router.post("/instant-quote/", response_model=InstantQuoteResponse)
async def instant_quote(
    user_id: str = Query(..., description="User ID for the print job"),
    profile_name: str = Query(..., description="Name of the printer config profile"),
    file: UploadFile = File(..., description="STL file for the instant quote")
):
    """Get instant quote details for a sliced model"""
    # Retrieve the printer and quote configurations
    printer_config = get_printer_config(
        user_id=user_id, 
        profile_name=profile_name
    )
    quote_config = get_quote_config(
        user_id=user_id, 
        profile_name=profile_name
    )

    upload_response = await local_upload_stl(
        user_id=user_id,
        file=file
    )
    
    slice_model_response = await local_slice_model(
        user_id=user_id,
        cleanup=False,
        stl_file_path=upload_response.stl_file_path + '/' + upload_response.file_name,
        printer_config=printer_config
    )
    
    quote_model_response = await local_quote_model(
        user_id=user_id,
        gcode_path=slice_model_response.gcode_path,
        quote_config=quote_config,
    )

    return InstantQuoteResponse(
        user_id = user_id,
        total_price=quote_model_response.total_price,
        currency=quote_model_response.currency,
        estimated_time=quote_model_response.estimated_time,
        estimated_time_seconds=quote_model_response.estimated_time_seconds,
        filament_weight=quote_model_response.filament_weight,
        filament_cost=quote_model_response.filament_cost,
        status="quoted"
    )