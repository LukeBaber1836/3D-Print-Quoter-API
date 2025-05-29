from fastapi import APIRouter, UploadFile, File, Query
from app.schemas.responses import InstantQuoteResponse
from app.api.v1.pro_routes import upload_stl
from app.utils.utilities import check_printability, cleanup_files
from app.schemas.responses import PrintabilityResponse


router = APIRouter()

@router.post("/instant-quote/", response_model=InstantQuoteResponse)
async def instant_quote(
    user_id: str = Query(..., description="User ID for the print job"),
    file: UploadFile = File(..., description="STL file to check printability")
):
    """Get instant quote details for a sliced model"""
    upload_response = await upload_stl(
        file=file,
        user_id=user_id,
        local_upload=True,
    )
    
    slice_model_response = await slice_model(
        user_id=user_id,
        use_local=True,
        save_file=False,
        file_path=upload_response.file_path + '/' + upload_response.file_name,
    )

    quote_model_response = await quote_model(
        user_id=user_id,
        gcode_file_path=slice_model_response.gcode_path,
        use_local=True,
    )

    return InstantQuoteResponse(
        user_id = quote_model_response.user_id,
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
    upload_response = await upload_stl(
        file=file,
        user_id=user_id,
        local_upload=True,
    )
    
    file_path = f"{upload_response.file_path}/{upload_response.file_name}"
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