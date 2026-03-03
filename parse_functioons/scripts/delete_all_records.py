#!/usr/bin/env python3
"""
⚠️ DANGEROUS SCRIPT ⚠️
Delete position-department records from the API

Usage:
    python3 scripts/delete_all_records.py
"""

import sys
import re
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import IIN, PASSWORD
from auth import login
from rgf_api import delete_position_department
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def find_all_import_reports():
    data_dir = Path(__file__).parent.parent / "data"
    return sorted(data_dir.glob("import_report_*.txt"))


def extract_record_ids_from_reports(report_files):
    """Extract {record_id: {file, org, report}} from all import reports"""
    records = {}

    for report_file in report_files:
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()

        for match in re.finditer(r'ID записи:\s*(\d+)', content):
            record_id = int(match.group(1))
            start = max(0, match.start() - 500)
            context = content[start:match.end() + 200]

            file_match = re.search(r'Положение.*?\.docx', context)
            org_match = re.search(r'Организация:\s*(.+?)(?:\n|$)', context)

            records[record_id] = {
                'file': file_match.group(0) if file_match else 'Unknown',
                'org': org_match.group(1).strip() if org_match else 'Unknown',
                'report': report_file.name
            }

    return records


def show_records_table(records):
    """Display all records as a numbered table"""
    print(f"\n{'№':>4}  {'ID':>7}  {'Организация':<50}  {'Файл'}")
    print("-" * 110)

    for i, (record_id, info) in enumerate(records.items(), 1):
        org = info['org'][:48] + '..' if len(info['org']) > 50 else info['org']
        filename = info['file']
        print(f"{i:>4}. {record_id:>7}  {org:<50}  {filename}")

    print()


def select_records_to_delete(all_records):
    """Interactive selection of records to delete"""
    record_items = list(all_records.items())

    show_records_table(all_records)

    print("Выберите записи для удаления:")
    print("  Формат: 1,3,5  или  1-5  или  1,3-7,10  или  'all' для всех")
    print("  Можно также ввести ID напрямую: id:6876,6867,6866")
    print()

    while True:
        choice = input("Ваш выбор: ").strip()

        if not choice:
            continue

        # Direct ID input: id:6876,6867
        if choice.lower().startswith('id:'):
            id_part = choice[3:]
            try:
                selected_ids = [int(x.strip()) for x in id_part.split(',')]
                # Validate all IDs exist
                invalid = [i for i in selected_ids if i not in all_records]
                if invalid:
                    print(f"  ✗ Не найдены ID: {invalid}")
                    continue
                selected = {k: v for k, v in all_records.items() if k in selected_ids}
                return selected
            except ValueError:
                print("  ✗ Неверный формат ID")
                continue

        # Select all
        if choice.lower() == 'all':
            return all_records

        # Parse numbers and ranges
        try:
            selected_indices = set()
            for part in choice.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-', 1))
                    selected_indices.update(range(start, end + 1))
                else:
                    selected_indices.add(int(part))

            if not all(1 <= i <= len(record_items) for i in selected_indices):
                print(f"  ✗ Номера должны быть от 1 до {len(record_items)}")
                continue

            selected = {record_items[i - 1][0]: record_items[i - 1][1]
                        for i in sorted(selected_indices)}
            return selected

        except ValueError:
            print("  ✗ Неверный формат. Примеры: 1,3,5  или  1-5  или  id:6876,6867")
            continue


def execute_deletion(token, records_to_delete):
    """Delete the given records and return (deleted_count, failed_ids)"""
    deleted_count = 0
    failed_ids = []
    total = len(records_to_delete)

    print()
    print("=" * 80)
    print("УДАЛЕНИЕ...")
    print("=" * 80)
    print()

    for i, (record_id, info) in enumerate(records_to_delete.items(), 1):
        org = info['org'][:50]
        print(f"[{i}/{total}] ID {record_id}  {org}...", end=" ", flush=True)

        result = delete_position_department(token, record_id)

        if result is not None:
            print("✓")
            deleted_count += 1
        else:
            print("✗")
            failed_ids.append(record_id)

    return deleted_count, failed_ids


def save_report(records_to_delete, deleted_count, failed_ids):
    report_file = (Path(__file__).parent.parent / "data" /
                   f"delete_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("ОТЧЕТ ОБ УДАЛЕНИИ ЗАПИСЕЙ\n")
        f.write("=" * 80 + "\n")
        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Всего: {len(records_to_delete)}\n")
        f.write(f"Удалено: {deleted_count}\n")
        f.write(f"Ошибок: {len(failed_ids)}\n\n")

        for record_id, info in records_to_delete.items():
            status = "✓ Удалено" if record_id not in failed_ids else "✗ Ошибка"
            f.write(f"{status}  ID {record_id}: {info['org']}\n")
            f.write(f"         Файл: {info['file']}\n\n")

    return report_file


def main():
    print("=" * 80)
    print("⚠️   УДАЛЕНИЕ ЗАПИСЕЙ ИЗ API   ⚠️")
    print("=" * 80)
    print()

    # Авторизация
    print("Авторизация...")
    token, _ = login(IIN, PASSWORD)
    if not token:
        print("✗ Не удалось авторизоваться")
        return
    print("✓ Авторизация успешна\n")

    # Загрузить записи из отчетов
    report_files = find_all_import_reports()
    if not report_files:
        print("✗ Не найдено отчетов об импорте. Нет записей для удаления.")
        return

    all_records = extract_record_ids_from_reports(report_files)
    if not all_records:
        print("✗ В отчетах не найдено ID записей")
        return

    print(f"✓ Найдено записей в отчетах: {len(all_records)}\n")

    # Главное меню
    print("Что вы хотите сделать?")
    print()
    print("  1. Выбрать конкретные записи для удаления")
    print("  2. Удалить ВСЕ записи")
    print("  3. Выход")
    print()

    while True:
        menu_choice = input("Выберите (1/2/3): ").strip()

        if menu_choice == '3':
            print("Выход.")
            return

        elif menu_choice == '1':
            records_to_delete = select_records_to_delete(all_records)
            if not records_to_delete:
                print("✗ Ничего не выбрано")
                return

            print(f"\nВыбрано для удаления: {len(records_to_delete)} записей")
            for record_id, info in records_to_delete.items():
                print(f"  - ID {record_id}: {info['org']}")

            confirm = input(f"\nУдалить {len(records_to_delete)} записей? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("✗ Отменено")
                return
            break

        elif menu_choice == '2':
            show_records_table(all_records)
            print(f"⚠️  Будет удалено ВСЕ {len(all_records)} записей!")
            confirm1 = input("Введите 'DELETE ALL' для подтверждения: ").strip()
            if confirm1 != 'DELETE ALL':
                print("✗ Отменено")
                return
            confirm2 = input(f"Точно удалить все {len(all_records)} записей? (yes/no): ").strip().lower()
            if confirm2 != 'yes':
                print("✗ Отменено")
                return
            records_to_delete = all_records
            break

        else:
            print("  ✗ Введите 1, 2 или 3")

    # Выполнить удаление
    deleted_count, failed_ids = execute_deletion(token, records_to_delete)

    # Итог
    print()
    print("=" * 80)
    print("ИТОГ")
    print("=" * 80)
    print(f"✓ Удалено: {deleted_count}")
    print(f"✗ Ошибок:  {len(failed_ids)}")

    if failed_ids:
        print(f"\nНе удалось удалить: {failed_ids}")

    report_path = save_report(records_to_delete, deleted_count, failed_ids)
    print(f"\n✓ Отчет: {report_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Прервано пользователем")
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
