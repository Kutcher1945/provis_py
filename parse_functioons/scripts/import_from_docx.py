#!/usr/bin/env python3
"""
Universal DOCX import to API

Supports all document structure types:
- CHAPTER-BASED (Глава 1, Глава 2...)
- NUMBERED-SECTIONS (1. Общие положения, 2. Задачи...)
- CUSTOM (keyword-based extraction)
"""

import sys
from docx import Document
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import IIN, PASSWORD
from auth import login
from rgf_api import create_position_department, get_gu_list

# Import universal parser functions
import universal_docx_parser


DOCX_PATH = Path(__file__).parent.parent / "data" / "Положение УАиГ.docx"


def parse_docx_for_api(docx_path=None):
    """Parse .docx and extract data for API using universal parser"""

    # Use provided path or default
    if docx_path is None:
        docx_path = DOCX_PATH

    # Use universal parser
    data = universal_docx_parser.parse_docx_universal(docx_path)

    return data


def select_company(token):
    """Let user select which company/GU to import to"""

    print("\n" + "="*70)
    print("SELECT COMPANY (GOVERNMENT UNIT)")
    print("="*70)

    # Fetch GU list
    print("\nFetching government units...")
    gu_list = get_gu_list(token, parent_id=85750)

    if not gu_list:
        print("✗ Failed to fetch GU list")
        return None, None

    # Sort by name for easier browsing
    gu_list_sorted = sorted(gu_list, key=lambda x: x.get('nameRu', ''))

    # Display all GUs
    print(f"\nFound {len(gu_list_sorted)} government units:\n")
    print(f"{'#':<4} {'ID':<20} {'Name'}")
    print("-" * 100)

    for i, gu in enumerate(gu_list_sorted, 1):
        gu_id = gu.get('id', 'N/A')
        gu_name = gu.get('nameRu', 'N/A')
        print(f"{i:<4} {gu_id:<20} {gu_name}")

    # Let user select
    print("\n" + "="*70)
    while True:
        try:
            choice = input("\nEnter company number (1-{}) or search term: ".format(len(gu_list_sorted))).strip()

            # Check if it's a number
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(gu_list_sorted):
                    selected = gu_list_sorted[idx]
                    break
                else:
                    print(f"✗ Invalid number. Please enter 1-{len(gu_list_sorted)}")
            else:
                # Search by name
                matches = []
                for i, gu in enumerate(gu_list_sorted):
                    if choice.lower() in gu.get('nameRu', '').lower():
                        matches.append((i, gu))

                if len(matches) == 0:
                    print(f"✗ No matches found for '{choice}'. Try again.")
                elif len(matches) == 1:
                    selected = matches[0][1]
                    print(f"✓ Found: {selected.get('nameRu')}")
                    break
                else:
                    print(f"\nFound {len(matches)} matches:")
                    for i, (orig_idx, gu) in enumerate(matches, 1):
                        print(f"  {i}. {gu.get('nameRu')}")
                    sub_choice = input(f"Select match (1-{len(matches)}): ").strip()
                    if sub_choice.isdigit() and 1 <= int(sub_choice) <= len(matches):
                        selected = matches[int(sub_choice) - 1][1]
                        break
                    else:
                        print("✗ Invalid selection")

        except (ValueError, KeyboardInterrupt):
            print("\n✗ Selection cancelled")
            return None, None

    # Confirm selection
    selected_id = selected.get('id')
    selected_name = selected.get('nameRu')

    print("\n" + "="*70)
    print("SELECTED COMPANY:")
    print(f"  ID: {selected_id}")
    print(f"  Name: {selected_name}")
    print("="*70)

    confirm = input("\nProceed with this selection? (y/n): ").strip().lower()
    if confirm != 'y':
        print("✗ Import cancelled")
        return None, None

    return selected_id, selected_name


def import_to_api(docx_file=None):
    """Import parsed DOCX data to API"""

    print("="*70)
    print("IMPORTING FROM DOCX FILE")
    print("="*70)

    # Determine which file to parse
    if docx_file:
        docx_path = Path(__file__).parent.parent / "data" / docx_file
    else:
        docx_path = DOCX_PATH

    if not docx_path.exists():
        print(f"✗ File not found: {docx_path}")
        return

    # Login first
    print("\nStep 1: Logging in...")
    token, _ = login(IIN, PASSWORD)

    if not token:
        print("✗ Login failed")
        return

    # Select company
    print("\nStep 2: Select company...")
    selected_gu_id, selected_gu_name = select_company(token)

    if not selected_gu_id:
        return

    # Parse DOCX
    print(f"\nStep 3: Parsing {docx_path.name}...")
    data = parse_docx_for_api(docx_path)

    print(f"  ✓ General Provisions: {len(data['general_provisions'])} characters")
    print(f"  ✓ Tasks: {len(data['tasks'])} items")
    print(f"  ✓ Authorities (права): {len(data['authorities_rights'])} items")
    print(f"  ✓ Authorities (обязанности): {len(data['authorities_responsibilities'])} items")
    print(f"  ✓ Functions: {len(data['functions'])} items")
    print(f"  ✓ Additions (Глава 3+): {len(data['additions'])} characters")

    # Debug: Show first few items
    print("\n  Preview:")
    print(f"    Tasks[0]: {data['tasks'][0] if data['tasks'] else 'None'}")
    print(f"    Rights[0]: {data['authorities_rights'][0] if data['authorities_rights'] else 'None'}")
    print(f"    Resp[0]: {data['authorities_responsibilities'][0] if data['authorities_responsibilities'] else 'None'}")
    print(f"    Func[0]: {data['functions'][0] if data['functions'] else 'None'}")

    # Step 4: Prepare payload
    print("\nStep 4: Preparing API payload...")

    payload = {
        "positionId": 762,
        "positionDepartmentId": 762,
        "departmentId": None,
        "committeeId": None,
        "guId": selected_gu_id,  # Use selected company ID
        "guName": selected_gu_name,  # Use selected company name
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
    print(f"    - guId: {payload['guId']}")
    print(f"    - guName: {payload['guName']}")
    print(f"    - Tasks: {len(payload['tasks'])}")
    print(f"    - Authorities (права): {len(payload['authoritiesLaw'])}")
    print(f"    - Authorities (обязанности): {len(payload['authoritiesResponsibilities'])}")
    print(f"    - Functions: {len(payload['functions'])}")

    # Step 5: Send POST
    print("\nStep 5: Sending POST request...")
    result = create_position_department(token, payload)

    # Step 6: Result
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
    # Accept optional filename argument
    docx_filename = sys.argv[1] if len(sys.argv) > 1 else None

    record_id = import_to_api(docx_filename)

    print("\n" + "="*70)
    if record_id:
        print(f"✓ Import successful! Record ID: {record_id}")
    else:
        print("✗ Import failed")
    print("="*70)
