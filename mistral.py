import pdfplumber
import pandas as pd
import re
import base64
import requests
import time
from io import BytesIO
from PIL import Image

# ===== НАСТРОЙКИ =====

# GEMINI_API_KEY="AIzaSyBUbZGaPsd4hrxgNHRPNcfbS1iBncqCVMY"
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     st.error("⚠️ API ключ Gemini не настроен. Проверьте ваш файл .env или определите ключ в коде.")
#     st.stop()

# # Configure Gemini
# genai.configure(api_key=GEMINI_API_KEY)
# model_gemini = genai.GenerativeModel('gemini-2.5-flash')  # Make sure this is the correct model

MISTRAL_API_KEY = "QqkMxELY0YVGkCx17Vya04Sq9nGvCahu"
MISTRAL_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"

PDF_PATH = "Полжения Отдел ООР.pdf"
OUTPUT_XLSX = "sections_russian_only.xlsx"

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
            print(f"  Страница {page_num}: {len(text)} символов")
            return text
        elif response.status_code == 429:
            wait_time = (attempt + 1) * 5
            print(f"  Rate limit, ждём {wait_time} сек...")
            time.sleep(wait_time)
        else:
            print(f"  Ошибка страница {page_num}: {response.status_code}")
            print(f"  {response.text}")
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

print("Извлекаем текст через Mistral Vision API...")

with pdfplumber.open(PDF_PATH) as pdf:
    full_text = ""

    for page_num, page in enumerate(pdf.pages, start=1):
        image = page.to_image(resolution=200).original  # Меньше разрешение = меньше размер
        text = extract_text_with_mistral(image, page_num)
        full_text += text + "\n"
        time.sleep(5)  # Пауза между запросами чтобы не превысить лимит

clean_text = keep_cyrillic_kazakh(full_text)

# print(clean_text[:2000])

rows = parse_sections_hierarchical(clean_text)

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
    # Проверяем казахские буквы
    if any(c in text for c in "ӘәҒғҚқҢңӨөҰұҮүҺһІі"):
        return "kaz"
    return "rus"

# Добавляем язык к каждой строке
for row in rows:
    row["language"] = detect_language(row["main_section"] + " " + row["content"])

df = pd.DataFrame(rows)
# Переставляем колонки: file, language, main_section, subsection, content
df.insert(0, "file", PDF_PATH)
cols = ["file", "language", "main_section", "subsection", "content"]
df = df[cols]

# Сохраняем subsection как текст (чтобы 1.1 не стало 1.10)
with pd.ExcelWriter(OUTPUT_XLSX, engine='openpyxl') as writer:
    df.to_excel(writer, index=False)
    worksheet = writer.sheets['Sheet1']
    # Форматируем колонку subsection как текст
    for row in range(2, len(df) + 2):
        cell = worksheet.cell(row=row, column=3)  # subsection - 3-я колонка
        cell.number_format = '@'  # текстовый формат

print(f"Готово. Найдено разделов: {len(df)}")
print(f"Файл сохранён: {OUTPUT_XLSX}")
