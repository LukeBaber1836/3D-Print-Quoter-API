from fastapi import APIRouter, UploadFile, File, Query
from app.utils.utilities import check_printability, cleanup_files
from app.schemas.responses import (
    InstantQuoteResponse,
    PrintabilityResponse, 
    PrinterConfig, 
    QuoteConfig
)
from app.services.base_routes_helpers import local_slice_model, local_quote_model, local_upload_stl

router = APIRouter()

@router.post("/instant-quote/", response_model=InstantQuoteResponse)
async def instant_quote(
    user_id: str = Query(..., description="User ID for the print job"),
    printer_config: PrinterConfig = PrinterConfig(),
    quote_config: QuoteConfig = QuoteConfig(),
    file: UploadFile = File(..., description="STL file for the instant quote")
):
    """Get instant quote details for a sliced model"""
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
        gcode_path=quote_model_response.gcode_path,
        total_price=quote_model_response.total_price,
        currency=quote_model_response.currency,
        estimated_time=quote_model_response.estimated_time,
        estimated_time_seconds=quote_model_response.estimated_time_seconds,
        filament_weight=quote_model_response.filament_weight,
        filament_cost=quote_model_response.filament_cost,
        status="quoted"
    )

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