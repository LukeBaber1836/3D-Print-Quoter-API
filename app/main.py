import uvicorn
from fastapi import FastAPI
from app.api.v1.base_routes import router as base_router
from app.api.v1.pro_routes import router as pro_router

app = FastAPI(
    title="Cloud Slicer API",
    description="API for slicing 3D models"
)

app.include_router(base_router, prefix="/api/v1", tags=["Base Level Routes"])
app.include_router(pro_router, prefix="/api/v1", tags=["Pro Level Routes"])

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "3D Printing Slicer API"}

if __name__ == "__main__":
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)