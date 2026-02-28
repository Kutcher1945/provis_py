"""
Маппинг организаций для автоматического определения GU ID

Основано на data/guid.md и data/guid_names.txt
Используется для автоматического определения организации по имени файла или содержимому документа
"""

import re
from pathlib import Path
from docx import Document


# Маппинг аббревиатура → ключевые слова для поиска организации
ABBREVIATION_TO_SEARCH = {
    'УДР': 'развития дорожной инфраструктуры',
    'УОДДиПТ': 'организации дорожного движения',
    'УЭиФ': 'экономики и финансов',
    'УМПиТиГО': 'мобилизационной подготовке',
    'УМПТиГР': 'мобилизационной подготовке',  # Вариант аббревиатуры
    'УКиЖИ': 'коммунальной инфраструктуры',
    'УКИЖИ': 'коммунальной инфраструктуры',  # Вариант без "и"
    'УРОП': 'развития общественных пространств',
    'УЗСП': 'занятости и социальных программ',
    'УМП': 'молодежной политики',
    'УЭиОС': 'экологии и окружающей среды',
    'УОЗ': 'общественного здравоохранения',
    'УЭВ': 'энергетики и водоснабжения',
    'УЭиВ': 'энергетики и водоснабжения',  # Вариант аббревиатуры
    'УСтроительства': 'строительства города',
    'УДРел': 'делам религий',
    'УЦ': 'цифровизации',
    'УПиИ': 'предпринимательства и инвестиций',
    'УГК': 'градостроительного контроля',
    'УК': 'культуры города',
    'УС': 'спорта города',
    'УТур': 'туризма',
    'УТ': 'туризма',  # Вариант аббревиатуры
    'УГА': 'государственных активов',
    'УЗО': 'земельных отношений',
    'УО': 'образования города',
    'УВП': 'внутренней политики',
    'УАиГ': 'архитектуры и градостроительства',
    'Аппарат': 'Аппарат акима города',
}


def extract_abbreviation_from_filename(filename):
    """Извлечь аббревиатуру из имени файла

    Примеры:
        'Положение УДР.docx' → 'УДР'
        'Положение УМПТиГР.docx' → 'УМПТиГР'
        'Положение о «Аппарат акима города Алматы».docx' → 'Аппарат'

    Args:
        filename (str): Имя файла

    Returns:
        str or None: Аббревиатура или None если не найдена
    """
    # Убрать расширение
    name = filename.replace('.docx', '').replace('.DOCX', '')

    # Паттерны для извлечения
    patterns = [
        r'Положение\s+([А-ЯЁа-яё]+(?:и[А-ЯЁ][А-ЯЁ])?)',  # Положение УМПиТиГО
        r'Положение\s+о\s+«(Аппарат)',  # Положение о «Аппарат акима...»
    ]

    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            abbr = match.group(1)
            # Проверить что это известная аббревиатура
            if abbr in ABBREVIATION_TO_SEARCH:
                return abbr

    return None


def extract_org_name_from_docx(file_path):
    """Извлечь название организации из заголовка документа

    Args:
        file_path (Path or str): Путь к .docx файлу

    Returns:
        str or None: Название организации или None
    """
    try:
        doc = Document(file_path)

        # Читаем первые несколько параграфов (обычно название в самом начале)
        for para in doc.paragraphs[:5]:
            text = para.text.strip()

            # Ищем текст в кавычках «...»
            match = re.search(r'«([^»]+)»', text)
            if match:
                org_name = match.group(1).strip()
                # Убедимся что это похоже на название организации
                if 'управление' in org_name.lower() or 'аппарат' in org_name.lower():
                    return org_name

        return None
    except Exception as e:
        print(f"  ⚠ Ошибка при чтении файла: {e}")
        return None


def find_gu_by_abbreviation(abbreviation, gu_list):
    """Найти организацию в списке по аббревиатуре

    Args:
        abbreviation (str): Аббревиатура (например, 'УДР')
        gu_list (list): Список организаций из API

    Returns:
        tuple: (gu_id, gu_name) или (None, None)
    """
    if abbreviation not in ABBREVIATION_TO_SEARCH:
        return None, None

    search_keywords = ABBREVIATION_TO_SEARCH[abbreviation]

    # Ищем организацию по ключевым словам
    for gu in gu_list:
        gu_name = gu.get('nameRu', '')
        gu_name_lower = gu_name.lower()

        if search_keywords.lower() in gu_name_lower:
            return gu.get('id'), gu.get('nameRu')

    return None, None


def find_gu_by_org_name(org_name, gu_list):
    """Найти организацию в списке по полному названию

    Args:
        org_name (str): Полное название организации
        gu_list (list): Список организаций из API

    Returns:
        tuple: (gu_id, gu_name) или (None, None)
    """
    org_name_lower = org_name.lower()

    # Искать точное совпадение
    for gu in gu_list:
        gu_name = gu.get('nameRu', '')
        gu_name_lower = gu_name.lower()

        # Проверка на точное совпадение (игнорируя КГУ, кавычки и т.д.)
        gu_core = gu_name_lower
        for prefix in ['кгу "', 'кгу «', 'кгу', '"', '«', '»']:
            gu_core = gu_core.replace(prefix, '')
        gu_core = gu_core.strip().strip('"»')

        if org_name_lower in gu_core or gu_core in org_name_lower:
            return gu.get('id'), gu.get('nameRu')

    # Если точного совпадения нет, ищем по ключевым словам
    keywords = []
    for word in org_name_lower.split():
        if len(word) > 4 and word not in ['города', 'алматы', 'управление']:
            keywords.append(word)

    # Ищем ГУ с максимальным совпадением ключевых слов
    best_match = None
    max_matches = 0

    for gu in gu_list:
        gu_name_lower = gu.get('nameRu', '').lower()
        matches = sum(1 for keyword in keywords if keyword in gu_name_lower)

        if matches > max_matches and matches >= len(keywords) // 2:
            max_matches = matches
            best_match = gu

    if best_match:
        return best_match.get('id'), best_match.get('nameRu')

    return None, None


def load_guid_mapping(guid_file_path=None):
    """Загрузить прямой маппинг GUID → Name из файла

    Args:
        guid_file_path (Path or str, optional): Путь к файлу guid_names.txt

    Returns:
        dict: {guid: name} маппинг
    """
    if guid_file_path is None:
        guid_file_path = Path(__file__).parent / 'data' / 'guid_names.txt'

    guid_mapping = {}

    try:
        with open(guid_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Пропустить заголовки и пустые строки
                if not line or line.startswith('GUID') or line.startswith('='):
                    continue

                # Формат: GUID\tName
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    guid = parts[0].strip()
                    name = parts[1].strip()
                    if guid and name:
                        guid_mapping[guid] = name

    except FileNotFoundError:
        pass  # Файл не обязателен, используем fallback методы

    return guid_mapping


def build_keyword_index(guid_mapping):
    """Построить индекс ключевые слова → GUID для быстрого поиска

    Args:
        guid_mapping (dict): {guid: name} маппинг

    Returns:
        dict: {keyword: [(guid, name, score)]} где score - релевантность ключевого слова
    """
    keyword_index = {}

    for guid, name in guid_mapping.items():
        name_lower = name.lower()

        # Извлечь значимые ключевые слова из названия
        # Убрать общие префиксы
        clean_name = name_lower
        for prefix in ['кгу "', 'кгу «', 'кгу', '"', '«', '»', 'департамент', 'управление']:
            clean_name = clean_name.replace(prefix, '')

        # Разбить на слова
        words = clean_name.split()

        # Фильтровать незначимые слова
        stop_words = {'города', 'алматы', 'по', 'и', 'г', 'г.', 'района', 'акима', 'аппарат'}
        significant_words = [w.strip('.",;:') for w in words if w not in stop_words and len(w) > 2]

        # Добавить в индекс
        for word in significant_words:
            if word not in keyword_index:
                keyword_index[word] = []
            # Score: чем короче слово, тем выше уникальность (обычно)
            # Но специальные длинные слова (>10 букв) очень уникальны
            score = len(word) if len(word) > 10 else 5
            keyword_index[word].append((guid, name, score))

    return keyword_index


def suggest_gu_for_file(filename, gu_list, file_path=None, use_guid_mapping=True):
    """Автоматически предложить организацию для файла

    Использует три стратегии (в порядке приоритета):
    1. Прямой GUID маппинг из guid_names.txt (самый быстрый, самый точный)
    2. Извлечение аббревиатуры из имени файла (быстро, точно)
    3. Извлечение полного названия из документа (медленнее, универсально)

    Args:
        filename (str): Имя файла
        gu_list (list): Список организаций из API
        file_path (Path or str, optional): Полный путь к файлу
        use_guid_mapping (bool): Использовать прямой GUID маппинг из файла (по умолчанию True)

    Returns:
        tuple: (gu_id, gu_name, detected_source) или (None, None, detected_source)
            detected_source - строка описывающая откуда было извлечено название
    """
    from pathlib import Path

    if file_path is None:
        file_path = Path(__file__).parent / 'data' / filename

    detected_source = None

    # Стратегия 0: Прямой GUID маппинг (если доступен)
    if use_guid_mapping:
        guid_mapping = load_guid_mapping()
        if guid_mapping:
            # Попробовать по аббревиатуре
            abbr = extract_abbreviation_from_filename(filename)
            if abbr and abbr in ABBREVIATION_TO_SEARCH:
                keywords = ABBREVIATION_TO_SEARCH[abbr]
                # Искать в GUID маппинге
                for guid, name in guid_mapping.items():
                    if keywords.lower() in name.lower():
                        # Найти соответствующий GU в списке API
                        for gu in gu_list:
                            if str(gu.get('id')) == str(guid):
                                detected_source = f"[GUID mapping: {abbr} → {guid}]"
                                return gu.get('id'), gu.get('nameRu'), detected_source

    # Стратегия 1: Поиск по аббревиатуре из имени файла
    abbr = extract_abbreviation_from_filename(filename)
    if abbr:
        gu_id, gu_name = find_gu_by_abbreviation(abbr, gu_list)
        if gu_id:
            detected_source = f"[Аббревиатура из имени файла: {abbr}]"
            return gu_id, gu_name, detected_source

    # Стратегия 2: Извлечение из документа
    org_name = extract_org_name_from_docx(file_path)
    if org_name:
        detected_source = org_name
        gu_id, gu_name = find_gu_by_org_name(org_name, gu_list)
        if gu_id:
            return gu_id, gu_name, detected_source

    return None, None, detected_source
