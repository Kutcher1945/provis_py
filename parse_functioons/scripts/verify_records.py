#!/usr/bin/env python3
"""
Script to verify and inspect imported records

Usage:
    python3 scripts/verify_records.py [record_ids]
    python3 scripts/verify_records.py --from-report <report_file>
"""

import sys
from pathlib import Path
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import IIN, PASSWORD
from auth import login
from rgf_api import get_position_department


def extract_ids_from_report(report_file):
    """Extract record IDs from an import report file"""
    ids = []

    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()

        # Find all lines with "ID записи: XXXX"
        matches = re.findall(r'ID записи:\s*(\d+)', content)
        ids.extend([int(id_str) for id_str in matches])

    return ids


def verify_record(token, record_id, show_details=False):
    """Verify a single record"""
    data = get_position_department(token, record_id)

    if not data:
        return {
            'id': record_id,
            'status': 'NOT_FOUND',
            'gu_name': None,
            'rights': 0,
            'responsibilities': 0,
            'tasks': 0,
            'functions': 0
        }

    rights_count = len(data.get('authoritiesLaw', []))
    resp_count = len(data.get('authoritiesResponsibilities', []))
    tasks_count = len(data.get('tasks', []))
    functions_count = len(data.get('functions', []))

    # Determine status
    if rights_count == 0 and resp_count == 0:
        status = 'BAD'
    elif rights_count == 0 or resp_count == 0:
        status = 'PARTIAL'
    else:
        status = 'OK'

    result = {
        'id': record_id,
        'status': status,
        'gu_name': data.get('guName', 'N/A'),
        'rights': rights_count,
        'responsibilities': resp_count,
        'tasks': tasks_count,
        'functions': functions_count
    }

    if show_details:
        print(f"\n{'='*80}")
        print(f"ЗАПИСЬ {record_id}")
        print("="*80)
        print(f"Организация: {result['gu_name']}")
        print(f"Статус: {status}")
        print(f"Права: {rights_count}")
        print(f"Обязанности: {resp_count}")
        print(f"Задачи: {tasks_count}")
        print(f"Функции: {functions_count}")

        if status == 'BAD':
            print("\n⚠ ПРОБЛЕМА: Отсутствуют права И обязанности!")
        elif status == 'PARTIAL':
            if rights_count == 0:
                print("\n⚠ ПРОБЛЕМА: Отсутствуют права!")
            if resp_count == 0:
                print("\n⚠ ПРОБЛЕМА: Отсутствуют обязанности!")

        # Show sample data
        if show_details and rights_count > 0:
            print(f"\nПримеры прав (первые 3):")
            for i, item in enumerate(data.get('authoritiesLaw', [])[:3], 1):
                text = item.get('authorityText', '')
                print(f"  {i}. {text[:80]}...")

        if show_details and resp_count > 0:
            print(f"\nПримеры обязанностей (первые 3):")
            for i, item in enumerate(data.get('authoritiesResponsibilities', [])[:3], 1):
                text = item.get('authorityText', '')
                print(f"  {i}. {text[:80]}...")

    return result


def verify_multiple(token, record_ids):
    """Verify multiple records and generate summary"""
    results = []

    print(f"\n{'='*80}")
    print("ПРОВЕРКА ЗАПИСЕЙ")
    print("="*80)

    for record_id in record_ids:
        result = verify_record(token, record_id, show_details=False)
        results.append(result)

    # Print summary table
    print(f"\n{'ID':<8} {'Права':<8} {'Обяз.':<8} {'Задачи':<8} {'Функц.':<8} {'Статус':<12} {'Организация'}")
    print("-"*100)

    for r in results:
        status_mark = {
            'OK': '✓ OK',
            'PARTIAL': '⚠ PARTIAL',
            'BAD': '✗ BAD',
            'NOT_FOUND': '✗ NOT FOUND'
        }.get(r['status'], r['status'])

        gu_name = r['gu_name'][:40] if r['gu_name'] else 'N/A'

        print(f"{r['id']:<8} {r['rights']:<8} {r['responsibilities']:<8} "
              f"{r['tasks']:<8} {r['functions']:<8} {status_mark:<12} {gu_name}")

    # Summary statistics
    print("-"*100)
    ok_count = sum(1 for r in results if r['status'] == 'OK')
    partial_count = sum(1 for r in results if r['status'] == 'PARTIAL')
    bad_count = sum(1 for r in results if r['status'] == 'BAD')
    not_found_count = sum(1 for r in results if r['status'] == 'NOT_FOUND')

    print(f"\nИтого:")
    print(f"  ✓ Нормальные: {ok_count}")
    print(f"  ⚠ Частичные: {partial_count}")
    print(f"  ✗ Плохие: {bad_count}")
    print(f"  ✗ Не найдены: {not_found_count}")

    # List bad record IDs
    bad_ids = [r['id'] for r in results if r['status'] in ['BAD', 'PARTIAL']]
    if bad_ids:
        print(f"\n{'='*80}")
        print("ЗАПИСИ ТРЕБУЮЩИЕ ИСПРАВЛЕНИЯ:")
        print("="*80)
        print("ID записей для удаления:")
        print(" ".join(str(id) for id in bad_ids))
        print(f"\nКоманда для удаления:")
        print(f"python3 scripts/cleanup_bad_imports.py {' '.join(str(id) for id in bad_ids)}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 scripts/verify_records.py [record_ids]")
        print("  python3 scripts/verify_records.py --from-report <report_file>")
        print("\nExamples:")
        print("  python3 scripts/verify_records.py 6822 6823 6824")
        print("  python3 scripts/verify_records.py --from-report data/import_report_20260228_183026.txt")
        return

    # Parse arguments
    if sys.argv[1] == '--from-report':
        if len(sys.argv) < 3:
            print("✗ Укажите файл отчета")
            return

        report_file = Path(sys.argv[2])
        if not report_file.exists():
            print(f"✗ Файл не найден: {report_file}")
            return

        record_ids = extract_ids_from_report(report_file)
        print(f"Извлечено {len(record_ids)} ID из отчета")

    else:
        # Direct IDs
        try:
            record_ids = [int(arg) for arg in sys.argv[1:]]
        except ValueError:
            print("✗ Неверный формат ID")
            return

    if not record_ids:
        print("✗ Нет ID для проверки")
        return

    # Login
    print("\nАвторизация...")
    token, _ = login(IIN, PASSWORD)

    if not token:
        print("✗ Ошибка авторизации")
        return

    print("✓ Авторизация успешна")

    # Verify
    verify_multiple(token, record_ids)


if __name__ == "__main__":
    main()
