from fastapi import FastAPI
from fastapi.routing import APIRouter
from mangum import Mangum
from fastq_manager_api_tools.api.v1.routers import fastq

app = FastAPI(title="Fastq Api", summary="Access Fastq Api Information")
router = APIRouter(prefix="/api/v1")
router.include_router(fastq.router, prefix="/fastq")
app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Welcome to the fastq api!!"}


handler = Mangum(app)
