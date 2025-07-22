#!/usr/bin/env python3
"""
Backend API Testing for Steinmetz App
Tests all backend functionality including PDF upload, text extraction, and search APIs
"""

import requests
import json
import base64
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://9ee8185c-291b-4204-a599-bfaa2b775a7e.preview.emergentagent.com/api"

class SteinmetzBackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.uploaded_order_ids = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
    
    def create_test_pdf(self, content_text):
        """Create a test PDF with German content"""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add content to PDF
        p.drawString(100, 750, "Steinmetz Auftrag")
        p.drawString(100, 720, "=" * 30)
        
        y_position = 680
        for line in content_text.split('\n'):
            if line.strip():
                p.drawString(100, y_position, line)
                y_position -= 20
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
    
    def test_api_root(self):
        """Test the root API endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/")
            if response.status_code == 200:
                data = response.json()
                if "Steinmetz" in data.get("message", ""):
                    self.log_result("API Root", True, "Root endpoint accessible")
                    return True
                else:
                    self.log_result("API Root", False, "Unexpected response message", data)
                    return False
            else:
                self.log_result("API Root", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("API Root", False, f"Connection error: {str(e)}")
            return False
    
    def test_pdf_upload_valid(self):
        """Test PDF upload with valid German content"""
        try:
            # Create test PDF with German content
            pdf_content = """
Auftragsnummer: A-2023-001
Kunde: Max Mustermann
Steinart: Granit
Beschreibung: Grabstein aus schwarzem Granit
Datum: 15.03.2023
"""
            pdf_bytes = self.create_test_pdf(pdf_content)
            
            # Upload PDF
            files = {'file': ('test_auftrag.pdf', pdf_bytes, 'application/pdf')}
            response = requests.post(f"{self.backend_url}/upload-pdf", files=files)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("order_id") and "extracted_info" in data:
                    extracted = data["extracted_info"]
                    self.uploaded_order_ids.append(data["order_id"])
                    
                    # Verify extraction worked
                    if (extracted.get("order_number") != "Nicht erkannt" and
                        extracted.get("customer_name") != "Nicht erkannt" and
                        extracted.get("stone_type") != "Nicht erkannt"):
                        self.log_result("PDF Upload Valid", True, "PDF uploaded and processed successfully", extracted)
                        return True
                    else:
                        self.log_result("PDF Upload Valid", False, "Text extraction failed", extracted)
                        return False
                else:
                    self.log_result("PDF Upload Valid", False, "Missing required response fields", data)
                    return False
            else:
                self.log_result("PDF Upload Valid", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("PDF Upload Valid", False, f"Error: {str(e)}")
            return False
    
    def test_pdf_upload_invalid_file(self):
        """Test PDF upload with non-PDF file"""
        try:
            # Create a text file instead of PDF
            text_content = b"This is not a PDF file"
            files = {'file': ('test.txt', text_content, 'text/plain')}
            response = requests.post(f"{self.backend_url}/upload-pdf", files=files)
            
            if response.status_code == 400:
                self.log_result("PDF Upload Invalid File", True, "Correctly rejected non-PDF file")
                return True
            else:
                self.log_result("PDF Upload Invalid File", False, f"Should reject non-PDF, got HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("PDF Upload Invalid File", False, f"Error: {str(e)}")
            return False
    
    def test_text_extraction_patterns(self):
        """Test text extraction with various German patterns"""
        try:
            # Test different German patterns
            test_cases = [
                {
                    "content": "Auftragsnummer: B-2023-002\nKunde: Anna Schmidt\nSteinart: Marmor",
                    "expected_order": "B-2023-002",
                    "expected_customer": "Anna Schmidt",
                    "expected_stone": "Marmor"
                },
                {
                    "content": "Auftrag: C-2023-003\nAuftraggeber: Hans Mueller\nMaterial: Kalkstein",
                    "expected_order": "C-2023-003", 
                    "expected_customer": "Hans Mueller",
                    "expected_stone": "Kalkstein"
                }
            ]
            
            all_passed = True
            for i, test_case in enumerate(test_cases):
                pdf_bytes = self.create_test_pdf(test_case["content"])
                files = {'file': (f'pattern_test_{i}.pdf', pdf_bytes, 'application/pdf')}
                response = requests.post(f"{self.backend_url}/upload-pdf", files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    extracted = data["extracted_info"]
                    self.uploaded_order_ids.append(data["order_id"])
                    
                    # Check if patterns were extracted correctly
                    order_match = test_case["expected_order"] in extracted.get("order_number", "")
                    customer_match = test_case["expected_customer"] in extracted.get("customer_name", "")
                    stone_match = test_case["expected_stone"] in extracted.get("stone_type", "")
                    
                    if order_match and customer_match and stone_match:
                        self.log_result(f"Pattern Extraction {i+1}", True, f"All patterns extracted correctly", extracted)
                    else:
                        self.log_result(f"Pattern Extraction {i+1}", False, f"Pattern extraction failed", {
                            "expected": test_case,
                            "extracted": extracted
                        })
                        all_passed = False
                else:
                    self.log_result(f"Pattern Extraction {i+1}", False, f"Upload failed: HTTP {response.status_code}")
                    all_passed = False
            
            return all_passed
        except Exception as e:
            self.log_result("Text Extraction Patterns", False, f"Error: {str(e)}")
            return False
    
    def test_search_by_order_number(self):
        """Test search by order number"""
        try:
            search_data = {
                "search_term": "A-2023",
                "search_type": "order_number"
            }
            response = requests.post(f"{self.backend_url}/search-orders", json=search_data)
            
            if response.status_code == 200:
                data = response.json()
                if "results" in data and "count" in data:
                    self.log_result("Search by Order Number", True, f"Found {data['count']} results", data["count"])
                    return True
                else:
                    self.log_result("Search by Order Number", False, "Missing results or count fields", data)
                    return False
            else:
                self.log_result("Search by Order Number", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Search by Order Number", False, f"Error: {str(e)}")
            return False
    
    def test_search_by_customer_name(self):
        """Test search by customer name"""
        try:
            search_data = {
                "search_term": "Max",
                "search_type": "customer_name"
            }
            response = requests.post(f"{self.backend_url}/search-orders", json=search_data)
            
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    self.log_result("Search by Customer Name", True, f"Found {data['count']} results")
                    return True
                else:
                    self.log_result("Search by Customer Name", False, "Missing results field", data)
                    return False
            else:
                self.log_result("Search by Customer Name", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Search by Customer Name", False, f"Error: {str(e)}")
            return False
    
    def test_search_by_stone_type(self):
        """Test search by stone type"""
        try:
            search_data = {
                "search_term": "Granit",
                "search_type": "stone_type"
            }
            response = requests.post(f"{self.backend_url}/search-orders", json=search_data)
            
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    self.log_result("Search by Stone Type", True, f"Found {data['count']} results")
                    return True
                else:
                    self.log_result("Search by Stone Type", False, "Missing results field", data)
                    return False
            else:
                self.log_result("Search by Stone Type", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Search by Stone Type", False, f"Error: {str(e)}")
            return False
    
    def test_search_all_fields(self):
        """Test search across all fields"""
        try:
            search_data = {
                "search_term": "2023",
                "search_type": "all"
            }
            response = requests.post(f"{self.backend_url}/search-orders", json=search_data)
            
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    self.log_result("Search All Fields", True, f"Found {data['count']} results")
                    return True
                else:
                    self.log_result("Search All Fields", False, "Missing results field", data)
                    return False
            else:
                self.log_result("Search All Fields", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Search All Fields", False, f"Error: {str(e)}")
            return False
    
    def test_get_all_orders(self):
        """Test GET all orders"""
        try:
            response = requests.get(f"{self.backend_url}/orders")
            
            if response.status_code == 200:
                data = response.json()
                if "orders" in data and isinstance(data["orders"], list):
                    self.log_result("Get All Orders", True, f"Retrieved {len(data['orders'])} orders")
                    return True
                else:
                    self.log_result("Get All Orders", False, "Invalid response format", data)
                    return False
            else:
                self.log_result("Get All Orders", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Get All Orders", False, f"Error: {str(e)}")
            return False
    
    def test_get_single_order(self):
        """Test GET single order by ID"""
        try:
            if not self.uploaded_order_ids:
                self.log_result("Get Single Order", False, "No uploaded orders to test with")
                return False
            
            order_id = self.uploaded_order_ids[0]
            response = requests.get(f"{self.backend_url}/order/{order_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == order_id:
                    self.log_result("Get Single Order", True, "Successfully retrieved order by ID")
                    return True
                else:
                    self.log_result("Get Single Order", False, "Order ID mismatch", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Get Single Order", False, "Order not found - possible database issue")
                return False
            else:
                self.log_result("Get Single Order", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Get Single Order", False, f"Error: {str(e)}")
            return False
    
    def test_delete_order(self):
        """Test DELETE order"""
        try:
            if not self.uploaded_order_ids:
                self.log_result("Delete Order", False, "No uploaded orders to test with")
                return False
            
            # Use the last uploaded order for deletion test
            order_id = self.uploaded_order_ids[-1]
            response = requests.delete(f"{self.backend_url}/order/{order_id}")
            
            if response.status_code == 200:
                data = response.json()
                if "erfolgreich gelöscht" in data.get("message", ""):
                    self.log_result("Delete Order", True, "Successfully deleted order")
                    self.uploaded_order_ids.remove(order_id)
                    return True
                else:
                    self.log_result("Delete Order", False, "Unexpected response message", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Delete Order", False, "Order not found for deletion")
                return False
            else:
                self.log_result("Delete Order", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Delete Order", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("STEINMETZ BACKEND API TESTING")
        print("=" * 60)
        print(f"Backend URL: {self.backend_url}")
        print()
        
        # Test sequence
        tests = [
            ("API Root", self.test_api_root),
            ("PDF Upload Valid", self.test_pdf_upload_valid),
            ("PDF Upload Invalid File", self.test_pdf_upload_invalid_file),
            ("Text Extraction Patterns", self.test_text_extraction_patterns),
            ("Search by Order Number", self.test_search_by_order_number),
            ("Search by Customer Name", self.test_search_by_customer_name),
            ("Search by Stone Type", self.test_search_by_stone_type),
            ("Search All Fields", self.test_search_all_fields),
            ("Get All Orders", self.test_get_all_orders),
            ("Get Single Order", self.test_get_single_order),
            ("Delete Order", self.test_delete_order),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\nRunning: {test_name}")
            print("-" * 40)
            if test_func():
                passed += 1
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Print detailed results
        print("\nDETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return passed == total

if __name__ == "__main__":
    tester = SteinmetzBackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)