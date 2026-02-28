#!/usr/bin/env python3
"""
Script to delete bad imports from the API

Usage:
    python3 scripts/cleanup_bad_imports.py [record_ids]

    # Delete specific records
    python3 scripts/cleanup_bad_imports.py 6822 6823 6824

    # Delete from import report
    python3 scripts/cleanup_bad_imports.py --from-report data/import_report_20260228_183026.txt
"""

import sys
from pathlib import Path
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import IIN, PASSWORD
from auth import login
from rgf_api import delete_position_department, get_position_department


def extract_ids_from_report(report_file):
    """Extract record IDs from an import report file"""
    ids = []

    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()

        # Find all lines with "ID записи: XXXX"
        matches = re.findall(r'ID записи:\s*(\d+)', content)
        ids.extend([int(id_str) for id_str in matches])

    return ids


def check_record(token, record_id):
    """Check what data is in a record"""
    print(f"\nПроверка записи {record_id}...")

    data = get_position_department(token, record_id)

    if data:
        print(f"  ГУ: {data.get('guName', 'N/A')}")
        print(f"  Права: {len(data.get('authoritiesLaw', []))} элементов")
        print(f"  Обязанности: {len(data.get('authoritiesResponsibilities', []))} элементов")
        print(f"  Задачи: {len(data.get('tasks', []))} элементов")
        print(f"  Функции: {len(data.get('functions', []))} элементов")

        # Check if права and обязанности are missing
        has_rights = len(data.get('authoritiesLaw', [])) > 0
        has_resp = len(data.get('authoritiesResponsibilities', [])) > 0

        if not has_rights or not has_resp:
            print(f"  ⚠ ПРОБЛЕМА: Отсутствуют права или обязанности!")
            return True  # Needs deletion
        else:
            print(f"  ✓ Запись выглядит нормально")
            return False
    else:
        print(f"  ✗ Не удалось получить запись")
        return None


def delete_records(token, record_ids, check_first=True):
    """Delete multiple records"""

    to_delete = []

    if check_first:
        print("\n" + "="*80)
        print("ПРОВЕРКА ЗАПИСЕЙ ПЕРЕД УДАЛЕНИЕМ")
        print("="*80)

        for record_id in record_ids:
            needs_deletion = check_record(token, record_id)
            if needs_deletion:
                to_delete.append(record_id)
            elif needs_deletion is None:
                # Record not found, might be already deleted
                continue

        if not to_delete:
            print("\n✓ Все записи выглядят нормально, удаление не требуется")
            return

        print(f"\n{'='*80}")
        print(f"ЗАПИСИ ДЛЯ УДАЛЕНИЯ: {len(to_delete)}")
        print("="*80)
        for rid in to_delete:
            print(f"  - {rid}")

        confirm = input(f"\nУдалить эти {len(to_delete)} записей? (y/n): ").strip().lower()
        if confirm != 'y':
            print("✗ Удаление отменено")
            return
    else:
        to_delete = record_ids

    # Delete
    print(f"\n{'='*80}")
    print("УДАЛЕНИЕ ЗАПИСЕЙ")
    print("="*80)

    success_count = 0
    failed_count = 0

    for record_id in to_delete:
        result = delete_position_department(token, record_id)
        if result:
            print(f"  ✓ Удалена запись {record_id}")
            success_count += 1
        else:
            print(f"  ✗ Ошибка при удалении {record_id}")
            failed_count += 1

    print(f"\n{'='*80}")
    print(f"✓ Успешно удалено: {success_count}")
    print(f"✗ Ошибок: {failed_count}")
    print("="*80)


def main():
    """Main function"""

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 scripts/cleanup_bad_imports.py [record_ids]")
        print("  python3 scripts/cleanup_bad_imports.py --from-report <report_file>")
        print("\nExamples:")
        print("  python3 scripts/cleanup_bad_imports.py 6822 6823 6824")
        print("  python3 scripts/cleanup_bad_imports.py --from-report data/import_report_20260228_183026.txt")
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
        print("✗ Нет ID для удаления")
        return

    print(f"\n{'='*80}")
    print("УДАЛЕНИЕ ПЛОХИХ ИМПОРТОВ")
    print("="*80)
    print(f"Записей для обработки: {len(record_ids)}")

    # Login
    print("\nАвторизация...")
    token, _ = login(IIN, PASSWORD)

    if not token:
        print("✗ Ошибка авторизации")
        return

    print("✓ Авторизация успешна")

    # Delete
    delete_records(token, record_ids, check_first=True)


if __name__ == "__main__":
    main()
