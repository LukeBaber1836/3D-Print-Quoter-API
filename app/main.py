import uvicorn
from fastapi import FastAPI
from app.api.v1.base_routes import router as base_router
from app.api.v1.pro_routes import router as pro_router
from app.api.v1.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Cloud Slicer API",
    description="API for slicing 3D models"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://cloud-slicer-app.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(base_router, prefix="/v1", tags=["Basic Level"])
app.include_router(pro_router, prefix="/v1", tags=["Advanced Level"])
app.include_router(auth_router, prefix="/v1", tags=["Authentication"])

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "3D Printing Slicer API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)