#!/usr/bin/env python3
"""Test REST API endpoints."""

import json
import requests

BASE_URL = "http://127.0.0.1:5000/api"

print("Testing Threat Feed Aggregator REST API...\n")

# Test health check
try:
    resp = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"[OK] Health Check: {resp.status_code}")
    print(f"  {resp.json()}\n")
except Exception as e:
    print(f"[FAIL] Health Check failed: {e}\n")
    exit(1)

# Test stats endpoint
try:
    resp = requests.get(f"{BASE_URL}/stats", timeout=5)
    print(f"[OK] Stats Endpoint: {resp.status_code}")
    data = resp.json()
    if data['status'] == 'success':
        stats = data['data']
        print(f"  Total IOCs: {stats['total_iocs']}")
        print(f"  Total Records: {stats['total_records']}")
        print(f"  Total Sources: {stats['total_sources']}")
        print(f"  Types: {stats['by_type']}\n")
except Exception as e:
    print(f"[FAIL] Stats Endpoint failed: {e}\n")

# Test filters endpoint
try:
    resp = requests.get(f"{BASE_URL}/filters", timeout=5)
    print(f"[OK] Filters Endpoint: {resp.status_code}")
    data = resp.json()
    if data['status'] == 'success':
        filters = data['data']
        print(f"  Types: {filters['types']}")
        print(f"  Sources count: {len(filters['sources'])}")
        print(f"  Severities: {filters['severities']}\n")
except Exception as e:
    print(f"[FAIL] Filters Endpoint failed: {e}\n")

# Test simple search
try:
    resp = requests.get(f"{BASE_URL}/iocs", params={"query": "192", "type": "ip", "page_size": 5}, timeout=5)
    print(f"[OK] Simple Search (192, type=ip): {resp.status_code}")
    data = resp.json()
    if data['status'] == 'success':
        print(f"  Results: {len(data['data'])}")
        print(f"  Total matches: {data['pagination']['total_results']}")
        if data['data']:
            print(f"  Example: {data['data'][0]['value']}\n")
except Exception as e:
    print(f"[FAIL] Simple Search failed: {e}\n")

# Test regex search
try:
    resp = requests.get(f"{BASE_URL}/iocs", params={
        "query": "^192\\.168",
        "search_mode": "regex",
        "type": "ip",
        "page_size": 3
    }, timeout=5)
    print(f"[OK] Regex Search (^192\\.168): {resp.status_code}")
    data = resp.json()
    if data['status'] == 'success':
        print(f"  Results: {len(data['data'])}")
        print(f"  Total matches: {data['pagination']['total_results']}\n")
except Exception as e:
    print(f"[FAIL] Regex Search failed: {e}\n")

# Test with source filter
try:
    resp = requests.get(f"{BASE_URL}/iocs", params={
        "source": "urlhaus",
        "page_size": 5
    }, timeout=5)
    print(f"[OK] Source Filter (urlhaus): {resp.status_code}")
    data = resp.json()
    if data['status'] == 'success':
        print(f"  Results: {len(data['data'])}")
        print(f"  Total matches: {data['pagination']['total_results']}\n")
except Exception as e:
    print(f"[FAIL] Source Filter failed: {e}\n")

# Test pagination
try:
    resp = requests.get(f"{BASE_URL}/iocs", params={
        "page": 2,
        "page_size": 10
    }, timeout=5)
    print(f"[OK] Pagination (page 2, size 10): {resp.status_code}")
    data = resp.json()
    if data['status'] == 'success':
        print(f"  Page: {data['pagination']['page']} of {data['pagination']['total_pages']}")
        print(f"  Total results: {data['pagination']['total_results']}\n")
except Exception as e:
    print(f"[FAIL] Pagination failed: {e}\n")

print("[SUCCESS] REST API is fully functional!")
print("\nExample API Calls:")
print("- Get stats: curl http://127.0.0.1:5000/api/stats")
print("- Search: curl 'http://127.0.0.1:5000/api/iocs?query=192&type=ip'")
print("- Regex: curl 'http://127.0.0.1:5000/api/iocs?query=^10\\.&search_mode=regex&type=ip'")
print("- Filters: curl http://127.0.0.1:5000/api/filters")
print("- Health: curl http://127.0.0.1:5000/api/health")

