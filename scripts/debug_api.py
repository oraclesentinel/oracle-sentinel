#!/usr/bin/env python3
"""Debug: Check what Gamma API actually returns for clobTokenIds"""

import requests
import json

GAMMA_API = "https://gamma-api.polymarket.com"

print("=== Fetching 1 market from Gamma API ===\n")

response = requests.get(
    f"{GAMMA_API}/markets",
    params={'limit': 1, 'active': 'true', 'order': 'volume24hr', 'ascending': 'false'},
    timeout=30
)

markets = response.json()

if markets:
    m = markets[0]
    
    print(f"Question: {m.get('question')}")
    print(f"ID: {m.get('id')}")
    print(f"conditionId: {m.get('conditionId')}")
    print(f"slug: {m.get('slug')}")
    print()
    
    # Check ALL token-related fields
    print("=== TOKEN FIELDS ===")
    for key in sorted(m.keys()):
        val = m[key]
        key_lower = key.lower()
        if 'token' in key_lower or 'clob' in key_lower or 'outcome' in key_lower:
            print(f"  {key}: {val}")
            print(f"    type: {type(val).__name__}")
    
    print()
    print("=== ALL KEYS ===")
    for key in sorted(m.keys()):
        val = m[key]
        val_str = str(val)[:60]
        print(f"  {key}: {val_str}")