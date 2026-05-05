#!/usr/bin/env python3
"""
RAG Pipeline for SEBI Order Analysis
Uses OLLAMA for embeddings and LLM generation
Stores embeddings in Chroma vector database
"""

import sqlite3
import os
import hashlib
from typing import List, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class SEBIRAGSystem:
    """Complete RAG system for SEBI order analysis"""
    
    def __init__(self, db_path='sebi_orders.db', chroma_dir='./chroma_db'):
        """Initialize RAG system"""
        
        print("🚀 Initializing SEBI RAG System...")
        
        self.db_path = db_path
        self.chroma_dir = chroma_dir
        
        # Create chroma directory if it doesn't exist
        os.makedirs(chroma_dir, exist_ok=True)
        
        try:
            # Initialize OLLAMA embeddings
            print("  📚 Loading embeddings model...")
            self.embeddings = OllamaEmbeddings(
                model="mistral:7b",
                base_url="http://localhost:11434"
            )
            
            # Initialize Chroma vector store
            print("  🔍 Initializing vector store...")
            self.vectorstore = Chroma(
                collection_name="sebi_orders",
                embedding_function=self.embeddings,
                persist_directory=chroma_dir
            )
            
            # Initialize LLM
            print("  🧠 Loading LLM...")
            self.llm = Ollama(
                model="mistral:7b",
                base_url="http://localhost:11434",
                temperature=0.3,
                num_predict=500
            )
            
            print("✅ RAG System initialized successfully!\n")
        
        except Exception as e:
            print(f"❌ Error initializing RAG system: {e}")
            print("Make sure OLLAMA is running: ollama serve")
            raise
    
    def get_sebi_orders_from_db(self) -> List[Tuple]:
        """Fetch all SEBI orders from database"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, company_name, order_type, risk_level, 
                       summary, full_text FROM sebi_orders
            ''')
            
            orders = cursor.fetchall()
            conn.close()
            
            return orders
        
        except Exception as e:
            print(f"❌ Error fetching orders: {e}")
            return []
    
    def index_sebi_orders(self, force_reindex=False):
        """
        Index all SEBI orders into vector store
        Creates document chunks and stores embeddings
        """
        
        print("\n📑 Indexing SEBI Orders...")
        
        # Check if already indexed
        if not force_reindex and self.vectorstore._collection.count() > 0:
            count = self.vectorstore._collection.count()
            print(f"✓ Vector store already indexed ({count} chunks)")
            return
        
        # Fetch orders from database
        orders = self.get_sebi_orders_from_db()
        
        if not orders:
            print("❌ No SEBI orders found in database!")
            print("Please run: python3 pdf_processor.py first")
            return
        
        print(f"Found {len(orders)} SEBI orders")
        
        # Split text into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
        documents = []
        metadatas = []
        
        for order_id, company_name, order_type, risk_level, summary, full_text in orders:
            # Chunk the full text
            chunks = splitter.split_text(full_text)
            
            print(f"  📄 {company_name} ({order_type}) - {len(chunks)} chunks")
            
            for chunk_idx, chunk in enumerate(chunks):
                # Create unique IDs
                doc_id = f"{order_id}_chunk_{chunk_idx}"
                
                documents.append(chunk)
                metadatas.append({
                    'order_id': order_id,
                    'company_name': company_name,
                    'order_type': order_type,
                    'risk_level': risk_level,
                    'chunk_id': chunk_idx,
                    'doc_id': doc_id
                })
        
        # Add to Chroma
        print(f"\n  ⏳ Adding {len(documents)} chunks to vector store...")
        
        # Add in batches to avoid memory issues
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_meta = metadatas[i:i+batch_size]
            
            self.vectorstore.add_texts(
                batch_docs,
                metadatas=batch_meta,
                ids=[m['doc_id'] for m in batch_meta]
            )
            
            progress = min(i + batch_size, len(documents))
            print(f"    Progress: {progress}/{len(documents)}")
        
        # Persist
        self.vectorstore.persist()
        
        print(f"\n✅ Indexing complete! Total chunks: {len(documents)}\n")
    
    def hybrid_search(self, company_name: str, top_k: int = 5) -> Tuple[List, List]:
        """
        Hybrid search: combine vector search + keyword search
        Returns both semantic matches and exact matches
        """
        
        # Vector search
        search_query = f"Information about {company_name} fraud violations regulations"
        
        try:
            vector_results = self.vectorstore.similarity_search(
                search_query,
                k=top_k,
                filter={'company_name': company_name}
            )
        except:
            # If filter doesn't work, search without filter
            vector_results = self.vectorstore.similarity_search(
                search_query,
                k=top_k
            )
        
        # Keyword search (fallback for exact matches)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT company_name, order_type, risk_level, summary FROM sebi_orders
            WHERE company_name LIKE ? OR full_text LIKE ?
            LIMIT ?
        ''', (f"%{company_name}%", f"%{company_name}%", top_k))
        
        keyword_results = cursor.fetchall()
        conn.close()
        
        return vector_results, keyword_results
    
    def search_investment_risk(self, company_name: str) -> dict:
        """
        Search for investment risk information
        Returns structured data with search results
        """
        
        print(f"\n🔍 Searching investment risk for: {company_name}")
        
        # Perform hybrid search
        vector_results, keyword_results = self.hybrid_search(company_name, top_k=5)
        
        # Prepare context for LLM
        context_parts = []
        
        if vector_results:
            context_parts.append("=== Vector Search Results ===")
            for doc in vector_results:
                context_parts.append(doc.page_content)
        
        if keyword_results:
            context_parts.append("\n=== Keyword Search Results ===")
            for comp_name, order_type, risk_level, summary in keyword_results:
                context_parts.append(f"Company: {comp_name}\n"
                                   f"Type: {order_type}\n"
                                   f"Risk: {risk_level}\n"
                                   f"Summary: {summary}\n")
        
        context = "\n".join(context_parts)
        
        return {
            'company_name': company_name,
            'context': context,
            'vector_results': len(vector_results),
            'keyword_results': len(keyword_results)
        }
    
    def generate_investment_advice(self, company_name: str) -> str:
        """
        Generate investment advice using RAG
        LLM uses SEBI order context to provide recommendations
        """
        
        # Search for relevant information
        search_result = self.search_investment_risk(company_name)
        context = search_result['context']
        
        # If no results found
        if not context.strip():
            return f"No SEBI orders found for {company_name}. Company appears to have no known regulatory issues in SEBI database."
        
        # Build prompt
        prompt_template = """You are an investment advisor analyzing SEBI (Securities and Exchange Board of India) orders.

Based on the following information from SEBI orders about {company_name}:

{context}

Provide investment advice in this exact format:

RISK ASSESSMENT: [HIGH/MEDIUM/LOW]

VIOLATION DETAILS: [Specific violations or warnings from SEBI]

INVESTMENT RECOMMENDATION: [AVOID/CAUTION/SAFE]

REASONS: [Key reasons for your assessment, citing specific SEBI findings]

IMPORTANT: Only use information explicitly mentioned in the SEBI documents above. 
Do not speculate or infer information not present in the documents.
Be concise and factual."""

        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        # Create chain
        chain = prompt | self.llm | StrOutputParser()
        
        # Generate response
        try:
            response = chain.invoke({
                'company_name': company_name,
                'context': context
            })
            return response
        except Exception as e:
            print(f"❌ Error generating advice: {e}")
            return f"Error analyzing {company_name}. Please try again."
    
    def batch_analyze(self, company_list: List[str]) -> List[dict]:
        """Analyze multiple companies at once"""
        
        results = []
        
        for company in company_list:
            advice = self.generate_investment_advice(company)
            results.append({
                'company_name': company,
                'advice': advice
            })
        
        return results

def main():
    """Main execution"""
    
    # Initialize RAG system
    rag = SEBIRAGSystem()
    
    # Index all SEBI orders
    rag.index_sebi_orders()
    
    # Example queries
    print("\n" + "="*60)
    print("EXAMPLE QUERIES")
    print("="*60)
    
    test_companies = [
        "Telestone Technologies",
        "Parekh Aluminex",
        "Saradha Group"
    ]
    
    for company in test_companies:
        print(f"\n{'='*60}")
        print(f"Analyzing: {company}")
        print(f"{'='*60}")
        
        advice = rag.generate_investment_advice(company)
        print("\n" + advice)
    
    print("\n\n✨ RAG system ready for API integration!")

if __name__ == '__main__':
    main()
