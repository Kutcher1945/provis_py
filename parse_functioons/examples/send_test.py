#!/usr/bin/env python3
"""
Simple test - Send a record with TEST in all fields
"""

from config import IIN, PASSWORD
from auth import login
from rgf_api import create_position_department


def send_simple_test():
    """Send a test record with TEST in all fields"""

    print("="*60)
    print("SENDING TEST RECORD")
    print("="*60)

    # Login
    print("\nLogging in...")
    token, _ = login(IIN, PASSWORD)

    if not token:
        print("✗ Login failed")
        return

    # Simple test payload - all fields have TEST
    test_payload = {
        "positionId": 762,
        "positionDepartmentId": 762,
        "departmentId": None,
        "committeeId": None,
        "guId": 99900000011429,  # FIXED: Send as number, not string "guid"
        "guName": "КГУ \"ТЕСТ - Управление (создано через API)\"",  # FIXED: Proper name
        "type": 4,
        "staffNumbers": 3,
        "legalEntity": False,
        "status": "",
        "departmentGuid": None,
        "generalProvisions": "TEST - General Provisions",
        "additions": "TEST - Additions",
        "approvals": [],
        "functions": [],
        "tasks": [
            {"taskText": "TEST - Task 1"},
            {"taskText": "TEST - Task 2"},
            {"taskText": "TEST - Task 3"}
        ],
        "authoritiesLaw": [
            {"authorityText": "TEST - Authority Law 1"},
            {"authorityText": "TEST - Authority Law 2"}
        ],
        "authoritiesResponsibilities": [
            {"authorityText": "TEST - Responsibility 1"},
            {"authorityText": "TEST - Responsibility 2"}
        ]
    }

    print("\nSending POST request...")
    print(f"  GU Name: {test_payload['guName']}")
    print(f"  Tasks: {len(test_payload['tasks'])}")
    print(f"  Authorities: {len(test_payload['authoritiesLaw'])}")
    print(f"  Responsibilities: {len(test_payload['authoritiesResponsibilities'])}")

    # Send POST
    result = create_position_department(token, test_payload)

    # Display result
    print("\n" + "="*60)
    if result and result.get('success'):
        record_id = result.get('data')
        print(f"✓ SUCCESS! Created Record ID: {record_id}")
    else:
        print(f"✗ FAILED")
        print(f"Response: {result}")
    print("="*60)


if __name__ == "__main__":
    send_simple_test()
