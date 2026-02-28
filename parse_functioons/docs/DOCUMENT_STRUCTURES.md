# Document Structure Analysis

## Overview

All 25+ Положение documents follow **common patterns** but use **different organizational structures**. The universal parser automatically detects and handles all structure types.

## Structure Types

### 1️⃣ CHAPTER-BASED (11 documents)

**Pattern:**
- Uses **"Глава 1", "Глава 2", "Глава 3"** markers
- Sections: "12. Задачи", "13. Полномочия", "14. Функции"

**Documents:**
- Положение УАиГ.docx
- Положение УДР.docx
- Положение УМП.docx
- Положение УМПТиГР.docx
- Положение УОДДиПТ.docx
- Положение УОЗ.docx
- Положение УРДИ.docx
- Положение УРОП.docx
- Положение УТ.docx
- Положение УЭиВ.docx
- Положение УЭиОС.docx

**Structure:**
```
Глава 1. Общие положения
  1. ...
  2. ...
  ...

Глава 2. Задачи и полномочия
  12. Задачи:
    1) task 1
    2) task 2
    ...

  13. Полномочия:
    1) права:
      1. right 1
      2. right 2
    2) обязанности:
      1. responsibility 1
      2. responsibility 2

  14. Функции:
    1) function 1
    2) function 2
    ...

Глава 3. Статус, полномочия первого руководителя
  ...

Глава 4. Имущество
  ...

Глава 5. Реорганизация
  ...
```

### 2️⃣ NUMBERED SECTIONS (8 documents)

**Pattern:**
- Uses **bold numbered headers**: "1. Общие положения", "2. Задачи и полномочия"
- Sections: "14. Задачи", "15. Полномочия", "16. Функции"
- **Important:** права and обязанности items are **NOT numbered** - just paragraphs

**Documents:**
- Положение УВП 2025.docx
- Положение УВП 2026.docx
- Положение УГК.docx
- Положение УЗО.docx
- Положение УЗСП.docx
- Положение УО.docx
- Положение УЭиФ.docx
- Положение о «Аппарат акима города Алматы».docx

**Structure:**
```
1. Общие положения
  1. ...
  2. ...
  ...

2. Задачи и полномочия Управления
  14. Задачи:
    1) task 1
    2) task 2
    ...

  15. Полномочия:
    1) права:
      paragraph 1 (NOT numbered)
      paragraph 2 (NOT numbered)
      ...
    2) обязанности:
      paragraph 1 (NOT numbered)
      paragraph 2 (NOT numbered)
      ...

  16. Функции:
    1) function 1
    2) function 2
    ...

3. Статус, полномочия первого руководителя
  ...

4. Имущество
  ...

5. Реорганизация
  ...
```

### 3️⃣ CUSTOM/UNKNOWN (4 documents)

**Pattern:**
- Mixed or unique structure
- All sections combined in section 2
- Requires keyword-based extraction

**Documents:**
- Положение УГА.docx
- Положение УК.docx
- Положение УКИЖИ.docx
- Положение УСтроительства.docx

**Note:** These may require manual review or enhancement of the parser.

## Common Sections (All Documents)

Every document contains these sections:

1. **Общие положения** (General Provisions)
   - Basic information about the government unit
   - Legal framework
   - Organizational structure

2. **Задачи** (Tasks)
   - Main responsibilities and objectives
   - Numbered with `1)`, `2)`, `3)`

3. **Полномочия** (Authorities)
   - Divided into:
     - **1) права** (Rights/Powers)
     - **2) обязанности** (Responsibilities/Obligations)

4. **Функции** (Functions)
   - Detailed operational functions
   - Numbered with `1)`, `2)`, `3)`

5. **Additional Sections**
   - Статус первого руководителя (First leader status)
   - Имущество (Property)
   - Реорганизация (Reorganization)

## Detection Algorithm

The universal parser automatically detects structure type:

```python
if "Глава 1" and "Глава 2" in document:
    → CHAPTER-BASED
elif "1. Общие положения" in document:
    → NUMBERED-SECTIONS
else:
    → CUSTOM (keyword-based)
```

## Key Differences by Type

| Feature | Chapter-Based | Numbered-Sections | Custom |
|---------|---------------|-------------------|--------|
| Chapter markers | ✓ Глава 1, 2, 3... | ✗ Uses numbered headers | ✗ No clear markers |
| Section headers | Bold | **Bold** | Mixed |
| Tasks numbering | `1)`, `2)`, `3)` | `1)`, `2)`, `3)` | `1)`, `2)`, `3)` |
| Functions numbering | `1)`, `2)`, `3)` | `1)`, `2)`, `3)` | `1)`, `2)`, `3)` |
| Rights numbering | `1.`, `2.`, `3.` | **No numbers** (paragraphs) | Variable |
| Responsibilities | `1.`, `2.`, `3.` | **No numbers** (paragraphs) | Variable |

## Usage

### Import any document:

```bash
# Import УАиГ (chapter-based)
python3 scripts/import_from_docx.py "Положение УАиГ.docx"

# Import УВП (numbered-sections)
python3 scripts/import_from_docx.py "Положение УВП 2025.docx"

# Import УГА (custom)
python3 scripts/import_from_docx.py "Положение УГА.docx"
```

The parser automatically:
1. Detects structure type
2. Extracts all sections
3. Formats for API
4. Imports to selected company

## Analysis Scripts

### View all document structures:
```bash
python3 scripts/deep_structure_analysis.py
```

### Compare specific documents:
```bash
python3 scripts/analyze_docx_structure.py
```

### Test universal parser:
```bash
python3 scripts/universal_docx_parser.py
```

## Recommendations

✅ **Best supported:** CHAPTER-BASED and NUMBERED-SECTIONS documents work perfectly

⚠️ **Partial support:** CUSTOM documents may need manual review after import

💡 **Tip:** Always review the parsed data preview before confirming import

## Common Pitfalls

1. **Section detection:** Bold text is used to identify section headers in NUMBERED-SECTIONS
2. **Authorities formatting:** In NUMBERED-SECTIONS, права and обязанности are NOT numbered items
3. **Chapter transitions:** CUSTOM documents may have unexpected section boundaries

## Future Enhancements

- [ ] Improve CUSTOM document parsing
- [ ] Add validation for required sections
- [ ] Support for .doc files (currently only .docx)
- [ ] Automatic quality checks before import
