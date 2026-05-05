# 🚀 SEBI Investment LLM - Quick Start Guide

## Prerequisites
- Python 3.9+
- OLLAMA installed (download from https://ollama.ai)
- 4GB+ RAM
- ~10GB disk space (for models and data)

---

## 📋 Step 1: Environment Setup (5 minutes)

### 1.1 Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 1.2 Install Dependencies
```bash
pip install --break-system-packages -r requirements.txt
```

### 1.3 Verify OLLAMA Installation
```bash
# In a NEW terminal window, start OLLAMA
ollama serve

# In another terminal, pull the model
ollama pull mistral:7b
```

Wait for the model to download (~4GB). You should see:
```
pulling manifest
pulling 4bef08b3c3cb
```

---

## 🗄️ Step 2: Database Setup (2 minutes)

```bash
# Create and initialize the SQLite database
python3 setup_database.py
```

Expected output:
```
✅ Database schema created successfully!
   Location: /path/to/sebi_orders.db
```

---

## 📄 Step 3: Add Your SEBI PDF Files (varies)

### 3.1 Create PDF Folder
```bash
mkdir sebi_pdfs
```

### 3.2 Add Your SEBI Order PDFs
Place your SEBI order PDF files in the `sebi_pdfs/` folder.

**Where to get SEBI orders:**
- SEBI Website: https://www.sebi.gov.in/
- Search for: "SEBI Orders" → "Enforcement" section
- Download PDF files of SEBI orders

### 3.3 Sample PDFs (for testing)
If you don't have PDFs yet, the system includes sample data. Skip to Step 4.

---

## 🔄 Step 4: Process PDFs & Index (5-10 minutes)

```bash
# Extract data from PDFs and store in database
python3 pdf_processor.py
```

Expected output:
```
📄 Processing: sebi_order_telestone.pdf
  ✓ Company: Telestone Technologies
  ✓ Type: Fraud
  ✓ Risk: High
  ✓ Date: 2023-03-15
  ✓ Stored in database

✅ Batch processing complete!
```

---

## 🧠 Step 5: Build RAG System (10-20 minutes)

```bash
# Create vector embeddings and index
python3 rag_pipeline.py
```

**First run:** Takes longer (10-20 mins) while creating embeddings
**Subsequent runs:** Much faster (< 1 min)

Expected output:
```
🚀 Initializing SEBI RAG System...
  📚 Loading embeddings model...
  🔍 Initializing vector store...
  🧠 Loading LLM...
✅ RAG System initialized successfully!

📑 Indexing SEBI Orders...
Found 10 SEBI orders
  ⏳ Adding 250 chunks to vector store...
✅ Indexing complete! Total chunks: 250

==============================================================
Analyzing: Telestone Technologies Ltd
==============================================================

🔍 Searching investment risk for: Telestone Technologies Ltd

RISK ASSESSMENT: HIGH

VIOLATION DETAILS: Fraud and insider trading activities...
...
```

---

## 🌐 Step 6: Start the API Server (2 minutes)

```bash
# Start FastAPI backend
python3 main.py
```

Expected output:
```
🚀 Starting SEBI Investment API...
📚 Initializing RAG system...
✅ API Ready!

Starting server on http://localhost:8000
API Documentation: http://localhost:8000/docs
```

---

## 🧪 Step 7: Test the API

### Option A: Using Swagger UI (Easiest)
1. Open browser: http://localhost:8000/docs
2. Click "Try it out" on `/analyze` endpoint
3. Enter company name: `Telestone Technologies`
4. Click "Execute"

### Option B: Using cURL
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Telestone Technologies", "stock_code": "TELESTONE"}'
```

### Option C: Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/analyze",
    json={"company_name": "Telestone Technologies"}
)

print(response.json())
```

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│          User Query (Company Name)                  │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│          FastAPI Server (main.py)                   │
│  - Handles HTTP requests                            │
│  - Manages RAG system                               │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│       RAG System (rag_pipeline.py)                  │
│  - Hybrid search (semantic + keyword)               │
│  - Vector store queries                             │
│  - Context retrieval                                │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼──────────┐  ┌───────▼──────────┐
│  Chroma Vector   │  │  SQLite Database │
│    Store         │  │  sebi_orders.db  │
│  (embeddings)    │  │  (order metadata)│
└──────────────────┘  └──────────────────┘
        │                     │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  OLLAMA LLM         │
        │  (mistral:7b)       │
        │  - Generates advice │
        │  - Uses context     │
        └─────────────────────┘
```

---

## 🔧 Troubleshooting

### Issue: "Cannot connect to OLLAMA"
```
❌ Error: HTTPConnectionError
Solution:
1. Open new terminal
2. Run: ollama serve
3. Wait for "Listening on..."
```

### Issue: "Model not found"
```
❌ Error: Model mistral:7b not found
Solution:
Run in terminal: ollama pull mistral:7b
Wait for download to complete.
```

### Issue: "Out of memory"
```
❌ Error: CUDA out of memory
Solution:
- Reduce chunk_size in rag_pipeline.py (1000 → 500)
- Reduce top_k in hybrid_search (5 → 3)
- Use CPU instead: Set OLLAMA_DEVICE=cpu
```

### Issue: "No PDFs found"
```
❌ Error: No PDF files found in sebi_pdfs/
Solution:
- Create folder: mkdir sebi_pdfs
- Add your SEBI PDF files to this folder
- Run: python3 pdf_processor.py
```

### Issue: "Database locked"
```
❌ Error: sqlite3.OperationalError: database is locked
Solution:
- Close other Python instances accessing the database
- Wait 10 seconds and retry
```

---

## 📈 Expected Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Setup | 5 mins | One-time |
| PDF Processing | 1-2 mins per PDF | Depends on PDF size |
| Vector Indexing | 10-20 mins first | ~1 min after |
| Single Query | 5-10 secs | LLM generation time |
| Batch (10 companies) | 1-2 mins | Parallel possible |

---

## 🎯 Next Steps

### Immediate (This Week)
- [ ] Get 10-20 real SEBI PDFs
- [ ] Process them with pdf_processor.py
- [ ] Test the API with real data
- [ ] Measure accuracy on known cases

### Short-term (This Month)
- [ ] Integrate NSE/BSE stock codes API
- [ ] Build a simple web frontend (Streamlit)
- [ ] Deploy to free hosting (Render.com)
- [ ] Improve accuracy with fine-tuning

### Medium-term (2-3 Months)
- [ ] Add multi-language support (Hindi, Tamil)
- [ ] Implement user feedback loop
- [ ] Create mobile app
- [ ] Deploy to scalable infrastructure

---

## 📚 Useful Resources

**SEBI Documents:**
- SEBI Orders: https://www.sebi.gov.in/orders
- Enforcement Actions: https://www.sebi.gov.in/enforcement

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Learning Resources:**
- RAG Systems: https://docs.langchain.com/docs/use_cases/question_answering
- OLLAMA Docs: https://github.com/ollama/ollama
- Vector Databases: https://www.trychroma.com/

---

## 💡 Pro Tips

### 1. Monitor Database Growth
```bash
sqlite3 sebi_orders.db "SELECT COUNT(*) FROM sebi_orders;"
```

### 2. Check Vector Store
```bash
python3 -c "from langchain_community.vectorstores import Chroma; 
c = Chroma(persist_directory='./chroma_db'); 
print(f'Total chunks: {c._collection.count()}')"
```

### 3. Backup Your Data
```bash
cp sebi_orders.db sebi_orders_backup.db
cp -r chroma_db chroma_db_backup
```

### 4. Clear Vector Store (Reindex)
```bash
rm -rf chroma_db/
python3 rag_pipeline.py  # Will rebuild
```

---

## 🤝 Contributing

Have SEBI PDFs to add? Improvements to suggest?
1. Process your PDFs
2. Test the system
3. Measure accuracy
4. Share results!

---

## ✅ Verification Checklist

Before claiming "ready for production":

- [ ] Database has >50 SEBI orders
- [ ] All PDFs processed successfully
- [ ] Vector store indexed (>500 chunks)
- [ ] API responds in <15 seconds
- [ ] Tested on 10+ companies
- [ ] Accuracy >80% on test set
- [ ] No errors in logs
- [ ] Can handle batch requests

---

## 📞 Support

For issues:
1. Check troubleshooting section above
2. Review error messages in console
3. Check disk space: `df -h`
4. Check OLLAMA status: `ollama list`

---

## 🎉 You're Ready!

Once all steps are complete:
- API running on http://localhost:8000
- Test with: `curl http://localhost:8000/health`
- Check docs at: http://localhost:8000/docs

**Next: Build your frontend or integrate with NSE/BSE APIs!**
