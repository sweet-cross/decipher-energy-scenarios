import PyPDF2
import os
from typing import List, Dict, Optional
import re

class PDFProcessor:
    def __init__(self, reports_path: str):
        self.reports_path = reports_path
        self._cache = {}
        
    def get_available_reports(self) -> List[str]:
        """Get list of available PDF reports."""
        if not os.path.exists(self.reports_path):
            return []
        return [f for f in os.listdir(self.reports_path) if f.endswith('.pdf')]
    
    def extract_text(self, pdf_filename: str) -> str:
        """Extract text from a PDF file."""
        if pdf_filename in self._cache:
            return self._cache[pdf_filename]
            
        pdf_path = os.path.join(self.reports_path, pdf_filename)
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file {pdf_filename} not found")
        
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF {pdf_filename}: {e}")
            return ""
            
        self._cache[pdf_filename] = text
        return text
    
    def search_text(self, query: str, pdf_filename: Optional[str] = None) -> Dict[str, List[str]]:
        """Search for text across PDFs."""
        results = {}
        
        files_to_search = [pdf_filename] if pdf_filename else self.get_available_reports()
        
        for filename in files_to_search:
            try:
                text = self.extract_text(filename)
                # Split text into paragraphs and search
                paragraphs = text.split('\n\n')
                matches = []
                
                for paragraph in paragraphs:
                    if re.search(query, paragraph, re.IGNORECASE):
                        matches.append(paragraph.strip())
                
                if matches:
                    results[filename] = matches
                    
            except Exception as e:
                print(f"Error searching in {filename}: {e}")
                
        return results
    
    def get_document_summary(self, pdf_filename: str) -> Dict[str, any]:
        """Get summary information about a PDF document."""
        pdf_path = os.path.join(self.reports_path, pdf_filename)
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file {pdf_filename} not found")
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                summary = {
                    "filename": pdf_filename,
                    "num_pages": len(pdf_reader.pages),
                    "metadata": pdf_reader.metadata if hasattr(pdf_reader, 'metadata') else {},
                    "text_preview": self.extract_text(pdf_filename)[:500] + "..."
                }
                
                return summary
                
        except Exception as e:
            return {"error": f"Could not process PDF: {e}"}
    
    def extract_key_sections(self, pdf_filename: str, sections: List[str]) -> Dict[str, str]:
        """Extract specific sections from a PDF."""
        text = self.extract_text(pdf_filename)
        sections_found = {}
        
        for section in sections:
            # Simple pattern matching for section headers
            pattern = rf"(?i){section}.*?(?=\n\n[A-Z]|\n\n\d+\.|\Z)"
            matches = re.findall(pattern, text, re.DOTALL)
            
            if matches:
                sections_found[section] = matches[0].strip()
        
        return sections_found