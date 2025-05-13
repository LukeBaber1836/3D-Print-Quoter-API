from fastapi import APIRouter, UploadFile, File
from app.schemas.responses import InstantQuoteResponse
from app.api.v1.pro_routes import upload_stl, slice_model, quote_model
from app.db.supabase_handler import delete_file

router = APIRouter()

@router.post("/instant-quote/", response_model=InstantQuoteResponse)
async def instant_quote(
    user_id: str,
    file: UploadFile = File(...)
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