import uvicorn
from fastapi import FastAPI
from app.api.v1.routes import router as v1_router

app = FastAPI(
    title="Cloud Slicer API",
    description="API for slicing 3D models"
)

app.include_router(v1_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "3D Printing Slicer API"}

if __name__ == "__main__":
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)