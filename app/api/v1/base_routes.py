from fastapi import APIRouter, UploadFile, File
from app.schemas.responses import InstantQuoteResponse
from app.api.v1.pro_routes import upload_stl, slice_model, quote_model
from app.db.supabase_handler import delete_file

router = APIRouter()

@router.post("/instant-quote/", response_model=InstantQuoteResponse)
async def instant_quote(
    file: UploadFile = File(...)
):
    """Get instant quote details for a sliced model"""
    stl_response = await upload_stl(
        file=file,
        folder_name='temp'
    )

    slice_model_response = await slice_model(
        background_tasks=None,
        user_id='test_user',
        file_path=stl_response.file_path
    )

    quote_model_response = await quote_model(
        job_id=slice_model_response.job_id,
        file_name=slice_model_response.file_name
    )

    # Clean up temporary files
    await delete_file(
        user_id="test_user",
        bucket_name="stl-files",
        file_path=stl_response.file_path
    )
    await delete_file(
        user_id="test_user",
        bucket_name="gcode-files",
        file_path=slice_model_response.file_path
    )

    return InstantQuoteResponse(
        job_id = quote_model_response.job_id,
        file_name=quote_model_response.file_name,
        total_price=quote_model_response.total_price,
        currency=quote_model_response.currency,
        estimated_time=quote_model_response.estimated_time,
        filament_weight=quote_model_response.filament_weight,
        filament_cost=quote_model_response.filament_cost,
        estimated_time_seconds=quote_model_response.estimated_time_seconds,
        status="quoted"
    )