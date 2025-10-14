#!/usr/bin/env python3
"""
Test the Lead Management API
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint."""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_create_lead():
    """Test creating a new lead."""
    print("➕ Testing lead creation...")
    lead_data = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "+1234567890",
        "company": "Test Corp",
        "source": "website",
        "budget": 50000,
        "timeline": "3 months",
        "notes": "Test lead for API validation"
    }

    try:
        response = requests.post(f"{API_BASE_URL}/api/v1/leads/", json=lead_data)
        if response.status_code == 200:
            lead = response.json()
            print("✅ Lead created successfully")
            print(f"   Lead ID: {lead.get('id')}")
            return lead.get('id')
        else:
            print(f"❌ Lead creation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Lead creation error: {e}")
        return None

def test_get_leads():
    """Test getting all leads."""
    print("📋 Testing get leads...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/leads/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {data.get('total', 0)} leads")
            return True
        else:
            print(f"❌ Get leads failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get leads error: {e}")
        return False

def test_process_lead(lead_id):
    """Test processing a lead with AI agents."""
    print("🚀 Testing lead processing...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/v1/leads/{lead_id}/process")
        if response.status_code == 200:
            result = response.json()
            print("✅ Lead processed successfully")
            print(f"   Score: {result.get('score')}")
            print(f"   Recommendation: {result.get('recommendation')}")
            return True
        else:
            print(f"❌ Lead processing failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Lead processing error: {e}")
        return False

def test_analytics():
    """Test analytics endpoints."""
    print("📊 Testing analytics...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/analytics/leads")
        if response.status_code == 200:
            analytics = response.json()
            print("✅ Analytics retrieved successfully")
            print(f"   Total leads: {analytics.get('total_leads')}")
            print(f"   Conversion rate: {analytics.get('conversion_rate'):.1f}%")
            return True
        else:
            print(f"❌ Analytics failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Analytics error: {e}")
        return False

def main():
    """Run all API tests."""
    print("🧪 LEAD MANAGEMENT API TESTS")
    print("=" * 50)

    # Wait for API to be ready
    print("⏳ Waiting for API to be ready...")
    time.sleep(2)

    tests = [
        ("Health Check", test_health_check),
        ("Create Lead", test_create_lead),
        ("Get Leads", test_get_leads),
        ("Analytics", test_analytics),
    ]

    results = []
    lead_id = None

    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        if test_name == "Create Lead":
            lead_id = test_func()
            results.append(lead_id is not None)
        elif test_name == "Process Lead" and lead_id:
            results.append(test_func(lead_id))
        else:
            results.append(test_func())

    # Process lead if we created one
    if lead_id:
        print(f"\n🔬 Running: Process Lead")
        results.append(test_process_lead(lead_id))

    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{test_name}: {status}")

    if lead_id:
        status = "✅ PASS" if results[-1] else "❌ FAIL"
        print(f"Process Lead: {status}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the API configuration.")
        return 1

if __name__ == "__main__":
    exit(main())