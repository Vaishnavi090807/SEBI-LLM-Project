from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import os
import shutil
from datetime import datetime
import logging
from rag_pipeline import SEBIRAGSystem
from pdf_processor import SEBIPDFProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello, SEBI LLM is live!"}

app = FastAPI(
    title="SEBI Investment Risk Analysis API",
    description="Analyze SEBI fraud orders for investment risk",
    version="2.0.0"
)

# Initialize systems
rag_system = None
pdf_processor = None

class InvestmentQuery(BaseModel):
    company_name: str
    stock_code: Optional[str] = None

class InvestmentResponse(BaseModel):
    company_name: str
    risk_level: str
    advice: str
    timestamp: str

@app.on_event("startup")
async def startup():
    global rag_system, pdf_processor
    print("\n🚀 Starting SEBI Investment API v2.0...")
    
    rag_system = SEBIRAGSystem()
    pdf_processor = SEBIPDFProcessor()
    rag_system.index_sebi_orders()
    
    print("✅ API Ready!\n")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Web UI Home Page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SEBI Investment Risk Analyzer</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                padding: 40px;
            }
            h1 { 
                color: #333; 
                margin-bottom: 10px;
                text-align: center;
            }
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 30px;
            }
            .section {
                margin-bottom: 30px;
            }
            .section-title {
                font-size: 18px;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 15px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            input, textarea, button {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            button {
                background: #667eea;
                color: white;
                border: none;
                cursor: pointer;
                font-weight: bold;
                transition: 0.3s;
            }
            button:hover {
                background: #764ba2;
            }
            .result {
                background: #f0f4ff;
                padding: 20px;
                border-radius: 5px;
                margin-top: 20px;
                display: none;
            }
            .result.show {
                display: block;
            }
            .risk-high { color: #d32f2f; font-weight: bold; }
            .risk-medium { color: #f57c00; font-weight: bold; }
            .risk-low { color: #388e3c; font-weight: bold; }
            .loading {
                text-align: center;
                color: #667eea;
                display: none;
            }
            .upload-area {
                border: 2px dashed #667eea;
                border-radius: 5px;
                padding: 20px;
                text-align: center;
                cursor: pointer;
                transition: 0.3s;
            }
            .upload-area:hover {
                background: #f0f4ff;
            }
            .file-input {
                display: none;
            }
            .stats {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-top: 20px;
            }
            .stat-box {
                background: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                text-align: center;
            }
            .stat-number {
                font-size: 24px;
                color: #667eea;
                font-weight: bold;
            }
            .stat-label {
                color: #666;
                font-size: 12px;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 SEBI Investment Risk Analyzer</h1>
            <p class="subtitle">Check if a company is safe to invest based on SEBI orders</p>
            
            <!-- Query Section -->
            <div class="section">
                <div class="section-title">📊 Analyze Company Risk</div>
                <input type="text" id="company" placeholder="Enter company name (e.g., Telestone Technologies)">
                <input type="text" id="stock" placeholder="Stock code (optional)">
                <button onclick="analyzeCompany()">Analyze Risk</button>
            </div>
            
            <!-- Upload Section -->
            <div class="section">
                <div class="section-title">📄 Upload New SEBI PDF</div>
                <div class="upload-area" onclick="document.getElementById('pdfFile').click()">
                    <p>📁 Click to upload or drag SEBI order PDF</p>
                    <input type="file" id="pdfFile" class="file-input" accept=".pdf">
                </div>
                <button onclick="uploadPDF()">Upload PDF</button>
            </div>
            
            <!-- Loading -->
            <div class="loading" id="loading">⏳ Processing... please wait</div>
            
            <!-- Results -->
            <div class="result" id="result">
                <h2 id="resultCompany"></h2>
                <p><strong>Risk Level:</strong> <span id="resultRisk"></span></p>
                <p><strong>Analysis:</strong></p>
                <p id="resultAdvice"></p>
            </div>
            
            <!-- Stats -->
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-number" id="totalOrders">-</div>
                    <div class="stat-label">SEBI Orders</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number" id="totalSearches">-</div>
                    <div class="stat-label">Total Searches</div>
                </div>
            </div>
        </div>
        
        <script>
            // Load stats
            async function loadStats() {
                try {
                    const res = await fetch('/stats');
                    const data = await res.json();
                    document.getElementById('totalOrders').textContent = data.total_sebi_orders;
                    document.getElementById('totalSearches').textContent = data.total_searches;
                } catch (e) {
                    console.error('Error loading stats:', e);
                }
            }
            
            // Analyze company
            async function analyzeCompany() {
                const company = document.getElementById('company').value;
                if (!company) {
                    alert('Please enter company name');
                    return;
                }
                
                document.getElementById('loading').style.display = 'block';
                document.getElementById('result').classList.remove('show');
                
                try {
                    const res = await fetch('/analyze', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ company_name: company })
                    });
                    
                    const data = await res.json();
                    
                    document.getElementById('resultCompany').textContent = data.company_name;
                    document.getElementById('resultRisk').textContent = data.risk_level;
                    document.getElementById('resultRisk').className = `risk-${data.risk_level.toLowerCase()}`;
                    document.getElementById('resultAdvice').textContent = data.advice;
                    
                    document.getElementById('result').classList.add('show');
                    loadStats(); // Refresh stats
                } catch (e) {
                    alert('Error: ' + e.message);
                } finally {
                    document.getElementById('loading').style.display = 'none';
                }
            }
            
            // Upload PDF
            async function uploadPDF() {
                const file = document.getElementById('pdfFile').files[0];
                if (!file) {
                    alert('Please select a PDF file');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', file);
                
                document.getElementById('loading').style.display = 'block';
                
                try {
                    const res = await fetch('/upload-pdf', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await res.json();
                    alert('✅ PDF uploaded and processed! Company: ' + data.company_name);
                    
                    document.getElementById('pdfFile').value = '';
                    loadStats();
                } catch (e) {
                    alert('Error: ' + e.message);
                } finally {
                    document.getElementById('loading').style.display = 'none';
                }
            }
            
            // Handle drag and drop
            document.getElementById('pdfFile').addEventListener('change', uploadPDF);
            
            // Load stats on page load
            loadStats();
            setInterval(loadStats, 30000); // Refresh every 30 seconds
        </script>
    </body>
    </html>
    """

@app.post("/analyze")
async def analyze_investment(query: InvestmentQuery):
    """Analyze company risk"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        advice = rag_system.generate_investment_advice(query.company_name)
        
        # Extract risk level
        if "HIGH" in advice.upper():
            risk_level = "HIGH"
        elif "MEDIUM" in advice.upper():
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return InvestmentResponse(
            company_name=query.company_name,
            risk_level=risk_level,
            advice=advice,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload and process SEBI PDF"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    try:
        # Save uploaded file
        upload_path = f"sebi_pdfs/{file.filename}"
        with open(upload_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
        # Process PDF
        order_data = pdf_processor.process_pdf(upload_path)
        
        if order_data:
            # Store in database
            pdf_processor.store_order(order_data)
            
            # Reindex in background
            if background_tasks:
                background_tasks.add_task(rag_system.index_sebi_orders, force_reindex=True)
            
            return {
                "status": "success",
                "filename": file.filename,
                "company_name": order_data['company_name'],
                "risk_level": order_data['risk_level']
            }
        else:
            raise HTTPException(status_code=400, detail="Could not process PDF")
    
    except Exception as e:
        logger.error(f"Error uploading PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get database statistics"""
    try:
        conn = sqlite3.connect('sebi_orders.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sebi_orders")
        total_orders = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM search_logs")
        total_searches = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_sebi_orders": total_orders,
            "total_searches": total_searches,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "rag_initialized": rag_system is not None,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("SEBI Investment Risk API v2.0")
    print("="*60)
    print("\n🌐 Web UI: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("⏸️  To stop: Press Ctrl+C\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)