#!/usr/bin/env python3
"""
Complete workflow to fix bad imports:
1. Delete bad records
2. Re-import with fixed parser

Usage:
    python3 scripts/reimport_bad_files.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import IIN, PASSWORD
from auth import login
from rgf_api import delete_position_department, create_position_department, get_gu_list
import universal_docx_parser

DATA_DIR = Path(__file__).parent.parent / "data"


# Files from bad_import.txt that need re-importing
BAD_IMPORTS = {
    'Положение УВП 2026.docx': 'Управление внутренней политики',
    'Положение УДР.docx': 'Управление развития',
    'Положение УГК.docx': 'Управление государственного контроля',
    'Положение УГА.docx': 'Управление государственных активов',
    'Положение УК.docx': 'Управление культуры',
    'Положение УЗО.docx': 'Управление здравоохранения',
    'Положение УКИЖИ.docx': 'Управление коммунальной инфраструктуры',
    'Положение УМП.docx': 'Управление молодежной политики',
    'Положение УМПТиГР.docx': 'Управление по мобилизационной',
    'Положение УО.docx': 'Управление образования',
    'Положение УОДДиПТ.docx': 'Управление организации дорожного',
    'Положение УОЗ.docx': 'Управление охраны здоровья',
    'Положение УРДИ.docx': 'Управление развития инфраструктуры',
    'Положение УРОП.docx': 'Управление развития общественного',
    'Положение УСтроительства.docx': 'Управление строительства',
    'Положение УТ.docx': 'Управление туризма',
    'Положение о «Аппарат акима города Алматы».docx': 'Аппарат акима',
    'Положение УЭиОС.docx': 'Управление экологии',
    'Положение УЭиВ.docx': 'Управление экологии',
}


def find_gu_by_search(gu_list, search_term):
    """Find GU by search term"""
    search_lower = search_term.lower()

    for gu in gu_list:
        gu_name = gu.get('nameRu', '')
        if search_lower in gu_name.lower():
            return gu.get('id'), gu.get('nameRu')

    return None, None


def delete_record_ids(token, record_ids):
    """Delete multiple record IDs"""
    print(f"\n{'='*80}")
    print(f"УДАЛЕНИЕ {len(record_ids)} ПЛОХИХ ЗАПИСЕЙ")
    print("="*80)

    for record_id in record_ids:
        try:
            result = delete_position_department(token, record_id)
            if result:
                print(f"  ✓ Удалена запись {record_id}")
            else:
                print(f"  ⚠ Запись {record_id} возможно уже удалена")
        except Exception as e:
            print(f"  ✗ Ошибка при удалении {record_id}: {e}")


def reimport_files(token, gu_list):
    """Re-import bad files with fixed parser"""

    print(f"\n{'='*80}")
    print(f"РЕ-ИМПОРТ {len(BAD_IMPORTS)} ФАЙЛОВ")
    print("="*80)

    results = []

    for filename, search_term in BAD_IMPORTS.items():
        file_path = DATA_DIR / filename

        if not file_path.exists():
            print(f"\n✗ {filename} - ФАЙЛ НЕ НАЙДЕН")
            results.append({'file': filename, 'status': 'not_found'})
            continue

        print(f"\n{'='*80}")
        print(f"[{len(results)+1}/{len(BAD_IMPORTS)}] {filename}")
        print("="*80)

        # Find GU
        gu_id, gu_name = find_gu_by_search(gu_list, search_term)

        if not gu_id:
            print(f"  ✗ Не найдена организация по запросу: {search_term}")
            results.append({'file': filename, 'status': 'gu_not_found'})
            continue

        print(f"  ГУ: {gu_name} (ID: {gu_id})")

        # Parse document
        try:
            print(f"  📄 Парсинг документа...")
            data = universal_docx_parser.parse_docx_universal(file_path)

            print(f"    ✓ Общие положения: {len(data['general_provisions'])} символов")
            print(f"    ✓ Задачи: {len(data['tasks'])} элементов")
            print(f"    ✓ Права: {len(data['authorities_rights'])} элементов")
            print(f"    ✓ Обязанности: {len(data['authorities_responsibilities'])} элементов")
            print(f"    ✓ Функции: {len(data['functions'])} элементов")

            # Check if parsed correctly
            if len(data['authorities_rights']) == 0 and len(data['authorities_responsibilities']) == 0:
                print(f"  ⚠ ПРЕДУПРЕЖДЕНИЕ: Не извлечены права и обязанности!")
                print(f"  ⚠ Этот файл все еще не парсится корректно")
                results.append({'file': filename, 'status': 'parse_bad', 'gu_id': gu_id})
                continue

        except Exception as e:
            print(f"  ✗ Ошибка парсинга: {e}")
            results.append({'file': filename, 'status': 'parse_error', 'error': str(e)})
            continue

        # Prepare payload
        payload = {
            "positionId": 762,
            "positionDepartmentId": 762,
            "departmentId": None,
            "committeeId": None,
            "guId": gu_id,
            "guName": gu_name,
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

        # Import
        try:
            print(f"  🚀 Отправка в API...")
            result = create_position_department(token, payload)

            if result and result.get('success'):
                record_id = result.get('data')
                print(f"  ✓ УСПЕХ! ID записи: {record_id}")
                print(f"  URL: https://planning.gov.kz/rgffront#/rgffront/filter/positions/department/{record_id}/edit")
                results.append({
                    'file': filename,
                    'status': 'success',
                    'record_id': record_id,
                    'gu_name': gu_name,
                    'rights': len(data['authorities_rights']),
                    'resp': len(data['authorities_responsibilities'])
                })
            else:
                print(f"  ✗ ОШИБКА API: {result}")
                results.append({'file': filename, 'status': 'api_error', 'error': str(result)})

        except Exception as e:
            print(f"  ✗ ИСКЛЮЧЕНИЕ: {e}")
            results.append({'file': filename, 'status': 'exception', 'error': str(e)})

    # Final report
    print(f"\n{'='*80}")
    print("ИТОГОВЫЙ ОТЧЕТ РЕ-ИМПОРТА")
    print("="*80)

    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = len(results) - success_count

    print(f"\nВсего обработано: {len(results)}")
    print(f"✓ Успешно: {success_count}")
    print(f"✗ Ошибок/Пропущено: {failed_count}")

    if success_count > 0:
        print(f"\n{'='*80}")
        print("УСПЕШНО РЕ-ИМПОРТИРОВАННЫЕ:")
        print("="*80)
        for r in results:
            if r['status'] == 'success':
                print(f"  ✓ {r['file']}")
                print(f"    → {r['gu_name']}")
                print(f"    → ID: {r['record_id']}")
                print(f"    → Права: {r['rights']}, Обязанности: {r['resp']}")
                print(f"    → URL: https://planning.gov.kz/rgffront#/rgffront/filter/positions/department/{r['record_id']}/edit")
                print()

    if failed_count > 0:
        print(f"\n{'='*80}")
        print("НЕ УДАЛОСЬ РЕ-ИМПОРТИРОВАТЬ:")
        print("="*80)
        for r in results:
            if r['status'] != 'success':
                print(f"  ✗ {r['file']}")
                print(f"    → Статус: {r['status']}")
                if 'error' in r:
                    print(f"    → Ошибка: {r['error']}")
                print()


def main():
    """Main workflow"""

    print(f"\n{'='*80}")
    print("РЕ-ИМПОРТ ПЛОХИХ ФАЙЛОВ")
    print("="*80)

    # Show what will be done
    print(f"\nЭтот скрипт:")
    print(f"1. Может удалить старые плохие записи (опционально)")
    print(f"2. Ре-импортирует {len(BAD_IMPORTS)} файлов с исправленным парсером")
    print(f"\nФайлы для ре-импорта:")
    for i, filename in enumerate(BAD_IMPORTS.keys(), 1):
        print(f"  {i}. {filename}")

    # Ask for confirmation
    proceed = input(f"\nПродолжить? (y/n): ").strip().lower()
    if proceed != 'y':
        print("✗ Отменено")
        return

    # Ask if should delete old records first
    delete_old = input(f"\nУдалить старые записи перед ре-импортом? (y/n): ").strip().lower()

    if delete_old == 'y':
        ids_input = input("\nВведите ID старых записей через пробел (или оставьте пустым): ").strip()
        if ids_input:
            try:
                old_ids = [int(x) for x in ids_input.split()]
            except ValueError:
                print("✗ Неверный формат ID")
                return
        else:
            old_ids = []
    else:
        old_ids = []

    # Login
    print(f"\n{'='*80}")
    print("АВТОРИЗАЦИЯ")
    print("="*80)

    print("\nВход в систему...")
    token, _ = login(IIN, PASSWORD)

    if not token:
        print("✗ Ошибка авторизации")
        return

    print("✓ Авторизация успешна")

    # Get GU list
    print("\nЗагрузка списка организаций...")
    gu_list = get_gu_list(token, parent_id=85750)

    if not gu_list:
        print("✗ Не удалось загрузить список организаций")
        return

    print(f"✓ Загружено {len(gu_list)} организаций")

    # Delete old records if requested
    if old_ids:
        delete_record_ids(token, old_ids)

    # Re-import files
    reimport_files(token, gu_list)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Прервано пользователем")
    except Exception as e:
        print(f"\n\n✗ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
