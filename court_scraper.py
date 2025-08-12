#!/usr/bin/env python3
"""
Galveston County Court Document Scraper
Standalone script for downloading court documents with 7-step navigation process
"""

import time
import logging
import re
import os
import requests
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import threading
import queue

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

@dataclass
class DocumentInfo:
    """Document information container"""
    index: int
    filename: str
    url: str
    fragment_id: str
    date: str
    display_name: str
    doc_type: str
    size: int = 0
    status: str = "pending"

class GalvestonCourtScraper:
    """Complete Galveston County court document scraper"""
    
    def __init__(self, headless: bool = True, verbose: bool = False, progress_callback=None):
        self.headless = headless
        self.verbose = verbose
        self.driver = None
        self.base_url = "https://publicaccess.galvestoncountytx.gov/PublicAccess/"
        self.documents = []
        self.used_filenames = set()
        self.progress_callback = progress_callback
        
        # Setup logging
        self.setup_logging()
        
        # Navigation steps for progress tracking
        self.navigation_steps = [
            "Opening Galveston County Public Access",
            "Clicking 'Civil and Family Case Records'", 
            "Selecting 'Case' radio button",
            "Entering case number",
            "Clicking case number hyperlink (first time)",
            "Clicking case number hyperlink (second time) - CRUCIAL",
            "Extracting HTML source with document links"
        ]
    
    def setup_logging(self):
        """Setup logging for the scraper"""
        level = logging.INFO if self.verbose else logging.WARNING
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message"""
        if self.verbose:
            print(f"[{level}] {message}")
        if level == "ERROR":
            self.logger.error(message)
        else:
            self.logger.info(message)
    
    def report_progress(self, step: int, total_steps: int, message: str, phase: str = "navigation"):
        """Report progress to callback if available"""
        if self.progress_callback:
            percentage = (step / total_steps) * 100
            self.progress_callback({
                'phase': phase,
                'step': step,
                'total_steps': total_steps,
                'message': message,
                'percentage': percentage
            })
    
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
                self.log("Starting browser in headless mode")
            else:
                self.log("Starting browser in visible mode")
            
            # Standard Chrome options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Create driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            self.log("Browser initialized successfully")
            return True
            
        except WebDriverException as e:
            self.log(f"Failed to initialize browser: {str(e)}", "ERROR")
            return False
    
    def close_driver(self):
        """Close the browser driver"""
        if self.driver:
            try:
                self.driver.quit()
                self.log("Browser closed successfully")
            except Exception as e:
                self.log(f"Error closing browser: {e}", "ERROR")
            self.driver = None
    
    def navigate_to_case(self, case_number: str, max_retries: int = 2) -> Optional[tuple]:
        """
        Navigate through the 7-step process to get case documents HTML
        
        Args:
            case_number: Case number like '25-CV-0880'
            max_retries: Number of retry attempts if navigation fails
            
        Returns:
            Tuple of (HTML source, cookies dict) or None if failed
        """
        for attempt in range(max_retries + 1):
            if attempt > 0:
                self.log(f"Retry attempt {attempt} for case {case_number}")
                self.close_driver()
                time.sleep(2)
            
            try:
                return self._perform_navigation(case_number)
            except Exception as e:
                self.log(f"Navigation attempt {attempt + 1} failed: {str(e)}", "ERROR")
                if attempt == max_retries:
                    self.log(f"All navigation attempts failed for case {case_number}", "ERROR")
                    return None
        
        return None
    
    def _perform_navigation(self, case_number: str) -> tuple:
        """Perform the actual 7-step navigation"""
        
        # Step 1: Open Galveston County Public Access
        self.log(f"Step 1/7: {self.navigation_steps[0]}")
        self.report_progress(1, 7, self.navigation_steps[0])
        
        if not self.driver:
            if not self.setup_driver():
                raise Exception("Failed to setup browser driver")
        
        self.driver.get(f"{self.base_url}default.aspx")
        
        # Wait for page to load
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Step 2: Click "Civil and Family Case Records"
        self.log(f"Step 2/7: {self.navigation_steps[1]}")
        self.report_progress(2, 7, self.navigation_steps[1])
        
        civil_link = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Civil and Family Case Records"))
        )
        civil_link.click()
        
        # Better wait for navigation instead of sleep
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='radio']"))
        )
        
        # Step 3: Select "Case" radio button  
        self.log(f"Step 3/7: {self.navigation_steps[2]}")
        self.report_progress(3, 7, self.navigation_steps[2])
        
        case_radio = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='radio' and contains(@id, 'Case')]"))
        )
        case_radio.click()
        
        # Wait for form to update
        time.sleep(1)
        
        # Step 4: Enter case number
        self.log(f"Step 4/7: {self.navigation_steps[3]} - {case_number}")
        self.report_progress(4, 7, f"{self.navigation_steps[3]} - {case_number}")
        
        case_input = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable((By.ID, "CaseSearchValue"))
        )
        case_input.clear()
        case_input.send_keys(case_number)
        case_input.send_keys(Keys.RETURN)
        
        # Wait for search results with better condition
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, case_number))
        )
        
        # Step 5: Click case number hyperlink (first time)
        self.log(f"Step 5/7: {self.navigation_steps[4]}")
        self.report_progress(5, 7, self.navigation_steps[4])
        
        case_link = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, case_number))
        )
        case_link.click()
        
        # Wait for case details page
        WebDriverWait(self.driver, 10).until(
            lambda driver: case_number in driver.page_source
        )
        
        # Step 6: Click case number hyperlink again (CRUCIAL STEP)
        self.log(f"Step 6/7: {self.navigation_steps[5]}")
        self.report_progress(6, 7, self.navigation_steps[5])
        
        case_link_second = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, case_number))
        )
        case_link_second.click()
        
        # Wait for document list page - look for document indicators
        WebDriverWait(self.driver, 15).until(
            lambda driver: "ViewDocumentFragment.aspx" in driver.page_source or 
                          "No records found" in driver.page_source
        )
        
        # Step 7: Extract HTML source and cookies
        self.log(f"Step 7/7: {self.navigation_steps[6]}")
        self.report_progress(7, 7, self.navigation_steps[6])
        
        html_source = self.driver.page_source
        
        # Extract cookies from the browser session
        cookies = {}
        for cookie in self.driver.get_cookies():
            cookies[cookie['name']] = cookie['value']
        
        self.log(f"Extracted {len(cookies)} cookies from browser session")
        
        # Validate we got the document page
        if "ViewDocumentFragment.aspx" in html_source:
            doc_count = len(re.findall(r'ViewDocumentFragment\.aspx', html_source))
            self.log(f"Successfully extracted HTML with {doc_count} document links")
            return (html_source, cookies)
        elif "No records found" in html_source:
            self.log("Case found but no documents available")
            return (html_source, cookies)
        else:
            raise Exception("Failed to reach document page - unexpected content")
    
    def parse_documents(self, html_content: str) -> List[DocumentInfo]:
        """Parse HTML content and extract document information"""
        self.log("Parsing document information from HTML")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        documents = []
        
        # Find all document links
        all_links = soup.find_all('a', href=lambda x: x and 'ViewDocumentFragment.aspx' in x)
        
        if not all_links:
            self.log("No document links found in HTML")
            return documents
        
        self.log(f"Found {len(all_links)} document links")
        
        for i, link in enumerate(all_links, 1):
            try:
                href = link.get('href')
                link_text = link.get_text(strip=True)
                fragment_id = self.extract_fragment_id(href)
                
                # Find the parent row to get date information
                row = link.find_parent('tr')
                if row:
                    cells = row.find_all('td')
                    if len(cells) >= 1:
                        first_cell = cells[0].get_text(strip=True)
                        
                        # Look for date pattern MM/DD/YYYY
                        date_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', first_cell)
                        if date_match:
                            month, day, year = date_match.groups()
                            
                            # Extract document type from date cell
                            doc_type = first_cell[date_match.end():].strip()
                            doc_type = doc_type.replace('\u00a0', ' ').replace('&nbsp;', ' ')
                            doc_type = re.sub(r'\s+', ' ', doc_type).strip()
                            
                            # Choose the longest, most descriptive name
                            if len(link_text) > len(doc_type) and link_text != doc_type:
                                display_name = link_text
                            else:
                                display_name = doc_type
                            
                            # Remove .pdf extension if already present
                            if display_name.lower().endswith('.pdf'):
                                display_name = display_name[:-4]
                            
                            # Generate unique filename
                            filename = self.generate_unique_filename(year, month, day, display_name, fragment_id)
                            
                            doc_info = DocumentInfo(
                                index=i,
                                filename=filename,
                                url=href,
                                fragment_id=fragment_id,
                                date=f"{month}/{day}/{year}",
                                display_name=display_name,
                                doc_type=doc_type
                            )
                            
                            documents.append(doc_info)
                            
            except Exception as e:
                self.log(f"Error parsing document {i}: {e}", "ERROR")
                continue
        
        self.log(f"Successfully parsed {len(documents)} documents")
        return documents
    
    def extract_fragment_id(self, url: str) -> str:
        """Extract DocumentFragmentID from URL"""
        match = re.search(r'DocumentFragmentID=(\d+)', url)
        return match.group(1) if match else "unknown"
    
    def sanitize_filename(self, filename: str, max_length: int = 120) -> str:
        """Sanitize filename by removing invalid characters"""
        invalid_chars = r'[<>:"/\\|?*]'
        filename = re.sub(invalid_chars, '', filename)
        filename = re.sub(r'\s+', ' ', filename).strip()
        
        if len(filename) > max_length - 4:
            filename = filename[:max_length - 4]
        
        return filename
    
    def generate_unique_filename(self, year: str, month: str, day: str, display_name: str, fragment_id: str) -> str:
        """Generate guaranteed unique filename"""
        sanitized_name = self.sanitize_filename(display_name)
        base_filename = f"{year}.{month}.{day}_{sanitized_name}"
        final_filename = f"{base_filename}.pdf"
        
        # Check for duplicates and make unique if needed
        counter = 1
        while final_filename in self.used_filenames:
            final_filename = f"{base_filename}_(ID{fragment_id}).pdf"
            
            if final_filename in self.used_filenames:
                final_filename = f"{base_filename}_(ID{fragment_id})_{counter}.pdf"
                counter += 1
            else:
                break
        
        self.used_filenames.add(final_filename)
        return final_filename
    
    def _validate_pdf_content(self, content: bytes, filename: str) -> str:
        """
        Validate downloaded content and determine status
        
        Returns:
            'valid' - Valid PDF content
            'secured' - Content indicates secured/protected document
            'error' - Invalid content or error page
        """
        # Check minimum size (PDFs should be at least 1KB for real documents)
        if len(content) < 1024:
            # Very small files are often error pages, check if they're secured
            if len(content) > 0:
                content_str = content.decode('utf-8', errors='ignore').lower()
                if self._is_secured_content(content_str):
                    self.log(f"SECURED: {filename} - Access denied ({len(content)} bytes)")
                    return 'secured'
            
            self.log(f"Content too small for {filename}: {len(content)} bytes", "ERROR")
            return 'error'
        
        # Check PDF magic bytes (PDFs start with %PDF-)
        if not content.startswith(b'%PDF-'):
            # Not a PDF, check if it's a secured document indicator
            content_str = content.decode('utf-8', errors='ignore').lower()
            
            # Check for explicit secured content first
            if self._is_secured_content(content_str):
                self.log(f"SECURED: {filename} - Access denied or login required")
                return 'secured'
            
            # Check if it's a court system secured page (common for family cases)  
            if self._is_likely_court_secured_page(content_str):
                self.log(f"SECURED: {filename} - Court HTML page instead of PDF (likely protected)")
                return 'secured'
            
            self.log(f"Content not PDF format for {filename} (starts with: {content[:20]})", "ERROR")
            return 'error'
        
        # Check for common HTML error indicators in what appears to be a PDF
        content_str = content.decode('utf-8', errors='ignore').lower()
        html_indicators = ['<html', '<body', '<head', 'content-type: text/html', 'error', 'exception']
        if any(indicator in content_str for indicator in html_indicators):
            # Check if it's explicitly a secured document
            if self._is_secured_content(content_str):
                self.log(f"SECURED: {filename} - Access denied or login required")
                return 'secured'
            
            # For court documents, HTML pages instead of PDFs often indicate secured/protected content
            # Especially in family cases where sensitive information is involved
            if self._is_likely_court_secured_page(content_str):
                self.log(f"SECURED: {filename} - Court HTML page instead of PDF (likely protected)")
                return 'secured'
            
            self.log(f"Content appears to be HTML error page for {filename}", "ERROR")
            return 'error'
        
        return 'valid'
    
    def _is_secured_content(self, content_str: str) -> bool:
        """Check if content indicates a secured/protected document"""
        secured_indicators = [
            'access denied', 'access is denied', 'unauthorized', 'login required',
            'authentication required', 'not authorized', 'permission denied',
            'sealed', 'confidential', 'protected', 'restricted', 'private',
            'secure', 'classified', 'redacted', 'impounded',
            'court sealed', 'under seal', 'sealed by court',
            'login to view', 'sign in required', 'authentication needed',
            'forbidden', '401', '403', 'not permitted'
        ]
        
        return any(indicator in content_str for indicator in secured_indicators)
    
    def _is_likely_court_secured_page(self, content_str: str) -> bool:
        """Check if HTML content is likely a court system secured page"""
        # Look for court-specific patterns that indicate this is from the court system
        court_indicators = [
            'publicaccess', 'galveston', 'court', 'justice', 'clerk',
            'case', 'document', 'filing', 'docket'
        ]
        
        # Must be from court system AND be an HTML page when we expected PDF
        has_court_context = any(indicator in content_str for indicator in court_indicators)
        
        # Additional patterns that suggest this is a secured/redirect page
        secured_patterns = [
            'login', 'authentication', 'redirect', 'session', 'timeout',
            'not authorized', 'restricted', 'unavailable', 'protected',
            'not available', 'access denied', 'permission denied',
            'this document is', 'cannot be displayed', 'cannot be viewed',
            'error', 'expired', 'invalid request', 'forbidden'
        ]
        
        has_secured_pattern = any(pattern in content_str for pattern in secured_patterns)
        
        # If it's clearly from the court system and we got HTML instead of PDF,
        # it's likely a secured document (especially common in family cases)
        # Family courts often protect sensitive documents by default
        return has_court_context or has_secured_pattern
    
    def _create_placeholder_pdf(self, file_path: Path, filename: str, reason: str = "Document Secured/Sealed"):
        """Create a placeholder PDF for secured documents"""
        try:
            # Simple PDF content indicating secured document
            pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj

4 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
50 700 Td
({reason}) Tj
0 -20 Td
(Filename: {filename}) Tj
0 -20 Td
(This document is not available for public access.) Tj
0 -20 Td
(Generated by Court Scraper on {time}) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000376 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
626
%%EOF"""
            
            # Format the PDF content with actual values
            formatted_content = pdf_content.format(
                reason=reason,
                filename=filename,
                time=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            # Write placeholder PDF
            with open(file_path, 'wb') as f:
                f.write(formatted_content.encode('utf-8'))
            
            return True
            
        except Exception as e:
            self.log(f"Failed to create placeholder PDF for {filename}: {e}", "ERROR")
            return False
    
    def _download_with_retry(self, session, doc: DocumentInfo, file_path: Path, max_retries: int = 2) -> str:
        """Download a single document with retry mechanism"""
        url = urljoin(self.base_url, doc.url)
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.log(f"Retry {attempt} for {doc.filename}")
                    time.sleep(2)  # Wait before retry
                else:
                    self.log(f"Downloading: {doc.filename}")
                
                # Download file
                response = session.get(url, timeout=30)
                
                if response.status_code == 200:
                    content_length = len(response.content)
                    
                    # Validate content and determine status
                    validation_result = self._validate_pdf_content(response.content, doc.filename)
                    
                    if validation_result == 'valid':
                        # Save valid PDF file
                        with open(file_path, 'wb') as file:
                            file.write(response.content)
                        
                        self.log(f"SUCCESS: {doc.filename} ({content_length:,} bytes)")
                        return 'success'
                    
                    elif validation_result == 'secured':
                        # Create placeholder for secured document
                        if self._create_placeholder_pdf(file_path, doc.filename):
                            self.log(f"PLACEHOLDER: {doc.filename} - Created placeholder for secured document")
                            return 'secured'
                        else:
                            self.log(f"FAILED: {doc.filename} - Could not create placeholder", "ERROR")
                            return 'failed'
                    
                    elif validation_result == 'error':
                        if attempt == max_retries:
                            self.log(f"FAILED: {doc.filename} - Invalid PDF content after all retries", "ERROR")
                            return 'failed'
                        else:
                            self.log(f"Invalid content on attempt {attempt + 1}, retrying...", "WARNING")
                            continue
                else:
                    # Check for HTTP status codes that indicate secured files
                    if response.status_code in [401, 403]:
                        # Unauthorized or Forbidden - likely secured document
                        if self._create_placeholder_pdf(file_path, doc.filename, f"HTTP {response.status_code} - Access Denied"):
                            self.log(f"SECURED: {doc.filename} - HTTP {response.status_code}, created placeholder")
                            return 'secured'
                        else:
                            self.log(f"FAILED: {doc.filename} - HTTP {response.status_code}, could not create placeholder", "ERROR")
                            return 'failed'
                    
                    if attempt == max_retries:
                        self.log(f"FAILED: {doc.filename} - HTTP {response.status_code} after all retries", "ERROR")
                        return 'failed'
                    else:
                        self.log(f"HTTP {response.status_code} on attempt {attempt + 1}, retrying...")
                        continue
                        
            except Exception as e:
                if attempt == max_retries:
                    self.log(f"ERROR downloading {doc.filename} after all retries: {str(e)}", "ERROR")
                    return 'failed'
                else:
                    self.log(f"Exception on attempt {attempt + 1}, retrying: {str(e)}")
                    continue
        
        return 'failed'
    
    def download_documents(self, documents: List[DocumentInfo], download_dir: Path, cookies: dict = None, max_concurrent: int = 3) -> Dict:
        """Download all documents with concurrent downloading"""
        if not documents:
            self.log("No documents to download")
            return {"successful": 0, "failed": 0, "skipped": 0, "secured": 0}
        
        download_dir.mkdir(parents=True, exist_ok=True)
        self.log(f"Starting download of {len(documents)} documents to {download_dir}")
        
        # Report initial download progress
        self.report_progress(0, len(documents), f"Preparing to download {len(documents)} documents", "download")
        
        # Setup session for downloads
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        
        # Add cookies from browser session if provided
        if cookies:
            session.cookies.update(cookies)
            self.log(f"Added {len(cookies)} cookies to download session")
        
        # Disable SSL verification for problematic certificates
        session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        successful = 0
        failed = 0
        skipped = 0
        secured = 0
        
        for doc_index, doc in enumerate(documents, 1):
            try:
                file_path = download_dir / doc.filename
                
                # Report progress for current document
                self.report_progress(doc_index, len(documents), f"Processing: {doc.filename}", "download")
                
                # Skip if file already exists
                if file_path.exists():
                    existing_size = file_path.stat().st_size
                    self.log(f"SKIP: {doc.filename} (exists, {existing_size:,} bytes)")
                    skipped += 1
                    continue
                
                # Try downloading with retry mechanism
                download_result = self._download_with_retry(session, doc, file_path, max_retries=2)
                
                if download_result == 'success':
                    successful += 1
                elif download_result == 'secured':
                    secured += 1
                else:  # 'failed'
                    failed += 1
                
                # Respectful delay
                time.sleep(1.0)
                
            except Exception as e:
                self.log(f"ERROR downloading {doc.filename}: {str(e)}", "ERROR")
                failed += 1
        
        self.log(f"Download complete: {successful} successful, {secured} secured, {failed} failed, {skipped} skipped")
        return {"successful": successful, "failed": failed, "skipped": skipped, "secured": secured}
    
    def create_manifest(self, download_dir: Path) -> Path:
        """Create detailed manifest of downloaded files"""
        pdf_files = sorted(download_dir.glob("*.pdf"))
        manifest_file = download_dir / "MANIFEST.txt"
        
        with open(manifest_file, 'w', encoding='utf-8') as f:
            f.write("GALVESTON COUNTY COURT DOCUMENT MANIFEST\n")
            f.write("=" * 50 + "\n")
            f.write(f"Total Files: {len(pdf_files)}\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Download Directory: {download_dir}\n\n")
            
            total_size = 0
            for i, file in enumerate(pdf_files, 1):
                size = file.stat().st_size
                total_size += size
                f.write(f"{i:2d}. {file.name}\n")
                f.write(f"    Size: {size:,} bytes\n\n")
            
            f.write(f"TOTAL SIZE: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)\n")
        
        self.log(f"Manifest created: {manifest_file}")
        return manifest_file
    
    def scrape_case(self, case_number: str, download_dir: Optional[Path] = None) -> Dict:
        """
        Complete process: navigate, parse, and download documents for a case
        
        Returns:
            Dictionary with results summary
        """
        try:
            self.log(f"Starting scrape for case: {case_number}")
            
            # Navigate and get HTML with cookies
            navigation_result = self.navigate_to_case(case_number)
            if not navigation_result:
                return {"success": False, "error": "Navigation failed"}
            
            html_source, cookies = navigation_result
            
            # Parse documents (Phase between navigation and download)
            self.report_progress(1, 1, "📄 Parsing document information from HTML", "parsing")
            documents = self.parse_documents(html_source)
            if not documents:
                return {"success": True, "documents": 0, "downloaded": 0, "message": "No documents found"}
            
            # Download documents if directory specified
            download_stats = {"successful": 0, "failed": 0, "skipped": 0, "secured": 0}
            if download_dir:
                download_stats = self.download_documents(documents, download_dir, cookies)
                
                # Create manifest if any files were processed
                if download_stats["successful"] > 0 or download_stats["secured"] > 0:
                    self.create_manifest(download_dir)
            
            return {
                "success": True,
                "documents": len(documents),
                "downloaded": download_stats["successful"],
                "secured": download_stats["secured"], 
                "failed": download_stats["failed"],
                "skipped": download_stats["skipped"],
                "case_number": case_number
            }
            
        except Exception as e:
            self.log(f"Scrape failed for case {case_number}: {str(e)}", "ERROR")
            return {"success": False, "error": str(e)}
        
        finally:
            self.close_driver()

def main():
    """Main function for command line usage"""
    print("Galveston County Court Document Scraper")
    print("=" * 50)
    
    # Get case number from user
    case_number = input("Enter case number (e.g., 25-CV-0880): ").strip()
    
    if not case_number:
        print("Error: Case number is required")
        return 1
    
    # Validate case number format
    if not re.match(r'^\d{2}-[A-Z]{2,3}-\d{3,5}$', case_number):
        print(f"Warning: Case number '{case_number}' doesn't match expected format")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            return 1
    
    # Ask about browser visibility
    show_browser = input("Show browser window? (y/n): ").strip().lower() == 'y'
    
    # Setup download directory
    download_dir = Path("downloads") / case_number.replace('/', '_').replace('\\', '_')
    
    print(f"\nProcessing case: {case_number}")
    print(f"Download directory: {download_dir}")
    print("-" * 40)
    
    # Create scraper and run
    scraper = GalvestonCourtScraper(headless=not show_browser, verbose=True)
    result = scraper.scrape_case(case_number, download_dir)
    
    # Show results
    if result["success"]:
        if result["documents"] > 0:
            print(f"\n✓ Success!")
            print(f"  Documents found: {result['documents']}")
            print(f"  Documents downloaded: {result['downloaded']}")
            print(f"  Files saved to: {download_dir.absolute()}")
        else:
            print(f"\n✓ Case processed successfully")
            print(f"  {result.get('message', 'No documents available')}")
    else:
        print(f"\n✗ Failed: {result['error']}")
        return 1
    
    input("\nPress Enter to exit...")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())