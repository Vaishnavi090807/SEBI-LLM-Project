#!/usr/bin/env python3
"""
SEBI Order LLM - Database Setup Script
This script initializes your SQLite database with proper schema
Run this once: python3 setup_database.py
"""

import sqlite3
import os
from datetime import datetime

def setup_database(db_path='sebi_orders.db'):
    """Create database schema for SEBI orders"""
    
    # Remove existing DB if starting fresh
    if os.path.exists(db_path):
        print(f"Database {db_path} already exists. Skipping...")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Main SEBI Orders Table
    cursor.execute('''
        CREATE TABLE sebi_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id VARCHAR(100) UNIQUE NOT NULL,
            company_name VARCHAR(255) NOT NULL,
            nse_code VARCHAR(20),
            bse_code VARCHAR(20),
            order_date DATE,
            order_type VARCHAR(100),
            risk_level VARCHAR(20),
            summary TEXT,
            full_text TEXT,
            pdf_source VARCHAR(255),
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX idx_company ON sebi_orders(company_name)')
    cursor.execute('CREATE INDEX idx_order_type ON sebi_orders(order_type)')
    cursor.execute('CREATE INDEX idx_risk_level ON sebi_orders(risk_level)')
    
    # Vector Embeddings Table
    cursor.execute('''
        CREATE TABLE embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            chunk_id INTEGER,
            chunk_text TEXT NOT NULL,
            embedding BLOB,
            similarity_score FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(order_id) REFERENCES sebi_orders(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('CREATE INDEX idx_order_id ON embeddings(order_id)')
    
    # Search Logs Table (for analytics)
    cursor.execute('''
        CREATE TABLE search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_query VARCHAR(255),
            company_name VARCHAR(255),
            results_found INTEGER,
            risk_level VARCHAR(20),
            user_ip VARCHAR(50),
            response_time_ms INTEGER,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX idx_search_company ON search_logs(company_name)')
    cursor.execute('CREATE INDEX idx_search_date ON search_logs(searched_at)')
    # Cache Table (store common queries)
    cursor.execute('''
        CREATE TABLE query_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash VARCHAR(64) UNIQUE,
            company_name VARCHAR(255),
            cached_response TEXT,
            confidence_score FLOAT,
            expires_at TIMESTAMP,
            hit_count INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX idx_expires ON query_cache(expires_at)')
    
    # Validation Issues Table
    cursor.execute('''
        CREATE TABLE validation_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            issue_type VARCHAR(100),
            description TEXT,
            severity VARCHAR(20),
            resolved BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(order_id) REFERENCES sebi_orders(id)
        )
    ''')
    
    # User Feedback Table (for accuracy improvement)
    cursor.execute('''
        CREATE TABLE user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id INTEGER,
            company_name VARCHAR(255),
            user_rating INTEGER,
            feedback_text TEXT,
            marked_incorrect BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(query_id) REFERENCES search_logs(id)
        )
    ''')
    
    conn.commit()
    
    print("✅ Database schema created successfully!")
    print(f"   Location: {os.path.abspath(db_path)}")
    print("\nTables created:")
    print("  - sebi_orders: Main SEBI order data")
    print("  - embeddings: Vector embeddings for semantic search")
    print("  - search_logs: Query analytics")
    print("  - query_cache: Response caching")
    print("  - validation_issues: Data quality tracking")
    print("  - user_feedback: Accuracy improvement feedback")
    
    conn.close()

def insert_sample_data(db_path='sebi_orders.db'):
    """Insert sample SEBI orders for testing"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    sample_orders = [
        (
            'SEBI-2023-001',
            'Telestone Technologies Ltd',
            'TELESTONE',
            '517120',
            '2023-03-15',
            'Fraud/Insider Trading',
            'High',
            'SEBI imposed penalties and trading ban for unauthorized trading and fraud',
            'Full text of SEBI order against Telestone Technologies...',
            'sebi_order_telestone_2023.pdf'
        ),
        (
            'SEBI-2023-002',
            'Parekh Aluminex Limited',
            'PAREKHALM',
            '517165',
            '2023-05-20',
            'Violation of regulations',
            'Medium',
            'SEBI issued warning for regulatory non-compliance',
            'Full text of SEBI order against Parekh Aluminex...',
            'sebi_order_parekhalm_2023.pdf'
        ),
        (
            'SEBI-2023-003',
            'Saradha Group',
            None,
            None,
            '2023-01-10',
            'Ponzi Scheme',
            'High',
            'SEBI action against Ponzi scheme operator',
            'Full text regarding Saradha Group Ponzi scheme...',
            'sebi_order_saradha_2023.pdf'
        ),
    ]
    
    for order in sample_orders:
        try:
            cursor.execute('''
                INSERT INTO sebi_orders 
                (order_id, company_name, nse_code, bse_code, order_date, 
                 order_type, risk_level, summary, full_text, pdf_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', order)
        except sqlite3.IntegrityError:
            print(f"Order {order[0]} already exists, skipping...")
    
    conn.commit()
    print("\n✅ Sample data inserted successfully!")
    conn.close()

def verify_database(db_path='sebi_orders.db'):
    """Verify database structure"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("\n📊 Database Verification:")
    print(f"Tables: {len(tables)}")
    
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f"\n  {table[0]}: {len(columns)} columns")
        for col in columns[:5]:  # Show first 5 columns
            print(f"    - {col[1]} ({col[2]})")
    
    # Count records
    cursor.execute("SELECT COUNT(*) FROM sebi_orders")
    order_count = cursor.fetchone()[0]
    print(f"\n📝 Records: {order_count} SEBI orders")
    
    conn.close()

if __name__ == '__main__':
    print("🚀 SEBI Order LLM - Database Setup\n")
    
    setup_database()
    insert_sample_data()
    verify_database()
    
    print("\n✨ Setup complete! Your database is ready.")
    print("\nNext steps:")
    print("1. Place your SEBI PDF files in a 'sebi_pdfs/' folder")
    print("2. Run: python3 pdf_processor.py")
    print("3. Run: python3 rag_pipeline.py")
    print("4. Start the API: python3 main.py")
