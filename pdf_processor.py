#!/usr/bin/env python3
"""
PDF Processor for SEBI Orders
Extracts text, tables, and metadata from SEBI order PDFs
"""

import os
import re
import sqlite3
from datetime import datetime
import pdfplumber
from pathlib import Path

class SEBIPDFProcessor:
    """Process SEBI order PDFs and extract structured data"""
    
    def __init__(self, db_path='sebi_orders.db'):
        self.db_path = db_path
        self.date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',  # DD-MM-YYYY or MM/DD/YYYY
            r'\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
        ]
        self.company_patterns = [
            r'(?:against|regarding)\s+([A-Za-z\s&]+?)\s+(?:Limited|Ltd|Inc|Company)',
            r'(?:Order against|In the matter of)\s+([A-Za-z\s&]+)',
        ]
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract all text from PDF"""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text += f"\n--- Page {page_num} ---\n"
                    text += page.extract_text() or ""
                    
                    # Extract tables if any
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            for row in table:
                                text += "\n" + " | ".join(str(cell or "") for cell in row)
            
            return text
        except Exception as e:
            print(f"❌ Error extracting text from {pdf_path}: {e}")
            return None
    
    def extract_company_name(self, text):
        """Extract company name from SEBI order text"""
        for pattern in self.company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Clean up common endings
                company = re.sub(r'\s+(Limited|Ltd|Limited|Corporation|Corp)\s*$', 
                               '', company, flags=re.IGNORECASE)
                return company.title()
        
        # Fallback: look for capitalized terms with "Ltd"
        match = re.search(r'([A-Z][A-Za-z\s&]+?)(?:\s+(?:Limited|Ltd|Inc|Company))?', text)
        if match:
            return match.group(1).strip()
        
        return None
    
    def extract_order_date(self, text):
        """Extract order date from SEBI order"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    def extract_order_type(self, text):
        """Classify SEBI order type"""
        text_lower = text.lower()
        
        keywords = {
            'Ban': ['ban', 'prohibited', 'suspension', 'debarred'],
            'Fraud': ['fraud', 'fraudulent', 'deceptive', 'misrepresentation'],
            'Insider Trading': ['insider', 'insider trading', 'unpublished price sensitive'],
            'Ponzi Scheme': ['ponzi', 'illegal scheme', 'pyramid scheme'],
            'Violation': ['violation', 'contravention', 'breach'],
            'Warning': ['warning', 'cautionary'],
            'Investigation': ['investigation', 'enquiry', 'probe'],
            'Settlement': ['settlement', 'agreed settlement'],
        }
        
        for order_type, keywords_list in keywords.items():
            if any(kw in text_lower for kw in keywords_list):
                return order_type
        
        return 'Other'
    
    def assess_risk_level(self, text, order_type):
        """Assess risk level based on content"""
        text_lower = text.lower()
        
        high_risk_keywords = [
            'ban', 'fraud', 'ponzi', 'insider trading', 'prohibited',
            'debarred', 'cancellation', 'criminal prosecution'
        ]
        
        medium_risk_keywords = [
            'warning', 'violation', 'non-compliance', 'settlement',
            'penalty', 'fine', 'investigation'
        ]
        
        if any(kw in text_lower for kw in high_risk_keywords):
            return 'High'
        elif any(kw in text_lower for kw in medium_risk_keywords):
            return 'Medium'
        else:
            return 'Low'
    
    def generate_summary(self, text, max_length=500):
        """Generate brief summary of SEBI order"""
        # Take first meaningful paragraph
        paragraphs = [p.strip() for p in text.split('\n') if p.strip() and len(p) > 50]
        
        summary = ""
        for para in paragraphs[:3]:
            if len(summary) < max_length:
                summary += para + " "
        
        return summary[:max_length].strip()
    
    def extract_nse_bse_codes(self, company_name):
        """Lookup NSE/BSE codes for company (stub - integrate with API later)"""
        # TODO: Integrate with NSE/BSE API or CSV lookup
        return None, None
    
    def process_pdf(self, pdf_path):
        """Complete pipeline: extract all relevant data from PDF"""
        
        print(f"\n📄 Processing: {os.path.basename(pdf_path)}")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return None
        
        # Extract structured data
        company_name = self.extract_company_name(text)
        order_date = self.extract_order_date(text)
        order_type = self.extract_order_type(text)
        risk_level = self.assess_risk_level(text, order_type)
        summary = self.generate_summary(text)
        
        # Create order ID from date and company
        if order_date and company_name:
            order_id = f"SEBI-{order_date.split()[-1]}-{company_name[:3].upper()}"
        else:
            order_id = f"SEBI-{datetime.now().strftime('%Y%m%d')}-{os.path.basename(pdf_path)[:10]}"
        
        order_data = {
            'order_id': order_id,
            'company_name': company_name or 'Unknown',
            'order_date': order_date,
            'order_type': order_type,
            'risk_level': risk_level,
            'summary': summary,
            'full_text': text,
            'pdf_source': os.path.basename(pdf_path)
        }
        
        print(f"  ✓ Company: {order_data['company_name']}")
        print(f"  ✓ Type: {order_data['order_type']}")
        print(f"  ✓ Risk: {order_data['risk_level']}")
        print(f"  ✓ Date: {order_data['order_date']}")
        
        return order_data
    
    def store_order(self, order_data):
        """Store processed order in database"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sebi_orders 
                (order_id, company_name, order_date, order_type, risk_level, summary, full_text, pdf_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_data['order_id'],
                order_data['company_name'],
                order_data['order_date'],
                order_data['order_type'],
                order_data['risk_level'],
                order_data['summary'],
                order_data['full_text'],
                order_data['pdf_source']
            ))
            
            conn.commit()
            print(f"  ✓ Stored in database")
            
            conn.close()
            return True
        
        except sqlite3.IntegrityError as e:
            print(f"  ⚠️  Order already exists: {e}")
            return False
        except Exception as e:
            print(f"  ❌ Error storing order: {e}")
            return False
    
    def batch_process_pdfs(self, pdf_folder):
        """Process all PDFs in a folder"""
        
        if not os.path.exists(pdf_folder):
            print(f"❌ Folder not found: {pdf_folder}")
            return
        
        pdf_files = list(Path(pdf_folder).glob("*.pdf"))
        
        if not pdf_files:
            print(f"❌ No PDF files found in {pdf_folder}")
            return
        
        print(f"\n🚀 Starting batch processing of {len(pdf_files)} PDFs...")
        
        success_count = 0
        for pdf_path in pdf_files:
            order_data = self.process_pdf(str(pdf_path))
            if order_data and self.store_order(order_data):
                success_count += 1
        
        print(f"\n✅ Batch processing complete!")
        print(f"   Processed: {len(pdf_files)} files")
        print(f"   Successfully stored: {success_count} orders")

def main():
    """Main execution"""
    
    # Create sample SEBI PDFs folder if it doesn't exist
    pdf_folder = 'sebi_pdfs'
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)
        print(f"📁 Created folder: {pdf_folder}")
        print("   👉 Place your SEBI order PDF files here")
    
    # Initialize processor
    processor = SEBIPDFProcessor()
    
    # Process PDFs
    processor.batch_process_pdfs(pdf_folder)
    
    print("\n✨ Ready for RAG pipeline!")

if __name__ == '__main__':
    main()
