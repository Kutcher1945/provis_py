#!/usr/bin/env python3
"""
Example: How to use the API modules in your own scripts

This shows various common use cases:
1. Simple data fetching
2. Creating records from data
3. Error handling
"""

from config import IIN, PASSWORD, DEFAULT_PARENT_ID
from auth import login
from rgf_api import (
    get_positions,
    get_gu_list,
    create_position_department,
    get_position_department
)


def example_1_fetch_data():
    """Example 1: Simple data fetching"""
    print("\n" + "="*60)
    print("Example 1: Fetch and display GU list")
    print("="*60)

    # Login
    token, _ = login(IIN, PASSWORD)
    if not token:
        return

    # Get GU list
    gu_list = get_gu_list(token, parent_id=DEFAULT_PARENT_ID)

    if gu_list:
        print(f"\nFound {len(gu_list)} government units:")
        for i, gu in enumerate(gu_list[:5], 1):
            print(f"{i:2d}. {gu.get('nameRu')}")
            print(f"    ID: {gu.get('id')}, GUID: {gu.get('guid')}")


def example_2_create_record():
    """Example 2: Create a custom record"""
    print("\n" + "="*60)
    print("Example 2: Create a custom position-department record")
    print("="*60)

    # Login
    token, _ = login(IIN, PASSWORD)
    if not token:
        return

    # Prepare custom data
    payload = {
        "positionId": 762,
        "positionDepartmentId": 762,
        "departmentId": None,
        "committeeId": None,
        "additions": "Custom additions from example script",
        "approvals": [],
        "authoritiesLaw": [
            {"authorityText": "Соблюдать законодательство РК"},
            {"authorityText": "Обеспечивать прозрачность"}
        ],
        "authoritiesResponsibilities": [
            {"authorityText": "Ответственность за качество работы"},
            {"authorityText": "Ответственность за соблюдение сроков"}
        ],
        "departmentGuid": None,
        "functions": [],
        "generalProvisions": "Основные положения департамента (пример)",
        "guid": "99900000011429",
        "guName": "КГУ \"Аппарат акима г. Алматы\"",
        "legalEntity": False,
        "staffNumbers": 5,
        "status": "",
        "tasks": [
            {"taskText": "Задача 1: Разработка документации"},
            {"taskText": "Задача 2: Координация работы"}
        ],
        "type": 4
    }

    # Create record
    result = create_position_department(token, payload)

    if result and result.get('success'):
        record_id = result.get('data')
        print(f"\n✓ Created record ID: {record_id}")

        # Fetch it back to verify
        print(f"\nFetching created record...")
        record = get_position_department(token, record_id)
        if record:
            print(f"✓ Verified: Status = {record.get('status')}")
            print(f"  Tasks: {len(record.get('tasks', []))} tasks")
            print(f"  Authorities: {len(record.get('authoritiesLaw', []))} laws")


def example_3_bulk_create():
    """Example 3: Create multiple records from a list"""
    print("\n" + "="*60)
    print("Example 3: Bulk create records")
    print("="*60)

    # Login once
    token, _ = login(IIN, PASSWORD)
    if not token:
        return

    # Sample data (in real use case, this could come from CSV/Excel)
    records_data = [
        {
            "name": "Record 1",
            "tasks": ["Task 1.1", "Task 1.2"],
            "authorities": ["Auth 1.1"]
        },
        {
            "name": "Record 2",
            "tasks": ["Task 2.1"],
            "authorities": ["Auth 2.1", "Auth 2.2"]
        }
    ]

    created_ids = []

    for i, data in enumerate(records_data, 1):
        print(f"\nCreating record {i}/{len(records_data)}: {data['name']}")

        payload = {
            "positionId": 762,
            "positionDepartmentId": 762,
            "departmentId": None,
            "committeeId": None,
            "additions": f"Bulk import - {data['name']}",
            "approvals": [],
            "authoritiesLaw": [
                {"authorityText": auth} for auth in data['authorities']
            ],
            "authoritiesResponsibilities": [],
            "departmentGuid": None,
            "functions": [],
            "generalProvisions": f"General provisions for {data['name']}",
            "guid": "99900000011429",
            "guName": "КГУ \"Аппарат акима г. Алматы\"",
            "legalEntity": False,
            "staffNumbers": 3,
            "status": "",
            "tasks": [
                {"taskText": task} for task in data['tasks']
            ],
            "type": 4
        }

        result = create_position_department(token, payload)

        if result and result.get('success'):
            record_id = result.get('data')
            created_ids.append(record_id)
            print(f"  ✓ Created ID: {record_id}")
        else:
            print(f"  ✗ Failed to create record")

    print(f"\n✓ Summary: Created {len(created_ids)} records")
    print(f"  IDs: {created_ids}")


if __name__ == "__main__":
    # Run examples
    example_1_fetch_data()
    example_2_create_record()
    example_3_bulk_create()

    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)
