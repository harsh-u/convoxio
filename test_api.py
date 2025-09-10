#!/usr/bin/env python3
"""
WhatsApp Business API Test Script
Tests all API endpoints to ensure they're working correctly
"""

import requests
import json
import sys
from datetime import datetime

class APITester:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.user_data = None
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
        
    def test_endpoint(self, method, endpoint, data=None, files=None):
        """Test a single API endpoint"""
        url = f"{self.base_url}/api{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                if files:
                    response = self.session.post(url, files=files)
                else:
                    response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            result = response.json()
            
            if response.status_code < 400 and result.get('success', True):
                self.log(f"✅ {method} {endpoint} - SUCCESS", "PASS")
                return result
            else:
                self.log(f"❌ {method} {endpoint} - {result.get('error', 'Unknown error')}", "FAIL")
                return None
                
        except Exception as e:
            self.log(f"💥 {method} {endpoint} - Exception: {str(e)}", "ERROR")
            return None
    
    def run_tests(self):
        """Run comprehensive API tests"""
        self.log("🚀 Starting WhatsApp Business API Tests")
        
        # Test 1: User Registration
        self.log("\n📝 Testing Authentication APIs")
        register_data = {
            "business_name": "Test Business",
            "email": f"test_{datetime.now().timestamp()}@example.com",
            "phone_number": "919876543210",
            "password": "testpass123"
        }
        
        result = self.test_endpoint('POST', '/auth/register', register_data)
        if result:
            self.user_data = result.get('user')
            
        # Test 2: User Login (with same credentials)
        login_data = {
            "email": register_data['email'],
            "password": register_data['password']
        }
        self.test_endpoint('POST', '/auth/login', login_data)
        
        # Test 3: Get User Status
        self.test_endpoint('GET', '/auth/user/status')
        
        # Test 4: Dashboard APIs
        self.log("\n📊 Testing Dashboard APIs")
        self.test_endpoint('GET', '/dashboard')
        self.test_endpoint('GET', '/quick-stats')
        
        # Test 5: Template APIs
        self.log("\n📝 Testing Template APIs")
        self.test_endpoint('GET', '/templates')
        self.test_endpoint('GET', '/templates/approved')
        
        # Create a test template
        template_data = {
            "name": f"test_template_{int(datetime.now().timestamp())}",
            "language": "en_US",
            "content": "Hello {{name}}, this is a test message!",
            "category": "TRANSACTIONAL"
        }
        template_result = self.test_endpoint('POST', '/templates', template_data)
        
        # Test 6: Onboarding APIs
        self.log("\n⚙️ Testing Onboarding APIs")
        self.test_endpoint('GET', '/onboard/status')
        self.test_endpoint('POST', '/onboard/start')
        
        # Simple setup test
        setup_data = {
            "whatsapp_number": "919876543210",
            "otp": "123456"
        }
        self.test_endpoint('POST', '/onboard/simple-setup', setup_data)
        
        # Test 7: File Upload APIs
        self.log("\n📁 Testing File Upload APIs")
        self.test_endpoint('GET', '/uploads')
        
        # Test 8: Messaging APIs (will likely fail without proper WhatsApp setup)
        self.log("\n💬 Testing Messaging APIs")
        if template_result and template_result.get('template', {}).get('id'):
            message_data = {
                "recipient": "919876543210",
                "recipient_name": "Test User",
                "template_id": template_result['template']['id']
            }
            self.test_endpoint('POST', '/send-message', message_data)
        
        self.test_endpoint('GET', '/message-history')
        self.test_endpoint('GET', '/scheduled-messages')
        
        # Test 9: Analytics APIs (may have limited data)
        self.log("\n📈 Testing Analytics APIs")
        self.test_endpoint('GET', '/analytics/summary')
        self.test_endpoint('GET', '/analytics')
        self.test_endpoint('GET', '/analytics/templates')
        
        # Test 10: Logout
        self.log("\n🚪 Testing Logout")
        self.test_endpoint('POST', '/auth/logout')
        
        self.log("\n🎉 API Testing Complete!")

def main():
    """Main test function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5001"
    
    print(f"Testing APIs at: {base_url}")
    
    tester = APITester(base_url)
    tester.run_tests()

if __name__ == "__main__":
    main()