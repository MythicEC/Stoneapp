from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import base64
import io
import re
import pdfplumber

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str
    customer_name: str
    stone_type: str
    pdf_content: str  # base64 encoded PDF
    extracted_text: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)

class OrderCreate(BaseModel):
    order_number: str
    customer_name: str
    stone_type: str

class OrderSearch(BaseModel):
    search_term: str
    search_type: str  # "order_number", "customer_name", "stone_type", "all"

# Helper function to extract text from PDF
def extract_text_from_pdf(pdf_content: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return ""

# Helper function to extract structured data from text
def extract_order_info(text: str):
    # Extract order number patterns (assuming formats like "Auftrag: 12345", "Auftragsnummer: A-2023-001", etc.)
    order_patterns = [
        r"Auftrag(?:s?nummer)?[:\-\s]+([A-Z0-9\-]+)",
        r"Order[:\-\s]+([A-Z0-9\-]+)",
        r"Nr[:\-\s]+([A-Z0-9\-]+)"
    ]
    
    order_number = ""
    for pattern in order_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            order_number = match.group(1)
            break
    
    # Extract customer name patterns
    customer_patterns = [
        r"Kunde[:\-\s]+([A-Za-zäöüß\s]+)",
        r"Auftraggeber[:\-\s]+([A-Za-zäöüß\s]+)",
        r"Customer[:\-\s]+([A-Za-z\s]+)"
    ]
    
    customer_name = ""
    for pattern in customer_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            customer_name = match.group(1).strip()
            break
    
    # Extract stone type patterns
    stone_patterns = [
        r"Stein(?:art)?[:\-\s]+([A-Za-zäöüß\s]+)",
        r"Material[:\-\s]+([A-Za-zäöüß\s]+)",
        r"Granit|Marmor|Kalkstein|Sandstein|Schiefer|Basalt|Travertin"
    ]
    
    stone_type = ""
    for pattern in stone_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            stone_type = match.group(1).strip() if match.groups() else match.group(0)
            break
    
    return {
        "order_number": order_number or "Nicht erkannt",
        "customer_name": customer_name or "Nicht erkannt", 
        "stone_type": stone_type or "Nicht erkannt"
    }

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Steinmetz Auftragsverwaltung API"}

@api_router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Nur PDF-Dateien sind erlaubt")
        
        # Read file content
        pdf_content = await file.read()
        
        # Extract text from PDF
        extracted_text = extract_text_from_pdf(pdf_content)
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Kein Text im PDF gefunden")
        
        # Extract structured information
        order_info = extract_order_info(extracted_text)
        
        # Convert PDF to base64
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        # Create order object
        order = Order(
            order_number=order_info["order_number"],
            customer_name=order_info["customer_name"],
            stone_type=order_info["stone_type"],
            pdf_content=pdf_base64,
            extracted_text=extracted_text
        )
        
        # Save to database
        result = await db.orders.insert_one(order.dict())
        
        return {
            "message": "PDF erfolgreich hochgeladen und verarbeitet",
            "order_id": order.id,
            "extracted_info": {
                "order_number": order.order_number,
                "customer_name": order.customer_name,
                "stone_type": order.stone_type
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error uploading PDF: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Hochladen des PDFs")

@api_router.post("/search-orders")
async def search_orders(search: OrderSearch):
    try:
        # Build search query
        query = {}
        
        if search.search_type == "order_number":
            query["order_number"] = {"$regex": search.search_term, "$options": "i"}
        elif search.search_type == "customer_name":
            query["customer_name"] = {"$regex": search.search_term, "$options": "i"}
        elif search.search_type == "stone_type":
            query["stone_type"] = {"$regex": search.search_term, "$options": "i"}
        elif search.search_type == "all":
            query = {
                "$or": [
                    {"order_number": {"$regex": search.search_term, "$options": "i"}},
                    {"customer_name": {"$regex": search.search_term, "$options": "i"}},
                    {"stone_type": {"$regex": search.search_term, "$options": "i"}}
                ]
            }
        
        # Execute search
        orders_cursor = db.orders.find(query).sort("upload_date", -1)
        orders_list = await orders_cursor.to_list(100)
        
        # Remove PDF content from results (too large for response)
        results = []
        for order in orders_list:
            order_dict = Order(**order).dict()
            order_dict.pop('pdf_content', None)  # Remove large PDF content
            results.append(order_dict)
        
        return {
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logging.error(f"Error searching orders: {e}")
        raise HTTPException(status_code=500, detail="Fehler bei der Suche")

@api_router.get("/orders")
async def get_all_orders():
    try:
        orders_cursor = db.orders.find({}).sort("upload_date", -1)
        orders_list = await orders_cursor.to_list(100)
        
        # Remove PDF content from results
        results = []
        for order in orders_list:
            order_dict = Order(**order).dict()
            order_dict.pop('pdf_content', None)
            results.append(order_dict)
        
        return {"orders": results}
        
    except Exception as e:
        logging.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Aufträge")

@api_router.get("/order/{order_id}")
async def get_order(order_id: str):
    try:
        order = await db.orders.find_one({"id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Auftrag nicht gefunden")
        
        return Order(**order).dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching order: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden des Auftrags")

@api_router.delete("/order/{order_id}")
async def delete_order(order_id: str):
    try:
        result = await db.orders.delete_one({"id": order_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Auftrag nicht gefunden")
        
        return {"message": "Auftrag erfolgreich gelöscht"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting order: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Löschen des Auftrags")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()