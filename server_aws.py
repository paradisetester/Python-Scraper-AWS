from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import traceback
import asyncio
import signal
import sys
import os

# Import AWS-optimized modules
import database as db
import scraper_aws as scraper

# Configure logging for AWS
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/cars-scraper/server.log'),
        logging.StreamHandler()
    ]
)

app = FastAPI(
    title="Cars.com Scraper API - AWS",
    description="AWS-optimized API for cars.com scraping with enhanced reliability",
    version="2.0.0"
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logging.error(f"Unhandled exception: {exc}\nTraceback:\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check logs for details."}
    )

# CORS for production
origins = [
    "https://online-app-flex-cars.com",
    "https://online-app-flex-cars.com/",
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class ScrapeRequest(BaseModel):
    stock_type: str = Field(default='all')
    makes: Optional[List[str]] = Field(default=None)
    models: Optional[List[str]] = Field(default=None)
    zip_code: str = Field(default='60606')
    max_distance: int = Field(default=50)
    list_price_min: Optional[int] = Field(default=None)
    list_price_max: Optional[int] = Field(default=None)
    year_min: Optional[int] = Field(default=None)
    year_max: Optional[int] = Field(default=None)
    mileage_max: Optional[int] = Field(default=None)
    body_styles: Optional[List[str]] = Field(default=None)
    fuel_types: Optional[List[str]] = Field(default=None)
    start_page: int = Field(default=1, ge=1)
    end_page: int = Field(default=1, ge=1)
    user_email: Optional[str] = Field(default=None)

# Global task tracking
active_tasks = set()

async def cleanup_task(task_id: str):
    """Clean up completed tasks"""
    await asyncio.sleep(1)
    active_tasks.discard(task_id)

@app.post("/scrape/", status_code=202)
async def trigger_scraping(request: ScrapeRequest, background_tasks: BackgroundTasks):
    try:
        if request.end_page < request.start_page:
            raise HTTPException(status_code=400, detail="End page cannot be less than start page.")
        
        # Generate task ID
        import uuid
        task_id = str(uuid.uuid4())
        active_tasks.add(task_id)
        
        # Add cleanup task
        background_tasks.add_task(cleanup_task, task_id)
        
        # Run scraper in background with AWS optimizations
        background_tasks.add_task(
            scraper.scrape_cars,
            stock_type=request.stock_type,
            makes=request.makes,
            models=request.models,
            zip_code=request.zip_code,
            max_distance=request.max_distance,
            list_price_min=request.list_price_min,
            list_price_max=request.list_price_max,
            year_min=request.year_min,
            year_max=request.year_max,
            mileage_max=request.mileage_max,
            body_styles=request.body_styles,
            fuel_types=request.fuel_types,
            start_page=request.start_page,
            end_page=request.end_page,
            max_workers=2,  # Conservative for AWS
            user_email=request.user_email
        )
        
        return {
            "message": "Scraping started successfully on AWS. Email notification will be sent upon completion.",
            "task_id": task_id,
            "estimated_pages": request.end_page - request.start_page + 1
        }
        
    except Exception as e:
        logging.error(f"Error starting scrape: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scraping: {str(e)}")

@app.get("/health/")
async def health_check():
    """Enhanced health check for AWS"""
    try:
        # Check system resources
        import psutil
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy",
            "service": "Cars.com Scraper API - AWS",
            "version": "2.0.0",
            "active_tasks": len(active_tasks),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "active_tasks": len(active_tasks)
        }

@app.get("/status/")
async def get_status():
    """Get current scraping status"""
    return {
        "active_tasks": len(active_tasks),
        "server_status": "running",
        "wordpress_connection": await check_wordpress_connection()
    }

async def check_wordpress_connection():
    """Check WordPress connectivity"""
    try:
        cars_data = db.get_cars_data_from_wordpress(limit=1)
        return {"status": "connected", "sample_records": len(cars_data)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/wordpress-status/")
async def get_wordpress_status():
    """Check WordPress REST API status"""
    try:
        cars_data = db.get_cars_data_from_wordpress(limit=5)
        return {
            "wordpress_accessible": True,
            "sample_data_count": len(cars_data),
            "message": "WordPress REST API is working correctly."
        }
    except Exception as e:
        return {
            "wordpress_accessible": False,
            "error": str(e),
            "message": "WordPress REST API is not accessible."
        }

# Graceful shutdown handling
def signal_handler(signum, frame):
    logging.info(f"Received signal {signum}. Shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    import uvicorn
    logging.info("🚀 Starting Cars.com Scraper API on AWS...")
    logging.info("📡 Server will be available at: http://0.0.0.0:8000")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        workers=1,  # Single worker for AWS
        access_log=True,
        log_level="info"
    )