#!/usr/bin/env python3
"""
Test POST - Send a single test record to verify the API

This script shows the exact data structure needed and sends a test POST.
"""

import json
from config import IIN, PASSWORD
from auth import login
from rgf_api import create_position_department


def show_data_structure():
    """Display the data structure required for POST"""
    print("\n" + "="*70)
    print("DATA STRUCTURE FOR POST")
    print("="*70)

    example_payload = {
        "positionId": 762,
        "positionDepartmentId": 762,
        "departmentId": None,
        "committeeId": None,
        "guid": "99900000011429",
        "guName": "КГУ \"Управление образования города Алматы\"",
        "type": 4,
        "staffNumbers": 5,
        "legalEntity": False,
        "status": "",
        "departmentGuid": None,
        "generalProvisions": "1. Управление образования является государственным органом, осуществляющим управление в сфере образования города Алматы.",
        "additions": "Дополнительная информация об управлении образования",
        "approvals": [],
        "functions": [],
        "tasks": [
            {"taskText": "Разработка и внедрение образовательных программ"},
            {"taskText": "Контроль качества образования"},
            {"taskText": "Организация повышения квалификации педагогов"}
        ],
        "authoritiesLaw": [
            {"authorityText": "Утверждать образовательные стандарты"},
            {"authorityText": "Контролировать деятельность учебных заведений"},
            {"authorityText": "Лицензировать образовательные учреждения"}
        ],
        "authoritiesResponsibilities": [
            {"authorityText": "Ответственность за качество образования в городе"},
            {"authorityText": "Соблюдение законодательства РК в сфере образования"},
            {"authorityText": "Обеспечение доступности образования для всех граждан"}
        ]
    }

    print("\nJSON Payload Structure:")
    print(json.dumps(example_payload, indent=2, ensure_ascii=False))
    print("\n" + "="*70)

    return example_payload


def send_test_post():
    """Send a test POST request"""
    print("\n" + "="*70)
    print("SENDING TEST POST")
    print("="*70)

    # Login
    print("\nStep 1: Logging in...")
    token, _ = login(IIN, PASSWORD)

    if not token:
        print("✗ Login failed")
        return None

    # Prepare test data
    print("\nStep 2: Preparing test data...")
    test_payload = {
        "positionId": 762,
        "positionDepartmentId": 762,
        "departmentId": None,
        "committeeId": None,
        "guid": "99900000011429",
        "guName": "КГУ \"ТЕСТ - Управление образования города Алматы\"",
        "type": 4,
        "staffNumbers": 5,
        "legalEntity": False,
        "status": "",
        "departmentGuid": None,
        "generalProvisions": "ТЕСТ: Управление образования является государственным органом, осуществляющим управление в сфере образования города Алматы.\n\nОсновные положения:\n1. Управление создано для координации образовательной политики\n2. Осуществляет контроль качества образования\n3. Обеспечивает развитие образовательной инфраструктуры",
        "additions": "ТЕСТ: Дополнительные сведения об управлении образования города Алматы",
        "approvals": [],
        "functions": [],
        "tasks": [
            {"taskText": "Разработка и внедрение образовательных программ"},
            {"taskText": "Контроль качества образования в учебных заведениях"},
            {"taskText": "Организация повышения квалификации педагогических кадров"},
            {"taskText": "Мониторинг образовательных учреждений"}
        ],
        "authoritiesLaw": [
            {"authorityText": "Утверждать образовательные стандарты и программы"},
            {"authorityText": "Контролировать деятельность учебных заведений"},
            {"authorityText": "Лицензировать образовательные учреждения"},
            {"authorityText": "Проводить аттестацию педагогических работников"}
        ],
        "authoritiesResponsibilities": [
            {"authorityText": "Ответственность за качество образования в городе Алматы"},
            {"authorityText": "Соблюдение законодательства РК в сфере образования"},
            {"authorityText": "Обеспечение доступности и равенства в образовании"},
            {"authorityText": "Развитие материально-технической базы образовательных учреждений"}
        ]
    }

    print("Test data prepared:")
    print(f"  GU Name: {test_payload['guName']}")
    print(f"  Staff: {test_payload['staffNumbers']}")
    print(f"  Tasks: {len(test_payload['tasks'])}")
    print(f"  Authorities (Law): {len(test_payload['authoritiesLaw'])}")
    print(f"  Authorities (Resp): {len(test_payload['authoritiesResponsibilities'])}")

    # Send POST
    print("\nStep 3: Sending POST request...")
    result = create_position_department(token, test_payload)

    # Display result
    print("\n" + "="*70)
    print("RESULT")
    print("="*70)

    if result and result.get('success'):
        record_id = result.get('data')
        message = result.get('message')
        print(f"✓ SUCCESS!")
        print(f"  Message: {message}")
        print(f"  Created Record ID: {record_id}")
        print(f"\nYou can fetch this record with:")
        print(f"  from rgf_api import get_position_department")
        print(f"  record = get_position_department(token, {record_id})")
        return record_id
    else:
        print(f"✗ FAILED")
        print(f"  Response: {result}")
        return None


if __name__ == "__main__":
    # Show data structure
    show_data_structure()

    # Send test POST
    record_id = send_test_post()

    print("\n" + "="*70)
    print("Done!")
    print("="*70)

    if record_id:
        print(f"\n✓ Test POST successful! Record ID: {record_id}")
    else:
        print("\n✗ Test POST failed")
