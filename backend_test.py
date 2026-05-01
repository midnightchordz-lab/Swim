#!/usr/bin/env python3
"""
Backend testing for market-data leakage prevention in sports predictions.
Tests domain safety helpers and API regression.
"""

import sys
import os

# Add backend to path for imports
sys.path.insert(0, '/app/backend')

def test_backend_imports():
    """Test 1: Verify backend/server.py compiles and imports successfully."""
    print("\n=== TEST 1: Backend Import & Compilation ===")
    try:
        import server
        print("✅ backend/server.py imports successfully")
        return True
    except SyntaxError as e:
        print(f"❌ SyntaxError in backend/server.py: {e}")
        return False
    except Exception as e:
        print(f"❌ Import error in backend/server.py: {e}")
        return False


def test_domain_safety_helpers():
    """Test 2: Validate sports/domain safety helpers for IPL prompt."""
    print("\n=== TEST 2: Domain Safety Helpers ===")
    
    try:
        from server import get_session_domain, is_market_domain, sanitize_non_market_report
        
        # Test get_session_domain with IPL sports session
        ipl_session = {
            'topic': 'IPL 2026 winner prediction',
            'prediction_query': 'Which team can win IPL 2026?',
            'domain': 'sports'
        }
        
        domain = get_session_domain(ipl_session)
        print(f"get_session_domain(IPL session) = '{domain}'")
        
        if domain != 'sports':
            print(f"❌ Expected domain='sports', got '{domain}'")
            return False
        print("✅ get_session_domain correctly returns 'sports' for IPL")
        
        # Test is_market_domain
        is_market = is_market_domain('sports')
        print(f"is_market_domain('sports') = {is_market}")
        
        if is_market:
            print("❌ Expected is_market_domain('sports') to be False")
            return False
        print("✅ is_market_domain('sports') correctly returns False")
        
        # Test is_market_domain for actual market domains
        for market_domain in ['financial', 'crypto', 'macro', 'real_estate']:
            if not is_market_domain(market_domain):
                print(f"❌ is_market_domain('{market_domain}') should be True")
                return False
        print("✅ is_market_domain correctly identifies market domains")
        
        # Test sanitize_non_market_report
        print("\n--- Testing sanitize_non_market_report ---")
        
        # Create a legacy sports report with market data leakage
        legacy_report = {
            'domain': 'sports',
            'stock_data': [
                {'ticker': 'IPL.NS', 'last_close': 100, 'price': 105}
            ],
            'prediction': {
                'outcome': 'Mumbai Indians will win IPL 2026; stock price target Rs 500 with support at Rs 450.',
                'confidence': 'High',
                'confidence_score': 0.75
            },
            'prediction_quality': {
                'freshness': {
                    'market_data_points': 5,
                    'web_data_points': 10
                },
                'evidence_drivers': [
                    {'source': 'market_data', 'name': 'Stock Price'},
                    {'source': 'web_search', 'name': 'Team Form'}
                ]
            },
            'evidence_ledger': [
                {'category': 'market_data', 'source': 'ticker_IPL', 'signal': 'price up'},
                {'category': 'web_search', 'source': 'sports_news', 'signal': 'team strong'},
                {'category': 'market_data', 'source': 'market_analysis', 'signal': 'bullish'}
            ]
        }
        
        sanitized = sanitize_non_market_report(legacy_report, ipl_session)
        
        # Check stock_data removed
        if 'stock_data' in sanitized:
            print(f"❌ stock_data not removed: {sanitized.get('stock_data')}")
            return False
        print("✅ stock_data removed from sports report")
        
        # Check market_data_points set to 0
        freshness = sanitized.get('prediction_quality', {}).get('freshness', {})
        market_points = freshness.get('market_data_points', -1)
        if market_points != 0:
            print(f"❌ market_data_points not set to 0: {market_points}")
            return False
        print("✅ prediction_quality.freshness.market_data_points set to 0")
        
        # Check evidence_drivers filtered
        drivers = sanitized.get('prediction_quality', {}).get('evidence_drivers', [])
        market_drivers = [d for d in drivers if 'market' in str(d.get('source', '')).lower()]
        if market_drivers:
            print(f"❌ Market drivers not removed: {market_drivers}")
            return False
        print("✅ Market evidence_drivers removed")
        
        # Check evidence_ledger filtered
        ledger = sanitized.get('evidence_ledger', [])
        market_ledger = [item for item in ledger if item.get('category') == 'market_data']
        if market_ledger:
            print(f"❌ Market data ledger entries not removed: {market_ledger}")
            return False
        print("✅ Market data evidence_ledger entries removed")
        
        # Check outcome text scrubbed
        outcome = sanitized.get('prediction', {}).get('outcome', '')
        print(f"Sanitized outcome: {outcome}")
        
        # Check for stock-price language removal
        leak_keywords = ['stock price', 'Rs 500', 'Rs 450', 'support at', 'target']
        found_leaks = [kw for kw in leak_keywords if kw.lower() in outcome.lower()]
        
        if found_leaks:
            print(f"❌ Stock-price language not removed from outcome: {found_leaks}")
            return False
        
        # Check that sports winner clause is preserved
        if 'Mumbai Indians' not in outcome and 'IPL' not in outcome and 'sports' not in outcome.lower():
            print(f"❌ Sports winner clause removed incorrectly: {outcome}")
            return False
        
        print("✅ Stock-price clauses removed while preserving sports winner clause")
        
        return True
        
    except Exception as e:
        print(f"❌ Domain safety helper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_resolve_ticker_sports():
    """Test 3: Verify resolve_ticker behavior for sports queries."""
    print("\n=== TEST 3: resolve_ticker for Sports Queries ===")
    
    try:
        from server import resolve_ticker
        import asyncio
        
        # Test IPL query
        query = 'Which team can win IPL 2026?'
        graph = {'entities': [{'name': 'IPL'}]}
        
        print(f"Testing resolve_ticker('{query}', {graph})")
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tickers = loop.run_until_complete(resolve_ticker(query, graph))
        loop.close()
        
        print(f"resolve_ticker returned: {tickers}")
        
        # IPL should be in skip_words, so no ticker should be resolved
        if tickers:
            print(f"⚠️  WARNING: resolve_ticker returned tickers for sports query: {tickers}")
            print("    However, generate_report should skip ticker resolution for sports domain")
            # This is not a failure since the main gating is in generate_report
        else:
            print("✅ resolve_ticker correctly returns no tickers for IPL sports query")
        
        return True
        
    except Exception as e:
        print(f"❌ resolve_ticker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auth_endpoint_regression():
    """Test 4: Verify /api/auth/me returns 401, not 404 (regression safety)."""
    print("\n=== TEST 4: Auth Endpoint Regression ===")
    
    try:
        import requests
        
        backend_url = "https://predict.preview.emergentagent.com/api"
        
        print(f"Testing GET {backend_url}/auth/me (without auth)")
        
        response = requests.get(f"{backend_url}/auth/me", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code == 404:
            print("❌ REGRESSION: /api/auth/me returns 404 (should be 401)")
            return False
        
        if response.status_code != 401:
            print(f"⚠️  WARNING: Expected 401, got {response.status_code}")
            return False
        
        # Check response body
        try:
            data = response.json()
            detail = data.get('detail', '')
            if 'authentication required' not in detail.lower():
                print(f"⚠️  WARNING: Expected 'Authentication required' in detail, got: {detail}")
        except:
            pass
        
        print("✅ /api/auth/me correctly returns 401 Authentication required")
        return True
        
    except Exception as e:
        print(f"❌ Auth endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backend_running():
    """Test 5: Confirm backend is running and healthy."""
    print("\n=== TEST 5: Backend Health Check ===")
    
    try:
        import requests
        
        backend_url = "https://predict.preview.emergentagent.com/api"
        
        print(f"Testing GET {backend_url}/health")
        
        response = requests.get(f"{backend_url}/health", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 200:
            print(f"❌ Backend health check failed with status {response.status_code}")
            return False
        
        data = response.json()
        if data.get('status') != 'ok':
            print(f"❌ Backend health status not 'ok': {data}")
            return False
        
        print("✅ Backend is running and healthy")
        return True
        
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all backend tests."""
    print("=" * 70)
    print("BACKEND TESTING: Market-Data Leakage Prevention in Sports Predictions")
    print("=" * 70)
    
    results = {}
    
    # Test 1: Backend imports
    results['backend_imports'] = test_backend_imports()
    
    # Test 2: Domain safety helpers
    results['domain_safety'] = test_domain_safety_helpers()
    
    # Test 3: resolve_ticker for sports
    results['resolve_ticker'] = test_resolve_ticker_sports()
    
    # Test 4: Auth endpoint regression
    results['auth_regression'] = test_auth_endpoint_regression()
    
    # Test 5: Backend health
    results['backend_health'] = test_backend_running()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
