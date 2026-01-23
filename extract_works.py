import pdfplumber
import pytesseract
import pandas as pd
import re

# ===== НАСТРОЙКИ =====

PDF_PATH = "Полжения Отдел ООР.pdf"
OUTPUT_XLSX = "sections_kazakh_clean.xlsx"

# Казахские буквы (дополнительные к русским): Ә, Ғ, Қ, Ң, Ө, Ұ, Ү, Һ, І
# Полный набор: А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі

# Главные разделы: "1. Жалпы ереже", "2. Бөлімнің негізгі міндеттері"
# Паттерн: число (1-9) + точка + пробел + слова с заглавной буквы
MAIN_SECTION_RE = re.compile(
    r"(?<!\d)(\d)\.\s+([А-ЯЁӘҒҚҢӨҰҮҺІБЖНМКХЕӘа-яёәғқңөұүһі][а-яёәғқңөұүһіА-ЯЁӘҒҚҢӨҰҮҺІүңқ\s]+?)(?=\s+\d+\.\d+\.|\s+\d\.\s+[А-ЯӘҒҚҢӨҰҮҺІБЖНМКХЕ]|$)"
)

# ===== ФУНКЦИИ =====

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


def parse_sections(text: str):
    sections = []
    matches = list(MAIN_SECTION_RE.finditer(text))

    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        body = text[start:end].strip()

        if not is_garbage(body):
            section_num = match.group(1)
            section_title = match.group(2).strip()
            sections.append({
                "section": f"{section_num}. {section_title}",
                "content": body
            })

    return sections


# ===== ОСНОВНОЙ ПРОЦЕСС =====

rows = []

with pdfplumber.open(PDF_PATH) as pdf:
    full_text = ""

    for page_num, page in enumerate(pdf.pages, start=1):
        # Работаем как со СКАНОМ
        image = page.to_image(resolution=300).original
        text = pytesseract.image_to_string(image, lang="kaz+rus")
        full_text += text + "\n"

clean_text = keep_cyrillic_kazakh(full_text)

sections = parse_sections(clean_text)
print(clean_text[:2000])

for sec in sections:
    rows.append({
        "file": PDF_PATH,
        "section": sec["section"],
        "content": sec["content"]
    })

df = pd.DataFrame(rows)
df.to_excel(OUTPUT_XLSX, index=False)

print(f"Готово. Найдено разделов: {len(df)}")
print(f"Файл сохранён: {OUTPUT_XLSX}")
