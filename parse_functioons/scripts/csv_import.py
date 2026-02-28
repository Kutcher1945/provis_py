#!/usr/bin/env python3
"""
CSV Import Example

Shows how to import data from a CSV file and create position-department records.

CSV Format:
    name,general_provisions,tasks,authorities,staff_numbers
    "Dept 1","Provisions text","Task1;Task2","Auth1;Auth2",5
    "Dept 2","Provisions text","Task1","Auth1;Auth2;Auth3",3
"""

import csv
from pathlib import Path
from config import IIN, PASSWORD
from auth import login
from rgf_api import create_position_department


def read_csv_data(csv_path):
    """
    Read CSV file and return list of records

    Args:
        csv_path (str): Path to CSV file

    Returns:
        list: List of record dictionaries
    """
    records = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                'name': row.get('name', ''),
                'general_provisions': row.get('general_provisions', ''),
                'tasks': row.get('tasks', '').split(';') if row.get('tasks') else [],
                'authorities': row.get('authorities', '').split(';') if row.get('authorities') else [],
                'staff_numbers': int(row.get('staff_numbers', 3))
            })

    return records


def csv_to_payload(record_data):
    """
    Convert CSV record to API payload format

    Args:
        record_data (dict): CSV record data

    Returns:
        dict: API payload
    """
    return {
        "positionId": 762,
        "positionDepartmentId": 762,
        "departmentId": None,
        "committeeId": None,
        "additions": f"Imported from CSV - {record_data['name']}",
        "approvals": [],
        "authoritiesLaw": [
            {"authorityText": auth.strip()}
            for auth in record_data['authorities']
            if auth.strip()
        ],
        "authoritiesResponsibilities": [],
        "departmentGuid": None,
        "functions": [],
        "generalProvisions": record_data['general_provisions'],
        "guid": "99900000011429",
        "guName": f"{record_data['name']}",
        "legalEntity": False,
        "staffNumbers": record_data['staff_numbers'],
        "status": "",
        "tasks": [
            {"taskText": task.strip()}
            for task in record_data['tasks']
            if task.strip()
        ],
        "type": 4
    }


def import_from_csv(csv_path):
    """
    Import records from CSV file and create them via API

    Args:
        csv_path (str): Path to CSV file

    Returns:
        dict: Summary with created IDs and errors
    """
    # Check if file exists
    if not Path(csv_path).exists():
        print(f"✗ CSV file not found: {csv_path}")
        return {'success': [], 'errors': []}

    # Login
    print("Logging in...")
    token, _ = login(IIN, PASSWORD)
    if not token:
        print("✗ Login failed")
        return {'success': [], 'errors': []}

    # Read CSV
    print(f"\nReading CSV: {csv_path}")
    records = read_csv_data(csv_path)
    print(f"Found {len(records)} records to import")

    # Import records
    created_ids = []
    errors = []

    print("\nImporting records...")
    print("="*60)

    for i, record in enumerate(records, 1):
        print(f"\n[{i}/{len(records)}] Importing: {record['name']}")

        # Convert to API payload
        payload = csv_to_payload(record)

        # Create record
        result = create_position_department(token, payload)

        if result and result.get('success'):
            record_id = result.get('data')
            created_ids.append(record_id)
            print(f"  ✓ Created ID: {record_id}")
        else:
            error_msg = result.get('message') if result else 'Unknown error'
            errors.append({'name': record['name'], 'error': error_msg})
            print(f"  ✗ Failed: {error_msg}")

    # Summary
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"Total records: {len(records)}")
    print(f"✓ Successfully created: {len(created_ids)}")
    print(f"✗ Failed: {len(errors)}")

    if created_ids:
        print(f"\nCreated IDs: {created_ids}")

    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  - {err['name']}: {err['error']}")

    return {'success': created_ids, 'errors': errors}


def create_sample_csv(csv_path='sample_import.csv'):
    """
    Create a sample CSV file for testing

    Args:
        csv_path (str): Path for sample CSV file
    """
    sample_data = [
        {
            'name': 'Департамент тестирования 1',
            'general_provisions': 'Основные положения для тестового департамента 1',
            'tasks': 'Задача 1;Задача 2;Задача 3',
            'authorities': 'Соблюдать законодательство;Обеспечивать прозрачность',
            'staff_numbers': '5'
        },
        {
            'name': 'Департамент тестирования 2',
            'general_provisions': 'Основные положения для тестового департамента 2',
            'tasks': 'Задача А;Задача Б',
            'authorities': 'Контролировать процессы;Отчитываться перед вышестоящими органами',
            'staff_numbers': '3'
        }
    ]

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'general_provisions', 'tasks', 'authorities', 'staff_numbers']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_data)

    print(f"✓ Sample CSV created: {csv_path}")
    return csv_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Import from specified CSV file
        csv_file = sys.argv[1]
        import_from_csv(csv_file)
    else:
        # Create and import from sample CSV
        print("No CSV file specified. Creating sample CSV...")
        sample_csv = create_sample_csv()
        print(f"\nTo import from your own CSV, run:")
        print(f"  python3 csv_import.py your_file.csv\n")

        # Ask user if they want to import the sample
        response = input("Import sample CSV? (y/n): ").strip().lower()
        if response == 'y':
            import_from_csv(sample_csv)
