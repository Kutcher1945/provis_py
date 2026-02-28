#!/usr/bin/env python3
"""
⚠️ DANGEROUS SCRIPT ⚠️
Deletes ALL position-department records from the API

This script will:
1. Fetch all position-department records from the API
2. Show you how many records exist
3. Ask for multiple confirmations
4. Delete all records one by one

Usage:
    python3 scripts/delete_all_records.py
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import IIN, PASSWORD
from auth import login
from rgf_api import delete_position_department, get_gu_list
import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://planning.gov.kz/backend"


def find_all_import_reports():
    """Найти все файлы отчетов об импорте

    Returns:
        list: Список путей к файлам отчетов
    """
    data_dir = Path(__file__).parent.parent / "data"
    reports = list(data_dir.glob("import_report_*.txt"))
    return sorted(reports)


def extract_record_ids_from_reports(report_files):
    """Извлечь все ID записей из отчетов об импорте

    Args:
        report_files (list): Список путей к файлам отчетов

    Returns:
        dict: {record_id: {'file': filename, 'org': org_name}}
    """
    import re

    records = {}

    for report_file in report_files:
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()

            # Найти все строки вида "ID записи: XXXX"
            id_matches = re.finditer(r'ID записи:\s*(\d+)', content)

            for match in id_matches:
                record_id = int(match.group(1))

                # Попытаться найти имя файла и организацию рядом с ID
                # Ищем в контексте вокруг найденного ID
                start = max(0, match.start() - 500)
                end = min(len(content), match.end() + 200)
                context = content[start:end]

                # Попытаться извлечь название файла
                file_match = re.search(r'Положение.*?\.docx', context)
                filename = file_match.group(0) if file_match else 'Unknown'

                # Попытаться извлечь организацию
                org_match = re.search(r'Организация:\s*(.+?)(?:\n|$)', context)
                org_name = org_match.group(1).strip() if org_match else 'Unknown'

                records[record_id] = {
                    'file': filename,
                    'org': org_name,
                    'report': report_file.name
                }

    return records


def delete_all_records():
    """Основная функция для удаления всех записей"""

    print("=" * 80)
    print("⚠️  УДАЛЕНИЕ ВСЕХ ЗАПИСЕЙ ИЗ API  ⚠️")
    print("=" * 80)
    print()

    # Шаг 1: Авторизация
    print("Шаг 1: Авторизация...")
    token, _ = login(IIN, PASSWORD)  # login returns (token, user_data) tuple

    if not token:
        print("✗ Не удалось авторизоваться")
        return

    print("✓ Авторизация успешна\n")

    # Шаг 2: Найти все отчеты об импорте
    print("Шаг 2: Поиск отчетов об импорте...")
    report_files = find_all_import_reports()

    if not report_files:
        print("✗ Не найдено отчетов об импорте (import_report_*.txt)")
        print("   Нет записей для удаления")
        return

    print(f"✓ Найдено отчетов: {len(report_files)}")
    for report in report_files:
        print(f"    - {report.name}")
    print()

    # Шаг 3: Извлечь ID всех записей
    print("Шаг 3: Извлечение ID записей из отчетов...")
    all_records = extract_record_ids_from_reports(report_files)

    if not all_records:
        print("✗ В отчетах не найдено ID записей")
        return

    print(f"✓ Найдено записей: {len(all_records)}\n")

    # Шаг 4: Показать информацию о записях
    print("=" * 80)
    print("ИНФОРМАЦИЯ О ЗАПИСЯХ:")
    print("=" * 80)

    record_items = list(all_records.items())
    for i, (record_id, info) in enumerate(record_items[:10], 1):  # Показать первые 10
        org_name = info['org']
        filename = info['file']
        print(f"{i:3d}. ID: {record_id:6} | {org_name}")
        print(f"      Файл: {filename}")

    if len(all_records) > 10:
        print(f"     ... и еще {len(all_records) - 10} записей")

    print()

    # Шаг 4: Первое подтверждение
    print("=" * 80)
    print("⚠️  ВНИМАНИЕ! ⚠️")
    print("=" * 80)
    print(f"Вы собираетесь удалить ВСЕ {len(all_records)} записей из API!")
    print("Это действие НЕВОЗМОЖНО ОТМЕНИТЬ!")
    print()

    confirm1 = input(f"Вы уверены? Введите 'DELETE ALL' для продолжения: ").strip()

    if confirm1 != "DELETE ALL":
        print("\n✗ Операция отменена пользователем")
        return

    # Шаг 5: Второе подтверждение
    print()
    print("⚠️  ПОСЛЕДНЕЕ ПРЕДУПРЕЖДЕНИЕ ⚠️")
    print()
    confirm2 = input(f"Удалить {len(all_records)} записей навсегда? (yes/no): ").strip().lower()

    if confirm2 != "yes":
        print("\n✗ Операция отменена пользователем")
        return

    # Шаг 6: Удаление
    print()
    print("=" * 80)
    print("НАЧИНАЕТСЯ УДАЛЕНИЕ...")
    print("=" * 80)
    print()

    deleted_count = 0
    failed_count = 0
    failed_ids = []

    for i, (record_id, info) in enumerate(all_records.items(), 1):
        org_name = info['org']

        print(f"[{i}/{len(all_records)}] Удаление записи {record_id} ({org_name})...", end=" ")

        result = delete_position_department(token, record_id)

        if result or result is not None:
            print("✓")
            deleted_count += 1
        else:
            print("✗")
            failed_count += 1
            failed_ids.append(record_id)

    # Шаг 7: Итоговый отчет
    print()
    print("=" * 80)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 80)
    print(f"Всего записей: {len(all_records)}")
    print(f"✓ Удалено: {deleted_count}")
    print(f"✗ Ошибок: {failed_count}")

    if failed_ids:
        print()
        print("Не удалось удалить следующие ID:")
        for failed_id in failed_ids:
            print(f"  - {failed_id}")

    # Сохранить отчет
    report_file = Path(__file__).parent.parent / "data" / f"delete_all_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("ОТЧЕТ ОБ УДАЛЕНИИ ВСЕХ ЗАПИСЕЙ\n")
        f.write("=" * 80 + "\n")
        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Всего записей: {len(all_records)}\n")
        f.write(f"Удалено: {deleted_count}\n")
        f.write(f"Ошибок: {failed_count}\n\n")

        f.write("УДАЛЕННЫЕ ЗАПИСИ:\n")
        f.write("-" * 80 + "\n")
        for record_id, info in all_records.items():
            org_name = info['org']
            filename = info['file']
            status = "✓ Удалено" if record_id not in failed_ids else "✗ Ошибка"
            f.write(f"{record_id}: {org_name}\n")
            f.write(f"  Файл: {filename}\n")
            f.write(f"  Статус: {status}\n\n")

    print(f"\n✓ Отчет сохранен: {report_file}")
    print()


if __name__ == "__main__":
    try:
        delete_all_records()
    except KeyboardInterrupt:
        print("\n\n✗ Операция прервана пользователем")
    except Exception as e:
        print(f"\n\n✗ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
