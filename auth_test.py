#!/usr/bin/env python3
"""
SwarmSim Auth Endpoint Testing
Focused test for /api/auth/me endpoint as requested in test_result.md
"""

import requests
import json
import os
from pathlib import Path

def test_auth_endpoint():
    """Test the /api/auth/me endpoint specifically"""
    
    # Get backend URL from frontend .env
    frontend_env_path = Path("/app/frontend/.env")
    backend_url = "https://predict.preview.emergentagent.com"  # default
    
    if frontend_env_path.exists():
        with open(frontend_env_path, 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_url = line.split('=', 1)[1].strip()
                    break
    
    api_url = f"{backend_url}/api"
    auth_endpoint = f"{api_url}/auth/me"
    
    print(f"🔍 Testing Auth Endpoint: {auth_endpoint}")
    print("=" * 60)
    
    try:
        # Test without Authorization header - should return 401
        print("Testing GET /api/auth/me without Authorization header...")
        response = requests.get(auth_endpoint, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response Body: {json.dumps(response_data, indent=2)}")
        except:
            response_data = response.text
            print(f"Response Body (text): {response_data}")
        
        # Check requirements
        success = True
        issues = []
        
        # Must return 401, not 404
        if response.status_code != 401:
            success = False
            issues.append(f"Expected HTTP 401, got {response.status_code}")
        
        # Must not return 404
        if response.status_code == 404:
            success = False
            issues.append("Endpoint returned 404 - endpoint not found or not properly configured")
        
        # Check for JSON response with detail
        if response.status_code == 401:
            try:
                json_data = response.json()
                if "detail" not in json_data:
                    success = False
                    issues.append("Response missing 'detail' field")
                elif json_data["detail"] != "Authentication required":
                    success = False
                    issues.append(f"Expected detail 'Authentication required', got '{json_data.get('detail')}'")
            except:
                success = False
                issues.append("Response is not valid JSON")
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 AUTH ENDPOINT TEST RESULTS")
        print("=" * 60)
        
        if success:
            print("✅ Auth endpoint test PASSED")
            print("✅ Returns HTTP 401 (not 404)")
            print("✅ Returns JSON with detail 'Authentication required'")
        else:
            print("❌ Auth endpoint test FAILED")
            for issue in issues:
                print(f"❌ {issue}")
        
        return success, response.status_code, response_data
        
    except requests.exceptions.Timeout:
        print("❌ Request timeout - backend may not be running")
        return False, None, "timeout"
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - backend not accessible")
        return False, None, "connection_error"
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False, None, str(e)

def test_service_health():
    """Light service health check"""
    
    # Get backend URL from frontend .env
    frontend_env_path = Path("/app/frontend/.env")
    backend_url = "https://predict.preview.emergentagent.com"  # default
    
    if frontend_env_path.exists():
        with open(frontend_env_path, 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_url = line.split('=', 1)[1].strip()
                    break
    
    api_url = f"{backend_url}/api"
    
    print(f"\n🔍 Testing Service Health: {api_url}")
    print("=" * 60)
    
    # Test basic connectivity
    try:
        response = requests.get(f"{api_url}/health", timeout=10)
        print(f"Health endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Health response: {json.dumps(data, indent=2)}")
                return True
            except:
                print(f"Health response (text): {response.text}")
                return response.status_code == 200
        else:
            print(f"Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Health check timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Health check connection error")
        return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def main():
    """Main test runner"""
    print("🚀 SwarmSim Auth Endpoint Test")
    print("Testing imported latest main backend auth endpoint")
    print("=" * 60)
    
    # Run health check first
    health_ok = test_service_health()
    
    # Run auth endpoint test
    auth_success, status_code, response_data = test_auth_endpoint()
    
    print("\n" + "=" * 60)
    print("📋 FINAL SUMMARY")
    print("=" * 60)
    
    if health_ok:
        print("✅ Service health check: PASSED")
    else:
        print("❌ Service health check: FAILED")
    
    if auth_success:
        print("✅ Auth endpoint test: PASSED")
        print("   - GET /api/auth/me returns HTTP 401")
        print("   - Response contains JSON with detail 'Authentication required'")
        print("   - Does NOT return 404")
    else:
        print("❌ Auth endpoint test: FAILED")
        print(f"   - Status code: {status_code}")
        print(f"   - Response: {response_data}")
    
    return auth_success and health_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)