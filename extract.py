import pdfplumber
import pandas as pd
import re
import base64
import requests
import time
import os
import glob
import hashlib
import logging
from io import BytesIO
from PIL import Image
from datetime import datetime
import google.generativeai as genai
import psycopg2
from psycopg2.extras import execute_values
from tqdm import tqdm
from colorama import init, Fore, Style

# Инициализация colorama
init(autoreset=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format=f'{Fore.CYAN}%(asctime)s{Style.RESET_ALL} | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ===== НАСТРОЙКИ =====

# Выбор API: "gemini" или "mistral"
USE_API = "gemini"

GEMINI_API_KEY = "AIzaSyDZ64jYSAwJraVBzehE0SAIIsyV6Fgz96E"
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

MISTRAL_API_KEY = "QqkMxELY0YVGkCx17Vya04Sq9nGvCahu"
MISTRAL_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"

# Путь к папке с PDF файлами
PDF_PATH = "pdfs/Положения"

# PostgreSQL настройки
DB_CONFIG = {
    "host": "10.100.200.151",
    "port": 5432,
    "user": "analyst",
    "password": "4HPzQt2HyU",
    "dbname": "analytical_center_db"
}

def get_db_connection():
    """Подключение к PostgreSQL"""
    return psycopg2.connect(**DB_CONFIG)

def get_file_hash(filepath):
    """Вычисляем SHA256 хеш файла"""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def get_pdf_files(path):
    """Получаем список PDF файлов рекурсивно"""
    if os.path.isfile(path):
        return [path]
    elif os.path.isdir(path):
        # Рекурсивный поиск всех PDF
        return glob.glob(os.path.join(path, "**/*.pdf"), recursive=True)
    else:
        logger.error(f"Путь не найден: {path}")
        return []

def file_already_processed(conn, file_hash):
    """Проверяем, обработан ли файл"""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM provisions_source_files WHERE file_hash = %s", (file_hash,))
        result = cur.fetchone()
        return result[0] if result else None

def get_department_from_path(filepath):
    """Извлекаем название департамента из пути к файлу"""
    # pdfs/Положения/УГА/file.pdf -> УГА
    parts = filepath.split(os.sep)
    # Ищем папку после "Положения"
    for i, part in enumerate(parts):
        if part == "Положения" and i + 1 < len(parts) - 1:
            return parts[i + 1]
    # Если структура другая, берём родительскую папку
    if len(parts) >= 2:
        return parts[-2]
    return None


def insert_source_file(conn, file_name, file_hash, page_count, language_hint="mixed", department=None):
    """Добавляем файл в справочник"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO provisions_source_files (file_name, file_hash, page_count, language_hint, processed_at, departament)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (file_name, file_hash, page_count, language_hint, datetime.now(), department))
        file_id = cur.fetchone()[0]
        conn.commit()
        return file_id

def insert_sections(conn, file_id, sections):
    """Добавляем секции в БД"""
    if not sections:
        return

    with conn.cursor() as cur:
        data = [
            (file_id, s["language"], s["main_section"], s["subsection"], s["content"], s.get("page_number"))
            for s in sections
        ]
        execute_values(cur, """
            INSERT INTO provisions_document_sections
            (source_file_id, language, main_section, subsection, content, page_number)
            VALUES %s
        """, data)
        conn.commit()

# Казахские буквы (дополнительные к русским): Ә, Ғ, Қ, Ң, Ө, Ұ, Ү, Һ, І
# Полный набор: А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі

# Главные разделы: "1. Жалпы ереже", "2. Бөлімнің негізгі міндеттері"
# (?<![.\d]) - не после точки или цифры (чтобы не ловить 3.7. как секцию 7)
# Заголовок ДОЛЖЕН начинаться с заглавной буквы [А-ЯЁӘҒҚҢӨҰҮҺІ]
MAIN_SECTION_RE = re.compile(
    r"(?<![.\d])(\d)\.\s+([А-ЯЁӘҒҚҢӨҰҮҺІ][а-яёәғқңөұүһіА-ЯЁӘҒҚҢӨҰҮҺІүңқ\s]+?)(?=\.?\s+\d+\.\d+\.|\.?\s+\d{2}\.|\.?\s+\d\.\s+[А-ЯӘҒҚҢӨҰҮҺІ]|$)"
)

# Подразделы: "1.1.", "2.1.", "3.2." и т.д.
SUBSECTION_RE = re.compile(
    r"(\d+)\.(\d+)\.\s*"
)

# ===== ФУНКЦИИ =====

def image_to_base64(image: Image.Image) -> str:
    """Конвертируем PIL Image в base64 строку (JPEG для меньшего размера)"""
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=75)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def extract_text_with_gemini(image: Image.Image, page_num: int) -> str:
    """Извлекаем текст через Gemini Vision API"""
    prompt = """Извлеки ВЕСЬ текст с этой страницы документа.
Это официальный документ на казахском и русском языках.
Игнорируй подписи и печати - извлекай только печатный текст.
Сохраняй нумерацию разделов (1., 2., 3.) и подразделов (1.1., 1.2., 2.1.).
Выведи только текст, без комментариев."""

    try:
        response = gemini_model.generate_content([prompt, image])
        text = response.text
        logger.debug(f"Страница {page_num}: {len(text)} символов")
        return text
    except Exception as e:
        logger.warning(f"Ошибка страница {page_num}: {e}")
        return ""


def extract_text_with_mistral(image: Image.Image, page_num: int) -> str:
    """
    Извлекаем текст с изображения через Mistral Vision API.
    """
    img_base64 = image_to_base64(image)

    payload = {
        "model": "pixtral-12b-2409",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Извлеки ТОЛЬКО РУССКИЙ текст с этой страницы документа.
Это официальный документ - есть казахская и русская версии.
Извлекай ТОЛЬКО русскую часть, игнорируй казахский текст полностью.
Игнорируй подписи и печати.
Сохраняй нумерацию разделов (1., 2., 3.) и подразделов (1.1., 1.2., 2.1.).
Выведи только русский текст, без комментариев."""
                    },
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{img_base64}"
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 4096
    }

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    for attempt in range(3):
        response = requests.post(MISTRAL_ENDPOINT, json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            text = result["choices"][0]["message"]["content"]
            logger.debug(f"Страница {page_num}: {len(text)} символов")
            return text
        elif response.status_code == 429:
            wait_time = (attempt + 1) * 5
            logger.warning(f"Rate limit, ждём {wait_time} сек...")
            time.sleep(wait_time)
        else:
            logger.error(f"Ошибка страница {page_num}: {response.status_code}")
            return ""

    return ""


def keep_cyrillic_kazakh(text: str) -> str:
    """
    Оставляем кириллицу (включая казахские буквы), цифры и базовую пунктуацию
    """
    # Unicode ranges: \u0400-\u04FF (Cyrillic) + казахские специфичные символы
    text = re.sub(r"[^\u0400-\u04FFӘәҒғҚқҢңӨөҰұҮүҺһІі0-9\.\,\-\(\)\s]", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def is_garbage(text: str) -> bool:
    """
    Отсекаем OCR-мусор:
    - слишком короткий текст
    - слишком много одиночных букв
    """
    if len(text) < 80:
        return True

    # Включаем казахские буквы
    letters = re.findall(r"[А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]", text)
    single_letters = re.findall(r"\b[А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]\b", text)

    if letters and len(single_letters) / len(letters) > 0.35:
        return True

    return False


def parse_sections_hierarchical(text: str):
    """
    Парсим текст в иерархическую структуру:
    - Главные разделы (1., 2., 3.)
    - Подразделы (1.1., 1.2., 2.1.)
    """
    rows = []
    main_matches = list(MAIN_SECTION_RE.finditer(text))

    for i, main_match in enumerate(main_matches):
        main_num = main_match.group(1)
        main_title = main_match.group(2).strip()
        main_section = f"{main_num}. {main_title}"

        # Получаем текст этого раздела
        start = main_match.end()
        end = main_matches[i + 1].start() if i + 1 < len(main_matches) else len(text)
        section_body = text[start:end]

        # Ищем подразделы внутри этого раздела
        sub_matches = list(SUBSECTION_RE.finditer(section_body))

        if not sub_matches:
            # Нет подразделов - сохраняем весь текст
            if not is_garbage(section_body):
                rows.append({
                    "main_section": main_section,
                    "subsection": "",
                    "content": section_body.strip()
                })
        else:
            # Есть подразделы - разбиваем
            for j, sub_match in enumerate(sub_matches):
                # Добавляем пробел чтобы Excel не конвертировал в число
                sub_num = f"{sub_match.group(1)}.{sub_match.group(2)}."

                # Контент подраздела - от конца номера до начала следующего
                sub_start = sub_match.end()
                sub_end = sub_matches[j + 1].start() if j + 1 < len(sub_matches) else len(section_body)
                sub_content = section_body[sub_start:sub_end].strip()

                if sub_content and len(sub_content) > 10:
                    rows.append({
                        "main_section": main_section,
                        "subsection": sub_num,
                        "content": sub_content
                    })

    return rows


# ===== ОСНОВНОЙ ПРОЦЕСС =====

# Определяем язык по ключевым словам
russian_keywords = ["Общие", "Основные", "Права", "Ответственность", "Функции", "Задачи", "отдела"]
kazakh_keywords = ["Жалпы", "Бөлім", "негізгі", "міндеттері", "қызметтері", "құқықтары", "жауапкершілігі"]

def detect_language(text):
    """Определяем язык: kaz или rus"""
    text_lower = text.lower()
    if any(kw.lower() in text_lower for kw in kazakh_keywords):
        return "kaz"
    if any(kw.lower() in text_lower for kw in russian_keywords):
        return "rus"
    if any(c in text for c in "ӘәҒғҚқҢңӨөҰұҮүҺһІі"):
        return "kaz"
    return "rus"


# ===== ОСНОВНОЙ ПРОЦЕСС =====

if __name__ == "__main__":
    pdf_files = get_pdf_files(PDF_PATH)

    logger.info(f"{Fore.GREEN}Найдено PDF файлов: {len(pdf_files)}{Style.RESET_ALL}")
    logger.info(f"Используем API: {Fore.YELLOW}{USE_API.upper()}{Style.RESET_ALL}")

    # Подключаемся к БД
    conn = get_db_connection()
    logger.info(f"{Fore.GREEN}✅ Подключение к БД установлено{Style.RESET_ALL}")

    total_files = 0
    total_sections = 0
    skipped_files = 0

    # Основной цикл с прогресс-баром
    for pdf_file in tqdm(pdf_files, desc=f"{Fore.CYAN}Обработка PDF{Style.RESET_ALL}", unit="file"):
        file_name = os.path.basename(pdf_file)
        file_hash = get_file_hash(pdf_file)

        # Проверяем, не обработан ли файл
        existing_id = file_already_processed(conn, file_hash)
        if existing_id:
            logger.debug(f"⏭️  Пропускаем (уже в БД): {file_name}")
            skipped_files += 1
            continue

        department = get_department_from_path(pdf_file)
        logger.info(f"{Fore.BLUE}📄 Обрабатываем: {file_name} [{Fore.YELLOW}{department}{Fore.BLUE}]{Style.RESET_ALL}")

        try:
            with pdfplumber.open(pdf_file) as pdf:
                page_count = len(pdf.pages)
                full_text = ""

                # Прогресс-бар для страниц
                for page_num, page in enumerate(tqdm(pdf.pages, desc="  Страницы", leave=False, unit="стр"), start=1):
                    image = page.to_image(resolution=200).original

                    if USE_API == "gemini":
                        text = extract_text_with_gemini(image, page_num)
                    else:
                        text = extract_text_with_mistral(image, page_num)

                    full_text += text + "\n"
                    time.sleep(4)  # Пауза между запросами

            clean_text = keep_cyrillic_kazakh(full_text)
            rows = parse_sections_hierarchical(clean_text)

            # Добавляем язык к каждой строке
            for row in rows:
                row["language"] = detect_language(row["main_section"] + " " + row["content"])

            # Определяем основной язык файла
            kaz_count = sum(1 for r in rows if r["language"] == "kaz")
            rus_count = sum(1 for r in rows if r["language"] == "rus")
            if kaz_count > 0 and rus_count > 0:
                language_hint = "mixed"
            elif kaz_count > rus_count:
                language_hint = "kaz"
            else:
                language_hint = "rus"

            # Сохраняем в БД
            file_id = insert_source_file(conn, file_name, file_hash, page_count, language_hint, department)
            insert_sections(conn, file_id, rows)

            total_files += 1
            total_sections += len(rows)
            logger.info(f"{Fore.GREEN}  ✅ Сохранено: {len(rows)} разделов (file_id={file_id}){Style.RESET_ALL}")

        except Exception as e:
            logger.error(f"{Fore.RED}  ❌ Ошибка: {e}{Style.RESET_ALL}")
            conn.rollback()

    conn.close()

    # Итоговая статистика
    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    logger.info(f"{Fore.GREEN}📊 ИТОГО:{Style.RESET_ALL}")
    logger.info(f"   Обработано файлов: {Fore.GREEN}{total_files}{Style.RESET_ALL}")
    logger.info(f"   Пропущено (дубли): {Fore.YELLOW}{skipped_files}{Style.RESET_ALL}")
    logger.info(f"   Извлечено разделов: {Fore.GREEN}{total_sections}{Style.RESET_ALL}")
