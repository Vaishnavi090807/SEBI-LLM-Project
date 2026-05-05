# SEBI Order LLM Project - Complete Implementation Guide

## Project Overview
An LLM-based system that analyzes SEBI order PDFs to help Indian retail investors identify investment risks.

---

## PHASE 1: UNDERSTANDING YOUR ARCHITECTURE

### What You're Building (3-Layer System):
1. **PDF Processing Layer** → Extract & parse SEBI orders
2. **RAG (Retrieval-Augmented Generation) Layer** → Store and retrieve relevant order data
3. **LLM Query Layer** → Use OLLAMA to answer user questions with context

### Why 90% Accuracy is Achievable:
- SEBI orders are **structured legal documents** (not ambiguous)
- You're doing **retrieval + generation**, not pure generation
- The LLM only needs to match company names and return relevant order sections
- Combine keyword search + semantic search = high confidence

---

## PHASE 2: TECH STACK (All Free/Student-Friendly)

### 1. LLM Engine
**Tool:** OLLAMA (already installed ✓)
- **Model to use:** `mistral:7b` or `neural-chat:7b` (lightweight, good for RAG)
- Command to pull:
  ```bash
  ollama pull mistral:7b
  ```
- Why: Runs locally, free, good for RAG tasks

### 2. Database (Free Options)

#### **Option A: SQLite (Recommended for MVP)**
- File-based, zero setup
- Perfect for storing parsed SEBI order data
- Free & unlimited
- Great for small-medium datasets (100K+ documents)

#### **Option B: PostgreSQL (Scale Later)**
- If data grows beyond 100K documents
- Can run locally with Docker (free)
- Better for complex queries

#### **Option C: MongoDB (Document-based)**
- Great for storing raw PDFs and metadata
- Free locally
- Better for unstructured data

**My Recommendation:** Start with **SQLite** → Migrate to **PostgreSQL** if needed

### 3. Vector Database (For Semantic Search)
**Tool:** Chroma (free, open-source)
- Stores embeddings of SEBI orders
- Enables semantic search ("fraud company" finds relevant orders)
- Runs locally, no cost

### 4. PDF Processing
- **PyPDF2** - Extract text from PDFs (free)
- **pdfplumber** - Better extraction, table handling (free)
- **LangChain** - Orchestrate the entire RAG pipeline (free)

### 5. Backend API
- **FastAPI** (free, fast, Python-based)
- **Flask** (if you prefer simplicity)

### 6. Frontend (Optional)
- **Streamlit** (fastest for prototypes, free)
- **React** (if you want a polished UI)

---

## PHASE 3: DETAILED IMPLEMENTATION PLAN

### Step 1: Setup Your Development Environment

```bash
# Create project folder
mkdir sebi-llm-project
cd sebi-llm-project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --break-system-packages \
  langchain \
  ollama \
  chromadb \
  pdfplumber \
  pypdf2 \
  fastapi \
  uvicorn \
  sqlite3 \
  python-dotenv \
  pandas \
  numpy

# Verify OLLAMA is running
ollama serve  # In another terminal
```

### Step 2: Database Schema (SQLite)

```sql
-- Create tables for SEBI orders
CREATE TABLE sebi_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id VARCHAR(50) UNIQUE,
    company_name VARCHAR(255),
    nse_bse_code VARCHAR(20),
    order_date DATE,
    order_type VARCHAR(100),  -- 'Ban', 'Warning', 'Investigation', etc.
    risk_level VARCHAR(20),  -- 'High', 'Medium', 'Low'
    summary TEXT,
    full_text TEXT,
    pdf_source VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE search_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_query VARCHAR(255),
    results_count INTEGER,
    user_ip VARCHAR(20),
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    chunk_text TEXT,
    embedding BLOB,  -- Store vector embeddings
    FOREIGN KEY(order_id) REFERENCES sebi_orders(id)
);
```

### Step 3: PDF Processing Pipeline

```python
# pdf_processor.py
import pdfplumber
import sqlite3
from datetime import datetime

def extract_sebi_order(pdf_path):
    """Extract structured data from SEBI order PDF"""
    
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    
    # Extract key information (company name, order date, etc.)
    # Use regex or OLLAMA to parse structured info
    
    order_data = {
        'company_name': extract_company_name(full_text),
        'order_date': extract_date(full_text),
        'order_type': extract_order_type(full_text),
        'summary': summarize_with_ollama(full_text),
        'full_text': full_text,
        'pdf_source': pdf_path
    }
    
    return order_data

def store_in_database(order_data):
    """Store extracted data in SQLite"""
    
    conn = sqlite3.connect('sebi_orders.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO sebi_orders 
        (company_name, order_date, order_type, summary, full_text, pdf_source)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        order_data['company_name'],
        order_data['order_date'],
        order_data['order_type'],
        order_data['summary'],
        order_data['full_text'],
        order_data['pdf_source']
    ))
    
    conn.commit()
    conn.close()

def batch_process_pdfs(pdf_folder):
    """Process all SEBI order PDFs"""
    import os
    
    for pdf_file in os.listdir(pdf_folder):
        if pdf_file.endswith('.pdf'):
            print(f"Processing {pdf_file}...")
            order_data = extract_sebi_order(os.path.join(pdf_folder, pdf_file))
            store_in_database(order_data)
```

### Step 4: RAG Pipeline with Vector Search

```python
# rag_pipeline.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
import sqlite3

class SEBIRAGSystem:
    def __init__(self):
        # Initialize OLLAMA embeddings
        self.embeddings = OllamaEmbeddings(model="mistral:7b")
        
        # Initialize Chroma for vector storage
        self.vectorstore = Chroma(
            collection_name="sebi_orders",
            embedding_function=self.embeddings,
            persist_directory="./chroma_db"
        )
        
        # Initialize LLM
        self.llm = ChatOllama(model="mistral:7b", temperature=0.3)
        
    def index_sebi_orders(self):
        """Index all SEBI orders from database into vector store"""
        
        conn = sqlite3.connect('sebi_orders.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, full_text, company_name FROM sebi_orders")
        orders = cursor.fetchall()
        
        # Split text into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        documents = []
        metadatas = []
        
        for order_id, full_text, company_name in orders:
            chunks = splitter.split_text(full_text)
            
            for chunk in chunks:
                documents.append(chunk)
                metadatas.append({
                    'order_id': order_id,
                    'company_name': company_name
                })
        
        # Add to Chroma
        self.vectorstore.add_texts(documents, metadatas=metadatas)
        conn.close()
        
        print(f"Indexed {len(documents)} chunks from {len(orders)} orders")
    
    def search_investment_risk(self, company_name_or_stock):
        """Search for investment risk information"""
        
        # Hybrid search: keyword + semantic
        query = f"Is {company_name_or_stock} involved in fraud or regulatory issues?"
        
        # Vector search
        relevant_docs = self.vectorstore.similarity_search(
            query, 
            k=5  # Top 5 relevant chunks
        )
        
        # Keyword search (fallback)
        conn = sqlite3.connect('sebi_orders.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT company_name, order_type, summary FROM sebi_orders 
            WHERE company_name LIKE ? OR full_text LIKE ?
        ''', (f"%{company_name_or_stock}%", f"%{company_name_or_stock}%"))
        keyword_results = cursor.fetchall()
        conn.close()
        
        # Combine results
        context = "\n".join([doc.page_content for doc in relevant_docs])
        
        return context, keyword_results
    
    def generate_investment_advice(self, company_name):
        """Generate investment advice with context"""
        
        context, keyword_results = self.search_investment_risk(company_name)
        
        # Build prompt
        template = """You are an investment advisor analyzing SEBI (Securities and Exchange Board of India) orders.
        
Given the following SEBI order information about {company_name}:

{context}

Keyword search results: {keyword_results}

Provide:
1. Risk Assessment (High/Medium/Low)
2. Specific violations or warnings from SEBI
3. Investment recommendation (Avoid/Caution/Safe)
4. Key reasons for your assessment

Be concise and factual. Only use information from SEBI orders."""

        prompt = ChatPromptTemplate.from_template(template)
        
        # Generate response
        chain = (
            {"context": lambda x: context, 
             "keyword_results": lambda x: str(keyword_results),
             "company_name": RunnablePassthrough()}
            | prompt 
            | self.llm
        )
        
        response = chain.invoke(company_name)
        
        return response.content

# Usage
rag = SEBIRAGSystem()
rag.index_sebi_orders()
advice = rag.generate_investment_advice("XYZ Limited")
print(advice)
```

### Step 5: FastAPI Backend

```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag_pipeline import SEBIRAGSystem
import sqlite3
from datetime import datetime

app = FastAPI(title="SEBI Investment Risk API")
rag_system = SEBIRAGSystem()

class InvestmentQuery(BaseModel):
    company_name: str
    stock_code: str = None

class InvestmentResponse(BaseModel):
    company_name: str
    risk_level: str
    advice: str
    source_orders: list

@app.on_event("startup")
async def startup():
    """Initialize RAG system on startup"""
    print("Indexing SEBI orders...")
    rag_system.index_sebi_orders()

@app.post("/analyze-investment/")
async def analyze_investment(query: InvestmentQuery):
    """Analyze investment risk for a company"""
    
    try:
        advice = rag_system.generate_investment_advice(query.company_name)
        
        # Log search
        conn = sqlite3.connect('sebi_orders.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO search_logs (search_query, results_count)
            VALUES (?, 1)
        ''', (query.company_name,))
        conn.commit()
        conn.close()
        
        return InvestmentResponse(
            company_name=query.company_name,
            advice=advice,
            risk_level="High/Medium/Low",
            source_orders=[]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 6: Simple Streamlit Frontend (Optional)

```python
# streamlit_app.py
import streamlit as st
import requests

st.title("🔍 SEBI Investment Risk Analyzer")
st.write("Check if a company is safe to invest in based on SEBI orders")

company_name = st.text_input("Enter company name or stock code:")
stock_code = st.text_input("Stock Code (Optional):", "")

if st.button("Analyze Investment Risk"):
    if company_name:
        response = requests.post(
            "http://localhost:8000/analyze-investment/",
            json={"company_name": company_name, "stock_code": stock_code}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            st.success(f"Analysis for {data['company_name']}")
            st.metric("Risk Level", data['risk_level'])
            st.write("**Investment Advice:**")
            st.write(data['advice'])
        else:
            st.error("Error analyzing investment. Try again.")
    else:
        st.warning("Please enter a company name")
```

---

## PHASE 4: ACHIEVING 90% ACCURACY

### Key Strategies:

1. **Hybrid Search (Keyword + Semantic)**
   - Keyword search catches exact company names
   - Semantic search catches related issues
   - Combine results → Higher accuracy

2. **Fine-tune Your Prompts**
   ```python
   # Good prompt = better output
   prompt = """You are analyzing SEBI regulatory documents.
   Return ONLY facts present in these documents.
   Do NOT infer or speculate.
   Format: [Risk: HIGH/MEDIUM/LOW] [Reason: specific violation] [Source: SEBI order date]"""
   ```

3. **Data Validation**
   ```python
   def validate_response(response, original_docs):
       """Ensure LLM response is grounded in source documents"""
       # Check if claimed violations are in source docs
       # Return confidence score
       pass
   ```

4. **Build a Small Test Set**
   - 10-20 SEBI orders with known outcomes
   - Test your system
   - Measure precision/recall
   - Iterate

5. **Use Smaller, Focused LLM**
   - Don't use GPT-4 (costs money)
   - `mistral:7b` is perfect for RAG
   - Smaller models = faster + accurate for structured tasks

---

## PHASE 5: DEPLOYMENT (Free Options)

### For Backend:
- **Render.com** - Free tier (FastAPI deployment)
- **Railway.app** - Free tier with credits
- **PythonAnywhere** - Free Python hosting
- **Replit** - Free cloud coding environment

### For Database:
- **ElephantSQL** - Free PostgreSQL (5MB limit, upgrade later)
- **Supabase** - Free PostgreSQL tier
- **Firebase** - Free Firestore (if you switch to NoSQL)

### For Vector DB:
- **Pinecone** - Free tier (up to 100K vectors)
- **Supabase Vector** - Free with PostgreSQL

---

## PHASE 6: STEP-BY-STEP EXECUTION

### Week 1: Setup & Processing
- [ ] Set up project structure
- [ ] Process 5-10 SEBI order PDFs
- [ ] Store in SQLite
- [ ] Test extraction quality

### Week 2: RAG Pipeline
- [ ] Create Chroma vector store
- [ ] Index all documents
- [ ] Test semantic search
- [ ] Fine-tune chunking strategy

### Week 3: LLM Integration
- [ ] Build RAG pipeline
- [ ] Create FastAPI backend
- [ ] Test accuracy on sample companies
- [ ] Iterate on prompts

### Week 4: Frontend & Testing
- [ ] Build Streamlit UI
- [ ] End-to-end testing
- [ ] Measure accuracy (aim for >90%)
- [ ] Optimize based on results

### Week 5: Deployment
- [ ] Deploy to free hosting
- [ ] Set up monitoring
- [ ] Gather user feedback

---

## PHASE 7: ACCURACY IMPROVEMENT TECHNIQUES

### If you're below 90%:

1. **Add Confidence Scoring**
   ```python
   # Don't return uncertain results
   if confidence < 0.8:
       return "Unable to determine from available SEBI orders"
   ```

2. **Use Few-Shot Prompting**
   ```python
   # Show examples of good analysis
   prompt = """Example 1:
   Query: "TCS Limited"
   SEBI Orders: None found
   Response: TCS is not mentioned in SEBI orders. No regulatory issues found.
   
   Example 2:
   Query: "XYZ Limited"
   SEBI Orders: [Ban issued, 2023]
   Response: [Risk: HIGH] XYZ Limited was banned by SEBI in 2023...
   
   Now analyze: {user_query}"""
   ```

3. **Regular Reindexing**
   - Update SEBI orders monthly
   - Keep vector embeddings fresh

4. **User Feedback Loop**
   - Log when users report incorrect advice
   - Improve based on feedback

---

## PHASE 8: NEXT STEPS AFTER MVP

1. **Add NSE/BSE API Integration**
   - Real-time stock data
   - Cross-reference with SEBI orders

2. **Multi-language Support**
   - Hindi, Tamil, Telugu, Marathi
   - Use Ollama's multilingual models

3. **Alerting System**
   - Notify users when new SEBI orders affect their portfolio

4. **Community Features**
   - User discussions
   - Investment case studies

---

## ESTIMATED TIMELINE
- **Setup & Basic Processing:** 1-2 weeks
- **RAG Pipeline:** 1 week
- **Integration & Testing:** 1-2 weeks
- **Refinement & Deployment:** 1 week
- **Total:** 4-6 weeks to MVP

---

## BUDGET (All Free)
- OLLAMA: Free ✓
- SQLite: Free ✓
- Chroma: Free ✓
- FastAPI: Free ✓
- Streamlit: Free ✓
- Hosting: Free tier (Render, Railway, Replit)
- **Total Cost: $0 for MVP**

---

## Common Pitfalls to Avoid

1. ❌ Don't use generic LLMs without context (hallucinations)
   ✅ Always use RAG (LLM only synthesizes retrieved docs)

2. ❌ Don't rely on semantic search alone
   ✅ Use hybrid search (keyword + semantic)

3. ❌ Don't process PDFs with generic text extraction
   ✅ Use `pdfplumber` for better table/structure handling

4. ❌ Don't ignore data quality
   ✅ Validate extracted data before storing

5. ❌ Don't set accuracy targets too high initially
   ✅ Start with 80%, iterate to 90%+

---

## Questions to Answer Before Starting

1. How many SEBI order PDFs do you have?
2. Are they all English?
3. Do you have NSE/BSE stock codes mapped to company names?
4. What's your target user base size?
5. Do you need real-time updates?

---

This guide gives you everything you need. Start with Phase 1 & 2, then execute Phase 3-6 step by step.
