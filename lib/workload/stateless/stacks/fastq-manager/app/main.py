from fastapi import FastAPI
from fastapi.routing import APIRouter
from mangum import Mangum
from .api.v1.routers import fastq

app = FastAPI(title="Fastq Api", summary="Access Fastq Api Information")
router = APIRouter(prefix="/v1")
router.include_router(fastq.router, prefix="/fastq")
app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Welcome to my api!!"}


handler = Mangum(app)
