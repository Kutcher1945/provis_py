#!/usr/bin/env python3
"""
Import parsed_output.csv data to API

This script reads the parsed Word document and POSTs it to the API.
"""

import csv
from config import IIN, PASSWORD
from auth import login
from rgf_api import create_position_department


def read_parsed_csv(csv_path='parsed_output.csv'):
    """Read and organize data from parsed_output.csv"""

    general_provisions = []
    tasks = []
    authorities_rights = []  # права (authoritiesLaw)
    authorities_responsibilities = []  # обязанности
    functions = []
    additions = []  # Everything from Глава 3 onwards

    in_rights_section = False
    in_responsibilities_section = False

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            main_section = row['main_section'].strip()
            subsection = row['subsection'].strip()
            content = row['content'].strip()

            if not content:
                continue

            # Extract General Provisions from Глава 1
            if 'Глава 1' in main_section:
                general_provisions.append(content)
                continue

            # Extract Tasks from "12. Задачи:"
            if 'Задачи' in subsection:
                if content and content[0].isdigit() and ')' in content[:5]:
                    tasks.append(content)
                continue

            # Handle Полномочия section (права and обязанности)
            if 'Полномочия' in subsection:
                # Check for section markers
                if 'права' in content:
                    in_rights_section = True
                    in_responsibilities_section = False
                    continue
                elif 'обязанности' in content:
                    in_rights_section = False
                    in_responsibilities_section = True
                    continue

                # Extract items
                if in_rights_section:
                    if content and content[0].isdigit() and '.' in content[:5]:
                        authorities_rights.append(content)
                elif in_responsibilities_section:
                    if content and content[0].isdigit() and '.' in content[:5]:
                        authorities_responsibilities.append(content)
                continue

            # Extract Functions from "14. Функции:"
            if 'Функции' in subsection:
                in_rights_section = False
                in_responsibilities_section = False
                if content and content[0].isdigit() and ')' in content[:5]:
                    functions.append(content)
                continue

            # Everything from Глава 3 onwards → additions
            if 'Глава 3' in main_section or 'Глава 4' in main_section or 'Глава 5' in main_section:
                additions.append(content)
                continue

    return {
        'general_provisions': '\n'.join(general_provisions),
        'tasks': tasks,
        'authorities_rights': authorities_rights,
        'authorities_responsibilities': authorities_responsibilities,
        'functions': functions,
        'additions': '\n\n'.join(additions)
    }


def import_to_api():
    """Import parsed data to API"""

    print("="*70)
    print("IMPORTING PARSED DATA TO API")
    print("="*70)

    # Step 1: Read CSV
    print("\nStep 1: Reading parsed_output.csv...")
    data = read_parsed_csv()

    print(f"  ✓ General Provisions: {len(data['general_provisions'])} characters")
    print(f"  ✓ Tasks: {len(data['tasks'])} items")
    print(f"  ✓ Authorities (права): {len(data['authorities_rights'])} items")
    print(f"  ✓ Authorities (обязанности): {len(data['authorities_responsibilities'])} items")
    print(f"  ✓ Functions: {len(data['functions'])} items")
    print(f"  ✓ Additions (Глава 3+): {len(data['additions'])} characters")

    # Step 2: Login
    print("\nStep 2: Logging in...")
    token, _ = login(IIN, PASSWORD)

    if not token:
        print("✗ Login failed")
        return

    # Step 3: Prepare payload
    print("\nStep 3: Preparing API payload...")

    payload = {
        "positionId": 762,
        "positionDepartmentId": 762,
        "departmentId": None,
        "committeeId": None,
        "guId": 9,  # FIXED: Correct GUID for УАиГ
        "guName": "КГУ \"Управление архитектуры и градостроительства города Алматы\"",
        "type": 4,
        "staffNumbers": 5,
        "legalEntity": False,
        "status": "",
        "departmentGuid": None,
        "generalProvisions": data['general_provisions'],
        "additions": data['additions'],
        "approvals": [],
        "functions": [
            {"functionText": func} for func in data['functions']
        ],
        "tasks": [
            {"taskText": task} for task in data['tasks']
        ],
        "authoritiesLaw": [
            {"authorityText": auth} for auth in data['authorities_rights']
        ],
        "authoritiesResponsibilities": [
            {"authorityText": auth} for auth in data['authorities_responsibilities']
        ]
    }

    print(f"  ✓ Payload prepared")
    print(f"    - guName: {payload['guName']}")
    print(f"    - Tasks: {len(payload['tasks'])}")
    print(f"    - Authorities (права): {len(payload['authoritiesLaw'])}")
    print(f"    - Authorities (обязанности): {len(payload['authoritiesResponsibilities'])}")
    print(f"    - Functions: {len(payload['functions'])}")

    # Step 4: Send POST
    print("\nStep 4: Sending POST request...")
    result = create_position_department(token, payload)

    # Step 5: Result
    print("\n" + "="*70)
    print("RESULT")
    print("="*70)

    if result and result.get('success'):
        record_id = result.get('data')
        message = result.get('message')
        print(f"✓ SUCCESS!")
        print(f"  Message: {message}")
        print(f"  Created Record ID: {record_id}")
        print(f"\n  View in browser:")
        print(f"  https://planning.gov.kz/rgffront#/rgffront/filter/positions/department/{record_id}/edit")
        return record_id
    else:
        print(f"✗ FAILED")
        print(f"  Response: {result}")
        return None


if __name__ == "__main__":
    record_id = import_to_api()

    print("\n" + "="*70)
    if record_id:
        print(f"✓ Import successful! Record ID: {record_id}")
    else:
        print("✗ Import failed")
    print("="*70)
