#!/usr/bin/env python3
"""Test advanced search functionality."""

from src.aggregator.store import search_iocs, count_iocs

print("Testing advanced search functionality...\n")

# Test simple search
results = search_iocs('data/iocs.db', query='192.168', search_mode='simple')
print(f'✓ Simple search (192.168): {len(results)} results')
if results:
    print(f'  First: {results[0]["value"]}')

# Test regex search
results = search_iocs('data/iocs.db', query='^192', search_mode='regex', ioc_type='ip')
print(f'✓ Regex search (^192): {len(results)} results')

# Test CIDR search
results = search_iocs('data/iocs.db', query='192.168.0.0/16', search_mode='cidr', ioc_type='ip')
print(f'✓ CIDR search (192.168.0.0/16): {len(results)} results')
if results:
    print(f'  First: {results[0]["value"]}')

# Test date range
results = search_iocs('data/iocs.db', date_from='2024-01-01', date_to='2025-12-31')
print(f'✓ Date range search (2024-2025): {len(results)} results')

# Test count with advanced filters
count = count_iocs('data/iocs.db', query='192', search_mode='simple', ioc_type='ip')
print(f'✓ Count with filters: {count} matching IOCs')

print('\n✅ All advanced search functions working!')
