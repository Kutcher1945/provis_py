#!/usr/bin/env python3
"""
Массовый импорт нескольких документов в API

Позволяет импортировать любое количество документов за один запуск.
Для каждого файла можно выбрать свою организацию или использовать одну для всех.
"""

import sys
from pathlib import Path
from datetime import datetime
from docx import Document
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import IIN, PASSWORD
from auth import login
from rgf_api import create_position_department, get_gu_list
import universal_docx_parser
import org_mapping  # Модуль для автоматического определения организаций

DATA_DIR = Path(__file__).parent.parent / "data"


def list_available_documents():
    """Показать список всех доступных .docx файлов"""

    docx_files = sorted(DATA_DIR.glob("Положение*.docx"))

    if not docx_files:
        print("✗ Нет доступных .docx файлов в папке data/")
        return []

    print(f"\n{'='*80}")
    print("ДОСТУПНЫЕ ДОКУМЕНТЫ")
    print(f"{'='*80}\n")
    print(f"{'#':<4} {'Файл'}")
    print("-" * 80)

    for i, file_path in enumerate(docx_files, 1):
        print(f"{i:<4} {file_path.name}")

    return docx_files


def select_documents(docx_files):
    """Позволить пользователю выбрать документы для импорта"""

    print(f"\n{'='*80}")
    print("ВЫБОР ДОКУМЕНТОВ ДЛЯ ИМПОРТА")
    print(f"{'='*80}\n")

    print("Варианты выбора:")
    print("  - Номера через запятую: 1,3,5")
    print("  - Диапазон: 1-5")
    print("  - Комбинация: 1,3,5-8,10")
    print("  - Все файлы: all")
    print("  - Поиск по названию: архитектур")

    while True:
        choice = input(f"\nВыберите документы (1-{len(docx_files)}): ").strip()

        if not choice:
            print("✗ Пожалуйста, введите ваш выбор")
            continue

        # Все файлы
        if choice.lower() == 'all':
            return docx_files

        # Поиск по названию
        if not any(c.isdigit() for c in choice):
            matches = []
            for i, f in enumerate(docx_files):
                if choice.lower() in f.name.lower():
                    matches.append(f)

            if matches:
                print(f"\n✓ Найдено файлов: {len(matches)}")
                for f in matches:
                    print(f"  - {f.name}")

                confirm = input("\nИспользовать эти файлы? (y/n): ").strip().lower()
                if confirm == 'y':
                    return matches
                else:
                    continue
            else:
                print(f"✗ Не найдено файлов с '{choice}'")
                continue

        # Парсинг номеров и диапазонов
        try:
            selected_indices = set()
            parts = choice.split(',')

            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Диапазон
                    start, end = map(int, part.split('-'))
                    selected_indices.update(range(start, end + 1))
                else:
                    # Одиночный номер
                    selected_indices.add(int(part))

            # Проверка валидности
            if not all(1 <= i <= len(docx_files) for i in selected_indices):
                print(f"✗ Некоторые номера вне диапазона 1-{len(docx_files)}")
                continue

            # Получить выбранные файлы
            selected_files = [docx_files[i-1] for i in sorted(selected_indices)]

            print(f"\n✓ Выбрано файлов: {len(selected_files)}")
            for f in selected_files:
                print(f"  - {f.name}")

            confirm = input("\nПродолжить с этими файлами? (y/n): ").strip().lower()
            if confirm == 'y':
                return selected_files
            else:
                continue

        except (ValueError, IndexError) as e:
            print(f"✗ Неверный формат ввода. Попробуйте снова.")
            continue


# Используем функции из org_mapping модуля
# (Старые функции extract_org_name_from_docx и suggest_company_from_filename удалены)


def select_company_for_file(token, filename, gu_list_cache=None, file_path=None):
    """Выбрать организацию для конкретного файла"""

    print(f"\n{'='*80}")
    print(f"ВЫБОР ОРГАНИЗАЦИИ ДЛЯ: {filename}")
    print(f"{'='*80}")

    # Использовать кэш если есть
    if gu_list_cache is None:
        print("\nЗагрузка списка организаций...")
        gu_list = get_gu_list(token, parent_id=85750)
        if not gu_list:
            print("✗ Не удалось загрузить список организаций")
            return None, None, gu_list
    else:
        gu_list = gu_list_cache

    # Сортировать по имени
    gu_list_sorted = sorted(gu_list, key=lambda x: x.get('nameRu', ''))

    # Автоматическое предложение на основе содержимого документа
    if file_path is None:
        file_path = DATA_DIR / filename
    suggested_id, suggested_name, detected_org_name = org_mapping.suggest_gu_for_file(filename, gu_list, file_path)

    if suggested_id:
        print(f"\n💡 АВТОМАТИЧЕСКОЕ ПРЕДЛОЖЕНИЕ:")
        print(f"   Название из документа: {detected_org_name}")
        print(f"   Найденная организация: {suggested_name}")
        print(f"   ID: {suggested_id}")

        confirm = input(f"\nИспользовать эту организацию? (y/n или введите другой запрос): ").strip()

        if confirm.lower() == 'y':
            print(f"✓ Выбрано: {suggested_name} (ID: {suggested_id})")
            return suggested_id, suggested_name, gu_list
    elif detected_org_name:
        print(f"\n⚠ Из документа извлечено: {detected_org_name}")
        print(f"   Но не удалось найти точное совпадение в списке организаций")

        # Если пользователь ввел что-то другое, используем это как поисковый запрос
        if confirm.lower() != 'n' and confirm:
            # Попробуем использовать это как поиск
            matches = []
            for i, gu in enumerate(gu_list_sorted):
                if confirm.lower() in gu.get('nameRu', '').lower():
                    matches.append((i, gu))

            if len(matches) == 1:
                selected = matches[0][1]
                print(f"✓ Найдено: {selected.get('nameRu')}")
                return selected.get('id'), selected.get('nameRu'), gu_list

    # Показать все организации
    print(f"\nВсего организаций: {len(gu_list_sorted)}\n")
    print(f"{'#':<4} {'ID':<20} {'Название'}")
    print("-" * 100)

    for i, gu in enumerate(gu_list_sorted, 1):
        gu_id = gu.get('id', 'N/A')
        gu_name = gu.get('nameRu', 'N/A')
        print(f"{i:<4} {gu_id:<20} {gu_name}")

    # Поиск/выбор
    while True:
        choice = input("\nВведите номер (1-{}) или поисковый запрос: ".format(len(gu_list_sorted))).strip()

        if not choice:
            print("✗ Введите номер или поисковый запрос")
            continue

        # Проверка - это номер?
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(gu_list_sorted):
                selected = gu_list_sorted[idx]
                break
            else:
                print(f"✗ Номер должен быть от 1 до {len(gu_list_sorted)}")
                continue
        else:
            # Поиск
            matches = []
            for i, gu in enumerate(gu_list_sorted):
                if choice.lower() in gu.get('nameRu', '').lower():
                    matches.append((i, gu))

            if len(matches) == 0:
                print(f"✗ Не найдено совпадений для '{choice}'")
                continue
            elif len(matches) == 1:
                selected = matches[0][1]
                print(f"✓ Найдено: {selected.get('nameRu')}")
                break
            else:
                print(f"\nНайдено совпадений: {len(matches)}")
                for i, (orig_idx, gu) in enumerate(matches[:10], 1):
                    print(f"  {i}. {gu.get('nameRu')}")
                if len(matches) > 10:
                    print(f"  ... и еще {len(matches) - 10}")

                sub_choice = input(f"Выберите (1-{min(len(matches), 10)}): ").strip()
                if sub_choice.isdigit() and 1 <= int(sub_choice) <= min(len(matches), 10):
                    selected = matches[int(sub_choice) - 1][1]
                    break
                else:
                    print("✗ Неверный выбор")
                    continue

    selected_id = selected.get('id')
    selected_name = selected.get('nameRu')

    print(f"\n✓ Выбрано: {selected_name} (ID: {selected_id})")

    return selected_id, selected_name, gu_list


def bulk_import():
    """Массовый импорт документов"""

    print(f"\n{'='*80}")
    print("МАССОВЫЙ ИМПОРТ ДОКУМЕНТОВ В API")
    print(f"{'='*80}")

    # Шаг 1: Показать доступные документы
    docx_files = list_available_documents()
    if not docx_files:
        return

    # Шаг 2: Выбрать документы
    selected_files = select_documents(docx_files)
    if not selected_files:
        print("\n✗ Не выбрано ни одного файла")
        return

    # Шаг 3: Авторизация
    print(f"\n{'='*80}")
    print("АВТОРИЗАЦИЯ")
    print(f"{'='*80}\n")

    print("Вход в систему...")
    token, _ = login(IIN, PASSWORD)

    if not token:
        print("✗ Ошибка авторизации")
        return

    print("✓ Авторизация успешна")

    # Шаг 4: Выбрать режим импорта
    print(f"\n{'='*80}")
    print("РЕЖИМ ИМПОРТА")
    print(f"{'='*80}\n")

    print("1. Одна организация для всех файлов")
    print("2. Выбрать организацию для каждого файла отдельно")
    print("3. 🤖 Автоматическое определение организации для каждого файла")

    mode = input("\nВыберите режим (1, 2 или 3): ").strip()

    gu_list_cache = None
    company_map = {}  # файл -> (guId, guName)

    if mode == '1':
        # Одна организация для всех
        print("\nВыбор организации для всех файлов...")
        gu_id, gu_name, gu_list_cache = select_company_for_file(token, "все файлы", None)

        if not gu_id:
            print("✗ Не выбрана организация")
            return

        for f in selected_files:
            company_map[f] = (gu_id, gu_name)

    elif mode == '3':
        # Автоматическое определение для всех
        print("\n🤖 АВТОМАТИЧЕСКОЕ ОПРЕДЕЛЕНИЕ ОРГАНИЗАЦИЙ\n")

        # Загрузить список ГУ один раз
        gu_list = get_gu_list(token, parent_id=85750)
        if not gu_list:
            print("✗ Не удалось загрузить список организаций")
            return

        for f in selected_files:
            suggested_id, suggested_name, detected_org_name = org_mapping.suggest_gu_for_file(f.name, gu_list, f)

            if suggested_id:
                print(f"✓ {f.name}")
                print(f"  → Извлечено из документа: {detected_org_name}")
                print(f"  → Найдено в системе: {suggested_name} (ID: {suggested_id})")
                company_map[f] = (suggested_id, suggested_name)
            else:
                print(f"⚠ {f.name}")
                if detected_org_name:
                    print(f"  → Извлечено: {detected_org_name}")
                    print(f"  → Но не найдено точное совпадение в списке ГУ")
                else:
                    print(f"  → Не удалось извлечь название организации из документа")
                print(f"  → Потребуется ручной выбор...")

                # Ручной выбор для этого файла
                gu_id, gu_name, _ = select_company_for_file(token, f.name, gu_list, f)

                if gu_id:
                    company_map[f] = (gu_id, gu_name)
                else:
                    print(f"✗ Пропуск файла {f.name}")

    else:
        # Для каждого файла своя организация
        for f in selected_files:
            gu_id, gu_name, gu_list_cache = select_company_for_file(
                token, f.name, gu_list_cache, f
            )

            if not gu_id:
                print(f"✗ Пропуск файла {f.name}")
                continue

            company_map[f] = (gu_id, gu_name)

    if not company_map:
        print("\n✗ Не выбрано ни одной организации")
        return

    # Шаг 5: Проверка существующих записей
    print(f"\n{'='*80}")
    print("ПРОВЕРКА СУЩЕСТВУЮЩИХ ЗАПИСЕЙ")
    print(f"{'='*80}\n")

    print("Проверяю, есть ли уже записи для выбранных организаций...")

    # Получить список всех ID из import reports
    report_files = list((Path(__file__).parent.parent / "data").glob("import_report_*.txt"))
    existing_gu_ids = set()

    if report_files:
        import re
        for report_file in report_files:
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Найти все guId из отчетов
                # Формат в отчете: "GU ID: XXXXX"
                gu_matches = re.findall(r'GU ID:\s*(\d+)', content)
                existing_gu_ids.update(gu_matches)

    # Проверить каждую организацию
    duplicates = {}
    for f, (gu_id, gu_name) in company_map.items():
        if str(gu_id) in existing_gu_ids:
            duplicates[f] = (gu_id, gu_name)

    if duplicates:
        print(f"\n⚠ ВНИМАНИЕ: Найдены организации, для которых уже есть записи!")
        print(f"   Всего дубликатов: {len(duplicates)}\n")

        for f, (gu_id, gu_name) in duplicates.items():
            print(f"  ⚠ {f.name}")
            print(f"    → {gu_name} (GU ID: {gu_id})")
            print(f"    → Запись уже существует в системе")

        print(f"\nВарианты действий:")
        print(f"  1. Пропустить дубликаты (импортировать только новые)")
        print(f"  2. Удалить старые и создать новые (перезаписать)")
        print(f"  3. Отменить импорт")

        choice = input(f"\nВыберите (1/2/3): ").strip()

        if choice == '1':
            # Удалить дубликаты из company_map
            for f in duplicates.keys():
                del company_map[f]
            print(f"\n✓ Дубликаты будут пропущены")
            if not company_map:
                print("✗ Не осталось файлов для импорта")
                return
        elif choice == '2':
            print(f"\n⚠ Функция удаления старых записей будет добавлена")
            print(f"   Пока продолжаем с импортом (создастся дубликат)")
        elif choice == '3':
            print("\n✗ Импорт отменен")
            return
        else:
            print("\n✗ Неверный выбор. Импорт отменен")
            return
    else:
        print("✓ Дубликатов не найдено. Все записи новые.\n")

    # Шаг 6: Подтверждение
    print(f"\n{'='*80}")
    print("ПОДТВЕРЖДЕНИЕ ИМПОРТА")
    print(f"{'='*80}\n")

    print(f"Будет импортировано файлов: {len(company_map)}\n")
    for f, (gu_id, gu_name) in company_map.items():
        print(f"  {f.name}")
        print(f"    → {gu_name} (GU ID: {gu_id})")

    confirm = input(f"\nНачать импорт? (y/n): ").strip().lower()
    if confirm != 'y':
        print("\n✗ Импорт отменен")
        return

    # Шаг 6: Импорт
    print(f"\n{'='*80}")
    print("ПРОЦЕСС ИМПОРТА")
    print(f"{'='*80}\n")

    results = []

    for idx, (file_path, (gu_id, gu_name)) in enumerate(company_map.items(), 1):
        print(f"\n[{idx}/{len(company_map)}] Обработка: {file_path.name}")
        print("-" * 80)

        try:
            # Парсинг
            print("  📄 Парсинг документа...")
            data = universal_docx_parser.parse_docx_universal(file_path)

            print(f"    ✓ Общие положения: {len(data['general_provisions'])} символов")
            print(f"    ✓ Задачи: {len(data['tasks'])} элементов")
            print(f"    ✓ Права: {len(data['authorities_rights'])} элементов")
            print(f"    ✓ Обязанности: {len(data['authorities_responsibilities'])} элементов")
            print(f"    ✓ Функции: {len(data['functions'])} элементов")

            # Проверка качества данных
            rights_count = len(data['authorities_rights'])
            resp_count = len(data['authorities_responsibilities'])
            tasks_count = len(data['tasks'])
            functions_count = len(data['functions'])

            # Собрать список проблем
            issues = []
            warnings = []

            # Критические проблемы (пропустить файл)
            if rights_count == 0 and resp_count == 0:
                issues.append("отсутствуют права И обязанности")
            elif rights_count == 0:
                issues.append("отсутствуют права")
            elif resp_count == 0:
                issues.append("отсутствуют обязанности")

            # Предупреждения (импортировать, но показать предупреждение)
            if tasks_count == 0:
                warnings.append("отсутствуют задачи")
            if functions_count == 0:
                warnings.append("отсутствуют функции")

            # Показать статистику
            print(f"  📊 Статистика: Права={rights_count}, Обязанности={resp_count}, "
                  f"Задачи={tasks_count}, Функции={functions_count}")

            # Если есть критические проблемы - пропустить
            if issues:
                skip_reason = "; ".join(issues).capitalize()
                if warnings:
                    skip_reason += f" (также: {'; '.join(warnings)})"

                print(f"  ⚠ ПРОПУСК: {skip_reason}")
                print(f"  ⚠ Файл будет пропущен, чтобы избежать импорта неполных данных")
                results.append({
                    'file': file_path.name,
                    'status': 'skipped',
                    'skip_reason': skip_reason,
                    'gu_name': gu_name,
                    'rights': rights_count,
                    'responsibilities': resp_count,
                    'tasks': tasks_count,
                    'functions': functions_count
                })
                continue

            # Если есть только предупреждения - показать но продолжить
            if warnings:
                warning_msg = "; ".join(warnings).capitalize()
                print(f"  ⚠ ПРЕДУПРЕЖДЕНИЕ: {warning_msg}")
                print(f"  ℹ Файл будет импортирован, но данные могут быть неполными")

            # Подготовка payload
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

            # Отправка
            print("  🚀 Отправка в API...")
            result = create_position_department(token, payload)

            if result and result.get('success'):
                record_id = result.get('data')
                print(f"  ✓ УСПЕХ! ID записи: {record_id}")

                result_entry = {
                    'file': file_path.name,
                    'status': 'success',
                    'record_id': record_id,
                    'gu_id': gu_id,
                    'gu_name': gu_name,
                    'rights': rights_count,
                    'responsibilities': resp_count,
                    'tasks': tasks_count,
                    'functions': functions_count
                }

                # Добавить предупреждения если есть
                if warnings:
                    result_entry['warnings'] = '; '.join(warnings)

                results.append(result_entry)
            else:
                print(f"  ✗ ОШИБКА: {result}")
                results.append({
                    'file': file_path.name,
                    'status': 'error',
                    'error': str(result),
                    'gu_name': gu_name
                })

        except Exception as e:
            print(f"  ✗ ИСКЛЮЧЕНИЕ: {e}")
            results.append({
                'file': file_path.name,
                'status': 'exception',
                'error': str(e),
                'gu_name': gu_name
            })

    # Шаг 7: Итоговый отчет
    print(f"\n{'='*80}")
    print("ИТОГОВЫЙ ОТЧЕТ")
    print(f"{'='*80}\n")

    success_count = sum(1 for r in results if r['status'] == 'success')
    skipped_count = sum(1 for r in results if r['status'] == 'skipped')
    error_count = sum(1 for r in results if r['status'] not in ['success', 'skipped'])

    print(f"Всего обработано: {len(results)}")
    print(f"✓ Успешно импортировано: {success_count}")
    print(f"⚠ Пропущено (неполные данные): {skipped_count}")
    print(f"✗ Ошибок: {error_count}\n")

    if success_count > 0:
        print("УСПЕШНЫЕ ИМПОРТЫ:")
        print("-" * 80)
        for r in results:
            if r['status'] == 'success':
                print(f"  ✓ {r['file']}")
                print(f"    → {r['gu_name']}")
                print(f"    → ID: {r['record_id']}")
                print(f"    → Права: {r.get('rights', 0)}, Обязанности: {r.get('responsibilities', 0)}, "
                      f"Задачи: {r.get('tasks', 0)}, Функции: {r.get('functions', 0)}")
                if r.get('warnings'):
                    print(f"    ⚠ Предупреждение: {r['warnings']}")
                print(f"    → URL: https://planning.gov.kz/rgffront#/rgffront/filter/positions/department/{r['record_id']}/edit")
                print()

    if skipped_count > 0:
        print("\nПРОПУЩЕННЫЕ ФАЙЛЫ (требуют доработки парсера):")
        print("-" * 80)
        for r in results:
            if r['status'] == 'skipped':
                print(f"  ⚠ {r['file']}")
                print(f"    → {r['gu_name']}")
                print(f"    → Причина: {r['skip_reason']}")
                print(f"    → Права: {r.get('rights', 0)}, Обязанности: {r.get('responsibilities', 0)}, "
                      f"Задачи: {r.get('tasks', 0)}, Функции: {r.get('functions', 0)}")
                print()

    if error_count > 0:
        print("\nОШИБКИ:")
        print("-" * 80)
        for r in results:
            if r['status'] not in ['success', 'skipped']:
                print(f"  ✗ {r['file']}")
                print(f"    → {r['gu_name']}")
                print(f"    → Ошибка: {r.get('error', 'Неизвестная ошибка')}")
                print()

    # Сохранение отчета
    report_file = Path(__file__).parent.parent / "data" / f"import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("ОТЧЕТ О МАССОВОМ ИМПОРТЕ\n")
        f.write("=" * 80 + "\n")
        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Всего файлов: {len(results)}\n")
        f.write(f"✓ Успешно импортировано: {success_count}\n")
        f.write(f"⚠ Пропущено (неполные данные): {skipped_count}\n")
        f.write(f"✗ Ошибок: {error_count}\n\n")

        # Успешные импорты
        if success_count > 0:
            f.write("\n" + "=" * 80 + "\n")
            f.write("УСПЕШНЫЕ ИМПОРТЫ:\n")
            f.write("=" * 80 + "\n")
            for r in results:
                if r['status'] == 'success':
                    f.write(f"\n{r['file']}\n")
                    f.write(f"  Организация: {r['gu_name']}\n")
                    f.write(f"  GU ID: {r.get('gu_id', 'N/A')}\n")
                    f.write(f"  ID записи: {r['record_id']}\n")
                    f.write(f"  Извлечено данных:\n")
                    f.write(f"    - Права: {r.get('rights', 0)}\n")
                    f.write(f"    - Обязанности: {r.get('responsibilities', 0)}\n")
                    f.write(f"    - Задачи: {r.get('tasks', 0)}\n")
                    f.write(f"    - Функции: {r.get('functions', 0)}\n")
                    if r.get('warnings'):
                        f.write(f"  ⚠ Предупреждение: {r['warnings']}\n")
                    f.write(f"  URL: https://planning.gov.kz/rgffront#/rgffront/filter/positions/department/{r['record_id']}/edit\n")

        # Пропущенные файлы
        if skipped_count > 0:
            f.write("\n" + "=" * 80 + "\n")
            f.write("ПРОПУЩЕННЫЕ ФАЙЛЫ (требуют доработки парсера):\n")
            f.write("=" * 80 + "\n")
            for r in results:
                if r['status'] == 'skipped':
                    f.write(f"\n{r['file']}\n")
                    f.write(f"  Организация: {r['gu_name']}\n")
                    f.write(f"  Причина: {r['skip_reason']}\n")
                    f.write(f"  Извлечено данных:\n")
                    f.write(f"    - Права: {r.get('rights', 0)}\n")
                    f.write(f"    - Обязанности: {r.get('responsibilities', 0)}\n")
                    f.write(f"    - Задачи: {r.get('tasks', 0)}\n")
                    f.write(f"    - Функции: {r.get('functions', 0)}\n")

        # Ошибки
        if error_count > 0:
            f.write("\n" + "=" * 80 + "\n")
            f.write("ОШИБКИ:\n")
            f.write("=" * 80 + "\n")
            for r in results:
                if r['status'] not in ['success', 'skipped']:
                    f.write(f"\n{r['file']}\n")
                    f.write(f"  Организация: {r['gu_name']}\n")
                    f.write(f"  Статус: {r['status']}\n")
                    f.write(f"  Ошибка: {r.get('error', 'N/A')}\n")

    print(f"\n✓ Отчет сохранен: {report_file}")
    print(f"\n{'='*80}")


if __name__ == "__main__":
    try:
        bulk_import()
    except KeyboardInterrupt:
        print("\n\n✗ Импорт прерван пользователем")
    except Exception as e:
        print(f"\n\n✗ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
