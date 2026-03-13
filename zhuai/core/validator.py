"""PDF validator module."""

import os
from typing import Optional
import requests
from PyPDF2 import PdfReader
from io import BytesIO


class PDFValidator:
    """Validates PDF files and URLs."""
    
    def __init__(self, timeout: int = 30):
        """Initialize validator.
        
        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; Zhuai/2.0)"
        })
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is accessible.
        
        Args:
            url: URL to check.
            
        Returns:
            True if URL is accessible, False otherwise.
        """
        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            return response.status_code == 200
        except Exception:
            return False
    
    def can_download_pdf(self, url: str) -> bool:
        """Check if PDF can be downloaded from URL.
        
        Args:
            url: PDF URL.
            
        Returns:
            True if PDF can be downloaded, False otherwise.
        """
        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code != 200:
                return False
            
            content_type = response.headers.get("Content-Type", "").lower()
            content_length = response.headers.get("Content-Length")
            
            if "application/pdf" in content_type:
                return True
            
            if content_length and int(content_length) < 1024:
                return False
            
            if url.lower().endswith(".pdf"):
                return True
            
            return False
            
        except Exception:
            return False
    
    def validate_pdf_file(self, file_path: str) -> bool:
        """Validate a local PDF file.
        
        Args:
            file_path: Path to PDF file.
            
        Returns:
            True if file is a valid PDF, False otherwise.
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            if os.path.getsize(file_path) == 0:
                return False
            
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                return len(reader.pages) > 0
                
        except Exception:
            return False
    
    def validate_pdf_content(self, content: bytes) -> bool:
        """Validate PDF content.
        
        Args:
            content: PDF content as bytes.
            
        Returns:
            True if content is valid PDF, False otherwise.
        """
        try:
            if len(content) < 4:
                return False
            
            if content[:4] != b"%PDF":
                return False
            
            reader = PdfReader(BytesIO(content))
            return len(reader.pages) > 0
            
        except Exception:
            return False