#!/usr/bin/env python3
"""
Auto PDF Processor with File Watcher
Monitors sebi_pdfs/ folder and processes new PDFs automatically
"""

import os
import time
import sqlite3
from pathlib import Path
from datetime import datetime
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from pdf_processor import SEBIPDFProcessor
from rag_pipeline import SEBIRAGSystem

class PDFWatcherHandler(FileSystemEventHandler):
    """Watch for new PDF files and process them"""
    
    def __init__(self, pdf_processor, rag_system):
        self.pdf_processor = pdf_processor
        self.rag_system = rag_system
        self.processed_files = set()
    
    def on_created(self, event):
        """Triggered when new file is created"""
        if event.is_dir:
            return
        
        # Only process PDF files
        if not event.src_path.endswith('.pdf'):
            return
        
        filename = os.path.basename(event.src_path)
        
        # Avoid processing same file twice
        if filename in self.processed_files:
            return
        
        print(f"\n📄 New PDF detected: {filename}")
        print(f"⏳ Waiting 2 seconds for file to finish uploading...")
        
        # Wait for file to finish writing
        time.sleep(2)
        
        try:
            # Process the PDF
            print(f"🔄 Processing: {filename}")
            order_data = self.pdf_processor.process_pdf(event.src_path)
            
            if order_data:
                # Store in database
                print(f"💾 Storing in database...")
                self.pdf_processor.store_order(order_data)
                
                # Reindex vector store
                print(f"🔍 Reindexing embeddings...")
                self.rag_system.index_sebi_orders(force_reindex=True)
                
                print(f"✅ Successfully processed: {filename}")
                self.processed_files.add(filename)
                
                # Log to file
                log_pdf_processing(filename, "SUCCESS", order_data['company_name'])
            else:
                print(f"❌ Failed to process: {filename}")
                log_pdf_processing(filename, "FAILED", "Unknown")
        
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            log_pdf_processing(filename, "ERROR", str(e))

class AutoPDFProcessor:
    """Main auto-processor class"""
    
    def __init__(self, pdf_folder='sebi_pdfs', db_path='sebi_orders.db'):
        self.pdf_folder = pdf_folder
        self.db_path = db_path
        
        # Initialize components
        self.pdf_processor = SEBIPDFProcessor(db_path)
        self.rag_system = SEBIRAGSystem()
        
        # Create watcher handler
        self.handler = PDFWatcherHandler(self.pdf_processor, self.rag_system)
        
        # Create observer
        self.observer = Observer()
    
    def start(self):
        """Start watching for new PDFs"""
        
        print("\n" + "="*60)
        print("🚀 AUTO PDF PROCESSOR STARTED")
        print("="*60)
        print(f"📁 Watching folder: {self.pdf_folder}")
        print(f"💾 Database: {self.db_path}")
        print(f"🔍 Vector DB: ./chroma_db/")
        print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print("\nWaiting for new PDFs...\n")
        
        # Start observer
        self.observer.schedule(self.handler, self.pdf_folder, recursive=False)
        self.observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop watching"""
        print("\n\n🛑 Stopping auto-processor...")
        self.observer.stop()
        self.observer.join()
        print("✅ Auto-processor stopped")

def log_pdf_processing(filename, status, details):
    """Log PDF processing to file"""
    
    log_file = "pdf_processing_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"[{timestamp}] {status}: {filename} ({details})\n"
    
    with open(log_file, 'a') as f:
        f.write(log_entry)

def main():
    """Main execution"""
    
    # Create sebi_pdfs folder if doesn't exist
    os.makedirs('sebi_pdfs', exist_ok=True)
    
    # Initialize auto-processor
    processor = AutoPDFProcessor()
    
    # Start watching
    processor.start()

if __name__ == '__main__':
    main()