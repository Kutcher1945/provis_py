#!/usr/bin/env python3
"""
Compare manually created vs API created records
"""

import json
from config import IIN, PASSWORD
from auth import login
from rgf_api import get_position_department

# Login
token, _ = login(IIN, PASSWORD)

print("="*70)
print("COMPARING RECORDS")
print("="*70)

# Get manually created record
print("\n1. Manually created record (6722):")
manual = get_position_department(token, 6722)
if manual:
    print(f"   Status: '{manual.get('status')}'")
    print(f"   StatusObj: {manual.get('statusObj')}")
    print(f"   LegalEntity: {manual.get('legalEntity')}")
    print(f"   Type: {manual.get('type')}")

# Get API created record
print("\n2. API created record (6734):")
api = get_position_department(token, 6734)
if api:
    print(f"   Status: '{api.get('status')}'")
    print(f"   StatusObj: {api.get('statusObj')}")
    print(f"   LegalEntity: {api.get('legalEntity')}")
    print(f"   Type: {api.get('type')}")

# Show differences
print("\n" + "="*70)
print("KEY DIFFERENCES:")
print("="*70)

if manual and api:
    if manual.get('status') != api.get('status'):
        print(f"✗ Status differs:")
        print(f"  Manual: '{manual.get('status')}'")
        print(f"  API:    '{api.get('status')}'")

    if manual.get('statusObj') != api.get('statusObj'):
        print(f"\n✗ StatusObj differs:")
        print(f"  Manual: {manual.get('statusObj')}")
        print(f"  API:    {api.get('statusObj')}")

print("\n" + "="*70)
print("FULL MANUAL RECORD (6722):")
print("="*70)
print(json.dumps(manual, indent=2, ensure_ascii=False)[:1500])

print("\n" + "="*70)
print("FULL API RECORD (6734):")
print("="*70)
print(json.dumps(api, indent=2, ensure_ascii=False)[:1500])
