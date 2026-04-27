#!/usr/bin/env python3
"""
Predicta Backend API Testing Suite
Tests all API endpoints for the Evidence-Aware Prediction Engine
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path

class PredictaAPITester:
    def __init__(self, base_url="https://swarm-predict-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'} if not files else {}

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = response.text

            if success:
                self.log_test(name, True, response_data=response_data)
                return True, response_data
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}: {response_data}")
                return False, response_data

        except requests.exceptions.Timeout:
            self.log_test(name, False, f"Request timeout after {timeout}s")
            return False, None
        except Exception as e:
            self.log_test(name, False, f"Request error: {str(e)}")
            return False, None

    def test_health_endpoint(self):
        """Test health check endpoint"""
        print("\n🔍 Testing Health Endpoint...")
        success, data = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        return success and data and data.get("status") == "ok"

    def test_session_creation(self):
        """Test session creation"""
        print("\n🔍 Testing Session Creation...")
        success, data = self.run_test(
            "Create Session",
            "POST",
            "sessions",
            200
        )
        
        if success and data and "session_id" in data:
            self.session_id = data["session_id"]
            print(f"   Session ID: {self.session_id}")
            return True
        return False

    def test_session_retrieval(self):
        """Test session retrieval"""
        if not self.session_id:
            self.log_test("Get Session", False, "No session ID available")
            return False
            
        print("\n🔍 Testing Session Retrieval...")
        success, data = self.run_test(
            "Get Session",
            "GET",
            f"sessions/{self.session_id}",
            200
        )
        return success and data and data.get("id") == self.session_id

    def create_test_document(self):
        """Create a test document for upload"""
        test_content = """
        Climate Change Policy Analysis
        
        The recent climate policy proposals have generated significant debate among various stakeholders.
        Environmental groups strongly support the new regulations, citing urgent need for action.
        Industry representatives express concerns about economic impact and implementation costs.
        Scientists provide mixed assessments of the policy's effectiveness.
        
        Key stakeholders include:
        - Environmental Protection Agency (EPA)
        - Green Coalition advocacy group
        - Manufacturing Industry Association
        - Climate Research Institute
        - Local communities affected by regulations
        
        The policy aims to reduce carbon emissions by 40% over the next decade through:
        - Stricter emission standards for industries
        - Incentives for renewable energy adoption
        - Carbon pricing mechanisms
        - Investment in green technology research
        """
        
        # Create temporary test file
        test_file_path = "/tmp/test_climate_policy.txt"
        with open(test_file_path, "w") as f:
            f.write(test_content)
        return test_file_path

    def test_document_upload(self):
        """Test document upload and knowledge graph extraction"""
        if not self.session_id:
            self.log_test("Document Upload", False, "No session ID available")
            return False
            
        print("\n🔍 Testing Document Upload & Knowledge Graph Extraction...")
        
        # Create test document
        test_file_path = self.create_test_document()
        prediction_query = "Will public support for the climate policy increase or decrease in the next 6 months?"
        
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_climate_policy.txt', f, 'text/plain')}
                data = {'prediction_query': prediction_query}
                
                success, response_data = self.run_test(
                    "Upload Document & Extract Graph",
                    "POST",
                    f"sessions/{self.session_id}/upload",
                    200,
                    data=data,
                    files=files,
                    timeout=60  # Longer timeout for AI processing
                )
                
                if success and response_data:
                    graph = response_data.get("graph", {})
                    if graph and "entities" in graph and "relationships" in graph:
                        print(f"   Extracted {len(graph.get('entities', []))} entities")
                        print(f"   Extracted {len(graph.get('relationships', []))} relationships")
                        return True
                    else:
                        self.log_test("Document Upload", False, "Invalid graph structure in response")
                        return False
                return False
                
        except Exception as e:
            self.log_test("Document Upload", False, f"File handling error: {str(e)}")
            return False
        finally:
            # Clean up test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)

    def test_agent_generation(self):
        """Test AI agent generation"""
        if not self.session_id:
            self.log_test("Agent Generation", False, "No session ID available")
            return False
            
        print("\n🔍 Testing Agent Generation...")
        
        success, response_data = self.run_test(
            "Generate Agents",
            "POST",
            f"sessions/{self.session_id}/generate-agents",
            200,
            data={"num_agents": 15},
            timeout=90  # Longer timeout for AI processing
        )
        
        if success and response_data:
            agents = response_data.get("agents", [])
            if len(agents) == 15:
                print(f"   Generated {len(agents)} agents")
                # Check agent structure
                if agents and all(key in agents[0] for key in ["id", "name", "personality_type", "occupation"]):
                    return True
                else:
                    self.log_test("Agent Generation", False, "Invalid agent structure")
                    return False
            else:
                self.log_test("Agent Generation", False, f"Expected 15 agents, got {len(agents)}")
                return False
        return False

    def test_simulation_start(self):
        """Test simulation start"""
        if not self.session_id:
            self.log_test("Start Simulation", False, "No session ID available")
            return False
            
        print("\n🔍 Testing Simulation Start...")
        
        success, response_data = self.run_test(
            "Start Simulation",
            "POST",
            f"sessions/{self.session_id}/simulate",
            200,
            data={"num_rounds": 3}  # Use fewer rounds for testing
        )
        
        return success and response_data and response_data.get("status") == "simulating"

    def test_simulation_status_polling(self):
        """Test simulation status polling"""
        if not self.session_id:
            self.log_test("Simulation Status", False, "No session ID available")
            return False
            
        print("\n🔍 Testing Simulation Status Polling...")
        
        # Poll for status updates
        max_polls = 20  # Max 2 minutes of polling
        poll_count = 0
        
        while poll_count < max_polls:
            success, response_data = self.run_test(
                f"Poll Status (attempt {poll_count + 1})",
                "GET",
                f"sessions/{self.session_id}/simulation-status",
                200
            )
            
            if not success:
                return False
                
            status = response_data.get("status")
            post_count = response_data.get("post_count", 0)
            current_round = response_data.get("current_round", 0)
            
            print(f"   Status: {status}, Posts: {post_count}, Round: {current_round}")
            
            if status == "simulation_done":
                print("   ✅ Simulation completed successfully")
                return True
            elif status == "error":
                self.log_test("Simulation Status", False, f"Simulation failed with error")
                return False
            
            poll_count += 1
            time.sleep(6)  # Wait 6 seconds between polls
        
        self.log_test("Simulation Status", False, "Simulation did not complete within timeout")
        return False

    def test_posts_retrieval(self):
        """Test posts retrieval"""
        if not self.session_id:
            self.log_test("Get Posts", False, "No session ID available")
            return False
            
        print("\n🔍 Testing Posts Retrieval...")
        
        success, response_data = self.run_test(
            "Get Simulation Posts",
            "GET",
            f"sessions/{self.session_id}/posts",
            200
        )
        
        if success and response_data:
            posts = response_data.get("posts", [])
            print(f"   Retrieved {len(posts)} posts")
            
            # Check post structure
            if posts and all(key in posts[0] for key in ["agent_name", "content", "platform", "round"]):
                return True
            elif not posts:
                self.log_test("Get Posts", False, "No posts found")
                return False
            else:
                self.log_test("Get Posts", False, "Invalid post structure")
                return False
        return False

    def test_report_generation(self):
        """Test report generation"""
        if not self.session_id:
            self.log_test("Generate Report", False, "No session ID available")
            return False
            
        print("\n🔍 Testing Report Generation...")
        
        success, response_data = self.run_test(
            "Generate Prediction Report",
            "POST",
            f"sessions/{self.session_id}/generate-report",
            200,
            timeout=90  # Longer timeout for AI processing
        )
        
        if success and response_data:
            report = response_data.get("report", {})
            required_keys = ["executive_summary", "prediction", "opinion_landscape"]
            
            if all(key in report for key in required_keys):
                print(f"   Report generated with prediction: {report.get('prediction', {}).get('outcome', 'N/A')}")
                return True
            else:
                self.log_test("Generate Report", False, "Invalid report structure")
                return False
        return False

    def test_report_retrieval(self):
        """Test report retrieval"""
        if not self.session_id:
            self.log_test("Get Report", False, "No session ID available")
            return False
            
        print("\n🔍 Testing Report Retrieval...")
        
        success, response_data = self.run_test(
            "Get Stored Report",
            "GET",
            f"sessions/{self.session_id}/report",
            200
        )
        
        if success and response_data:
            required_keys = ["executive_summary", "prediction", "opinion_landscape"]
            if all(key in response_data for key in required_keys):
                return True
            else:
                self.log_test("Get Report", False, "Invalid report structure")
                return False
        return False

    def test_chat_functionality(self):
        """Test chat functionality"""
        if not self.session_id:
            self.log_test("Chat Functionality", False, "No session ID available")
            return False
            
        print("\n🔍 Testing Chat Functionality...")
        
        # Test chat with ReportAgent
        success, response_data = self.run_test(
            "Chat with ReportAgent",
            "POST",
            f"sessions/{self.session_id}/chat",
            200,
            data={
                "target_type": "report",
                "target_id": "report_agent",
                "message": "What's the most important finding from the simulation?"
            },
            timeout=60
        )
        
        if success and response_data and "response" in response_data:
            print(f"   ReportAgent response: {response_data['response'][:100]}...")
            return True
        return False

    def test_chat_history(self):
        """Test chat history retrieval"""
        if not self.session_id:
            self.log_test("Chat History", False, "No session ID available")
            return False
            
        print("\n🔍 Testing Chat History...")
        
        success, response_data = self.run_test(
            "Get Chat History",
            "GET",
            f"sessions/{self.session_id}/chat-history?target_type=report&target_id=report_agent",
            200
        )
        
        if success and response_data and "history" in response_data:
            history = response_data["history"]
            print(f"   Retrieved {len(history)} chat messages")
            return True
        return False

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting Predicta Backend API Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test sequence - each test depends on previous ones
        test_sequence = [
            ("Health Check", self.test_health_endpoint),
            ("Session Creation", self.test_session_creation),
            ("Session Retrieval", self.test_session_retrieval),
            ("Document Upload", self.test_document_upload),
            ("Agent Generation", self.test_agent_generation),
            ("Simulation Start", self.test_simulation_start),
            ("Simulation Status", self.test_simulation_status_polling),
            ("Posts Retrieval", self.test_posts_retrieval),
            ("Report Generation", self.test_report_generation),
            ("Report Retrieval", self.test_report_retrieval),
            ("Chat Functionality", self.test_chat_functionality),
            ("Chat History", self.test_chat_history),
        ]
        
        failed_tests = []
        
        for test_name, test_func in test_sequence:
            try:
                success = test_func()
                if not success:
                    failed_tests.append(test_name)
                    print(f"⚠️  {test_name} failed - continuing with remaining tests")
            except Exception as e:
                failed_tests.append(test_name)
                print(f"💥 {test_name} crashed: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if failed_tests:
            print(f"\n❌ Failed tests: {', '.join(failed_tests)}")
        else:
            print("\n✅ All tests passed!")
        
        return len(failed_tests) == 0

def main():
    """Main test runner"""
    tester = PredictaAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())