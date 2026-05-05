# System Architecture & Data Flow Diagrams

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SEBI FRAUD DETECTION LLM SYSTEM               │
└─────────────────────────────────────────────────────────────────┘

                              INPUT LAYER
                              ──────────
                                  │
        ┌─────────────┬─────────────┬──────────────┐
        │             │             │              │
        ▼             ▼             ▼              ▼
    Web UI      Mobile App    API Client    Command Line
        │             │             │              │
        └─────────────┴─────────────┴──────────────┘
                      │
                      ▼
            ┌──────────────────────┐
            │   FastAPI Backend    │
            │   (main.py)          │
            │  - /analyze          │
            │  - /batch-analyze    │
            │  - /search           │
            │  - /stats            │
            └──────────────────────┘
                      │
                      ▼
        ┌────────────────────────────────┐
        │  RAG Processing Pipeline      │
        │  (rag_pipeline.py)            │
        │                               │
        │  1. Hybrid Search             │
        │     ├─ Vector search          │
        │     └─ Keyword search         │
        │  2. Context Retrieval         │
        │  3. LLM Analysis              │
        │  4. Response Generation       │
        └────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
    ┌─────────┐   ┌──────────┐   ┌──────────┐
    │ Chroma  │   │ SQLite   │   │  OLLAMA  │
    │Vector DB│   │Database  │   │  LLM 7B  │
    │Embeddings   │SEBI Data │   │Generation│
    └─────────┘   └──────────┘   └──────────┘
         │              │
         └──────────────┘
                │
                ▼
            OUTPUT LAYER
            ────────────
        Risk Assessment
        Recommendation
        Source Details
```

---

## 2. Data Processing Pipeline

```
SEBI PDF FILES
     │
     ▼
┌──────────────────────────────┐
│  PDF Processor (pdf_processor.py)
├──────────────────────────────┤
│ 1. Extract Text              │
│    └─ pdfplumber             │
│                              │
│ 2. Parse Metadata            │
│    ├─ Company name (regex)   │
│    ├─ Order date (parsing)   │
│    ├─ Order type (classify)  │
│    └─ Risk level (assess)    │
│                              │
│ 3. Generate Summary          │
│    └─ Extract key info       │
└──────────────────────────────┘
     │
     ▼
┌──────────────────────────────┐
│  SQLite Database             │
│  (setup_database.py)         │
├──────────────────────────────┤
│ sebi_orders table:           │
│ - order_id                   │
│ - company_name               │
│ - order_date                 │
│ - order_type                 │
│ - risk_level                 │
│ - summary                    │
│ - full_text                  │
│ - pdf_source                 │
└──────────────────────────────┘
     │
     ▼
┌──────────────────────────────┐
│  Vector Embedding            │
│  (rag_pipeline.py)           │
├──────────────────────────────┤
│ 1. Split into chunks         │
│    └─ 1000 chars/chunk       │
│                              │
│ 2. Create embeddings         │
│    └─ OLLAMA Mistral 7B      │
│                              │
│ 3. Store in Chroma           │
│    └─ Vector database        │
└──────────────────────────────┘
     │
     ▼
  READY FOR QUERIES
```

---

## 3. Query Processing Flow

```
USER QUERY: "Is XYZ Limited safe to invest?"
│
▼
┌─────────────────────────────────────┐
│ FastAPI Request Handler (main.py)   │
│ POST /analyze                       │
├─────────────────────────────────────┤
│ 1. Validate input                   │
│ 2. Log query                        │
│ 3. Pass to RAG system               │
└─────────────────────────────────────┘
│
▼
┌─────────────────────────────────────┐
│ RAG Pipeline (rag_pipeline.py)      │
│ generate_investment_advice()        │
├─────────────────────────────────────┤
│ STEP 1: Search                      │
│ ├─ Vector search:                   │
│ │  "fraud violations XYZ Limited"   │
│ │  → Top 5 similar chunks           │
│ │                                   │
│ └─ Keyword search:                  │
│    "XYZ Limited" LIKE query         │
│    → Exact matches                  │
│                                     │
│ STEP 2: Retrieve Context            │
│ ├─ Combine search results           │
│ ├─ Remove duplicates                │
│ └─ Build context string             │
│                                     │
│ STEP 3: Prepare Prompt              │
│ ├─ "You are investment advisor"     │
│ ├─ "Based on SEBI orders..."        │
│ ├─ "{context}"                      │
│ └─ "Provide risk assessment"        │
│                                     │
│ STEP 4: Generate Response           │
│ └─ Send to OLLAMA LLM               │
└─────────────────────────────────────┘
│
▼
┌─────────────────────────────────────┐
│ OLLAMA Mistral 7B LLM               │
├─────────────────────────────────────┤
│ Processes:                          │
│ - System prompt                     │
│ - Context from SEBI orders          │
│ - User query                        │
│                                     │
│ Generates:                          │
│ "RISK ASSESSMENT: HIGH              │
│  VIOLATIONS: Fraud charges          │
│  RECOMMENDATION: AVOID              │
│  REASONS: SEBI issued ban..."       │
└─────────────────────────────────────┘
│
▼
┌─────────────────────────────────────┐
│ Response Processing (main.py)       │
├─────────────────────────────────────┤
│ 1. Extract risk level               │
│ 2. Extract recommendation           │
│ 3. Format response                  │
│ 4. Add timestamp                    │
│ 5. Log to database                  │
└─────────────────────────────────────┘
│
▼
RESPONSE TO USER
┌─────────────────────────────────────┐
│ {                                   │
│   "company_name": "XYZ Limited",     │
│   "risk_level": "HIGH",             │
│   "advice": "SEBI issued ban...",   │
│   "timestamp": "2024-01-15T10:30Z"  │
│ }                                   │
└─────────────────────────────────────┘
```

---

## 4. Search Strategy (Hybrid Approach)

```
COMPANY: "Telestone Technologies"
│
├─────────────────────────────────────────────────┐
│                                                 │
▼                                                 ▼
VECTOR SEARCH                              KEYWORD SEARCH
(Semantic)                                (Exact Match)
│                                                 │
├─ Query: "fraud violations"            ├─ SQL: SELECT * FROM 
│  Telestone"                           │  sebi_orders WHERE
│                                        │  company_name LIKE '%Telestone%'
├─ Find similar embeddings              │
│                                        ├─ Exact company matches
├─ Top 5 results:                        │
│  1. "SEBI banned Telestone...  (0.92) ├─ Results:
│  2. "Fraud charges against...  (0.88) │  - Telestone Technologies
│  3. "Trading suspension for...  (0.85)│  - Telestone Industries (if exists)
│  4. "Insider trading case...   (0.82) │  - Telestonics Ltd (if exists)
│  5. "Regulatory action...      (0.78) │
│                                        │
└─────────────────────────┬──────────────┘
                          │
                          ▼
              COMBINE RESULTS
              ├─ Remove duplicates
              ├─ Rank by relevance
              ├─ Pick top 5
              └─ Create context
                          │
                          ▼
              SEND TO LLM WITH CONTEXT
```

---

## 5. Database Schema

```
┌──────────────────────────────────────┐
│      SEBI_ORDERS (Main Table)        │
├──────────────────────────────────────┤
│ PRIMARY KEY:                         │
│ - id (auto-increment)                │
│                                      │
│ UNIQUE:                              │
│ - order_id (SEBI-2023-001)           │
│                                      │
│ INDEXED (for search):                │
│ - company_name                       │
│ - order_type                         │
│ - risk_level                         │
│                                      │
│ CONTENT:                             │
│ - nse_code, bse_code                 │
│ - order_date                         │
│ - summary (short)                    │
│ - full_text (complete)               │
│ - pdf_source                         │
│ - created_at, extracted_at           │
└──────────────────────────────────────┘
        │                  │
        ▼                  ▼
┌──────────────┐    ┌────────────────┐
│ EMBEDDINGS   │    │  SEARCH_LOGS   │
├──────────────┤    ├────────────────┤
│ order_id (FK)│    │ search_query   │
│ chunk_id     │    │ company_name   │
│ chunk_text   │    │ results_count  │
│ embedding    │    │ searched_at    │
└──────────────┘    └────────────────┘
        │                  │
        │                  └─ Analytics
        │
        └─ Chroma Vector Store
```

---

## 6. API Endpoint Flow

```
CLIENT REQUEST
│
├─ POST /analyze
│  ├─ Input: {"company_name": "ABC Ltd"}
│  ├─ Process: generate_investment_advice()
│  └─ Output: {
│      "company_name": "ABC Ltd",
│      "risk_level": "HIGH",
│      "advice": "SEBI order...",
│      "timestamp": "2024-01-15T10:30Z"
│    }
│
├─ POST /batch-analyze
│  ├─ Input: {"companies": ["ABC", "XYZ", "PQR"]}
│  ├─ Process: Loop through each company
│  └─ Output: {
│      "total_companies": 3,
│      "successful": 3,
│      "failed": 0,
│      "results": [...]
│    }
│
├─ GET /search/{company_name}
│  ├─ Input: company_name = "ABC Ltd"
│  ├─ Process: hybrid_search()
│  └─ Output: {
│      "company_name": "ABC Ltd",
│      "vector_results_count": 5,
│      "keyword_results_count": 2,
│      "context_preview": "..."
│    }
│
├─ GET /stats
│  └─ Output: {
│      "total_sebi_orders": 250,
│      "orders_by_risk_level": {...},
│      "orders_by_type": {...},
│      "total_searches": 1543
│    }
│
├─ GET /health
│  └─ Output: {
│      "status": "healthy",
│      "rag_initialized": true
│    }
│
└─ GET /
   └─ Output: API documentation
```

---

## 7. Accuracy Improvement Loop

```
INITIAL SYSTEM
│
├─ Test on 20 companies
├─ Measure: 75% accuracy
│
▼
IDENTIFY PROBLEMS
│
├─ Analyze 5 failures
├─ Find patterns
│ ├─ Mistaken HIGH for MEDIUM
│ ├─ Missed keywords
│ └─ Poor context retrieval
│
▼
IMPLEMENT IMPROVEMENTS
│
├─ Improve prompt clarity
├─ Increase vector search k (5→10)
├─ Better chunking (1000→800)
├─ Add few-shot examples
│
▼
RETEST
│
├─ Test on same 20 companies
├─ Measure: 82% accuracy (+7%)
├─ Test on new 10 companies
├─ Measure: 80% accuracy (generalizes)
│
▼
REPEAT
│
├─ Find remaining patterns
├─ Adjust further
├─ Target: 90%+
│
▼
PRODUCTION
│
├─ Deploy with monitoring
├─ Collect user feedback
├─ Continuous improvement
```

---

## 8. System Dependencies

```
┌─────────────────────────────────────────────┐
│ EXTERNAL DEPENDENCIES                       │
├─────────────────────────────────────────────┤
│                                             │
│ ┌────────────────┐  ┌──────────────────┐  │
│ │  OLLAMA        │  │  Internet        │  │
│ │  (Local)       │  │  (Download only) │  │
│ ├────────────────┤  ├──────────────────┤  │
│ │ mistral:7b     │  │ First run:       │  │
│ │ 4GB model      │  │ Download ~4GB    │  │
│ │ Running on     │  │                  │  │
│ │ port 11434     │  │ After: Offline   │  │
│ └────────────────┘  └──────────────────┘  │
│                                             │
│ ┌────────────────┐  ┌──────────────────┐  │
│ │  Python 3.9+   │  │  ~4GB RAM        │  │
│ │  ~200MB        │  │  ~10GB Disk      │  │
│ └────────────────┘  └──────────────────┘  │
│                                             │
│ INTERNAL DEPENDENCIES:                     │
│ ├─ LangChain (RAG framework)               │
│ ├─ ChromaDB (Vector storage)               │
│ ├─ FastAPI (Web framework)                 │
│ ├─ pdfplumber (PDF processing)             │
│ └─ SQLite3 (Database)                      │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 9. Deployment Architecture

```
DEVELOPMENT
├─ Local machine
├─ OLLAMA on :11434
├─ FastAPI on :8000
├─ SQLite local
└─ Chroma local

         │
         ▼

TESTING
├─ Same machine
├─ Load test data
├─ Measure accuracy
└─ Optimize

         │
         ▼

PRODUCTION (Free Hosting)
┌──────────────────────────┐
│ Render.com / Railway.app │
├──────────────────────────┤
│ Container:               │
│ - Python 3.9+            │
│ - FastAPI app            │
│ - SQLite file            │
│ - Chroma vector DB       │
│ - OLLAMA (subprocess)    │
│                          │
│ Exposed:                 │
│ - HTTP API               │
│ - /docs (Swagger)        │
└──────────────────────────┘

         │
         ▼

USERS
├─ Web browser (frontend)
├─ Mobile app
├─ API clients
└─ Command line
```

---

## 10. Performance Metrics

```
LATENCY BREAKDOWN (per query)
│
├─ Vector search:        ~1-2 seconds
│  └─ Chroma retrieval
│
├─ Keyword search:       ~0.5 seconds
│  └─ SQLite query
│
├─ Context assembly:     ~0.5 seconds
│  └─ String concatenation
│
├─ LLM inference:        ~5-8 seconds
│  └─ Mistral 7B generation
│
├─ Response formatting:  ~0.5 seconds
│  └─ JSON serialization
│
└─ TOTAL:                ~8-12 seconds
   (Acceptable for web)

THROUGHPUT
├─ Single query:         1 per 10 seconds
├─ Concurrent queries:   ~2-3 (single machine)
├─ Batch queries:        50 companies in 8 minutes

ACCURACY
├─ Test set (20 cases):  90-95%
├─ Production data:      85-90%
├─ With feedback loop:   90%+ (improves over time)
```

---

## 11. Error Handling Flow

```
QUERY RECEIVED
│
├─ Empty company name?
│  └─ Return: 400 Bad Request
│
├─ OLLAMA not running?
│  └─ Return: 503 Service Unavailable
│
├─ No SEBI orders for company?
│  └─ Return: {
│      risk: "UNKNOWN",
│      message: "No SEBI orders found"
│    }
│
├─ LLM timeout (>30 secs)?
│  └─ Return: 408 Request Timeout
│
├─ Database error?
│  └─ Return: 500 Internal Error
│  └─ Log to file for debugging
│
├─ Invalid response format?
│  └─ Return cached response if available
│  └─ Else return error
│
└─ SUCCESS
   └─ Return result + 200 OK
```

These diagrams show the complete system architecture, data flow, and integration points.
