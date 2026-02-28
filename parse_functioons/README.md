# Planning.gov.kz API Client

Python client for interacting with the planning.gov.kz RGF Module API.

## 🌍 Documentation

- **[⚡ Быстрый старт](БЫСТРЫЙ_СТАРТ.md)** - Quick start guide in Russian (START HERE!)
- **[📘 Русская документация](docs/РУКОВОДСТВО_ПОЛЬЗОВАТЕЛЯ.md)** - Полное руководство на русском языке
- **[📗 English Documentation](docs/README.md)** - Complete guide in English

## 📁 Project Structure

```
polozhenia/parse_functioons/
├── config.py              # Configuration (credentials, URLs)
├── auth.py                # Authentication functions
├── rgf_api.py             # RGF Module API functions
├── organize.sh            # Organization script
│
├── docs/                  # Documentation
│   ├── README.md          # Detailed API documentation
│   ├── DATA_STRUCTURE.md  # Data structure reference
│   └── CSV_GUIDE.md       # CSV import guide
│
├── examples/              # Example scripts
│   ├── main.py            # Main demo (auth + CRUD)
│   ├── example_usage.py   # Various use cases
│   ├── send_test.py       # Send simple test record
│   ├── test_post.py       # Detailed POST test
│   └── compare_records.py # Compare manual vs API records
│
├── scripts/               # Import/utility scripts
│   ├── import_from_docx.py         # 🌟 Universal DOCX import (single file)
│   ├── bulk_import.py              # 🚀 Bulk import (multiple files at once)
│   ├── universal_docx_parser.py    # Universal document parser
│   ├── verify_records.py           # ✓ Verify imported records
│   ├── cleanup_bad_imports.py      # 🗑️ Delete bad records
│   ├── reimport_bad_files.py       # 🔄 Re-import with fixed parser
│   ├── list_all_gus.py             # List all government units
│   ├── analyze_docx_structure.py   # Analyze document structure
│   ├── deep_structure_analysis.py  # Deep structure analysis
│   ├── import_parsed_data.py       # Import from CSV
│   ├── csv_import.py               # Generic CSV import
│   └── find_guid_names.py          # Find names for GUIDs
│
├── data/                  # Data files
│   ├── Положение УАиГ.docx    # Source Word document
│   ├── parsed_output.csv      # Parsed CSV
│   ├── template.csv           # CSV template
│   ├── guids.txt              # List of GUIDs
│   └── guid_names.txt         # GUID → Name mapping
│
└── deprecated/            # Old/deprecated files
    ├── login.py           # Old single-file version
    └── parse.py           # Old parser
```

## 🚀 Quick Start

### 1. Configure credentials
Edit `config.py`:
```python
IIN = "your_iin_here"
PASSWORD = "your_password_here"
```

### 2. Run examples

**Import single document (auto-detects structure):**
```bash
python3 scripts/import_from_docx.py "Положение УВП 2025.docx"
```

**🚀 Bulk import multiple documents:**
```bash
python3 scripts/bulk_import.py
# Import 2, 10, or all 25+ documents at once!
```

**List all government units:**
```bash
python3 scripts/list_all_gus.py
```

**Analyze document structures:**
```bash
python3 scripts/deep_structure_analysis.py
```

**Basic demo:**
```bash
python3 examples/main.py
```

**Send test record:**
```bash
python3 examples/send_test.py
```

## 📖 Documentation

- **[📘 User Guide (Russian)](docs/РУКОВОДСТВО_ПОЛЬЗОВАТЕЛЯ.md)** - Полное руководство на русском
- **[API Documentation](docs/README.md)** - Complete API reference
- **[Data Structure](docs/DATA_STRUCTURE.md)** - JSON structure for POST
- **[Document Structures](docs/DOCUMENT_STRUCTURES.md)** - Analysis of document types
- **[CSV Guide](docs/CSV_GUIDE.md)** - CSV format and import guide

## 🔑 Key Features

✅ **Universal Document Parser** - Automatically handles 3 document structure types
✅ **Smart Structure Detection** - Auto-detects CHAPTER-BASED, NUMBERED-SECTIONS, or CUSTOM formats
✅ **🚀 Bulk Import** - Import multiple documents at once (2, 10, or all 25+ files)
✅ **🤖 Intelligent Organization Detection** - Extracts organization name directly from document header for accurate auto-matching
✅ **Interactive Company Selection** - Choose from 36+ government units before import
✅ **Three Import Modes** - Single file, bulk with selection, or fully automatic
✅ **Authentication** - Login and token management
✅ **Read Operations** - Fetch positions, GU lists, MIO status
✅ **Write Operations** - Create position-department records
✅ **Import Reports** - Detailed reports saved for each bulk import
✅ **GUID Lookup** - Find names for government unit IDs

## 📝 Common Tasks

### Import single Word document (auto-detects structure):
```bash
# Import default document (УАиГ)
python3 scripts/import_from_docx.py

# Import specific document
python3 scripts/import_from_docx.py "Положение УВП 2025.docx"

# The script will:
# 1. Login automatically
# 2. Show list of all government units
# 3. Let you select which organization to import to
# 4. Auto-detect document structure (CHAPTER-BASED, NUMBERED-SECTIONS, or CUSTOM)
# 5. Parse and import all sections
```

### 🚀 Bulk import multiple documents:
```bash
python3 scripts/bulk_import.py

# Choose files by:
# - Numbers: 1,3,5
# - Range: 1-10
# - All: all
# - Search: архитектур

# Three modes:
# 1. One organization for all files
# 2. Different organization for each file (with auto-suggestions)
# 3. 🤖 Fully automatic - reads organization name from each document

# Mode 3 (Automatic):
# - Reads document header
# - Extracts full organization name (e.g., "Управление земельных отношений города Алматы")
# - Matches against the list of 36 government units
# - No manual input needed!

# Features:
# - Real-time progress tracking
# - Detailed final report
# - Report saved to data/import_report_*.txt
```

### List all government units:
```bash
python3 scripts/list_all_gus.py
```

### Analyze document structure:
```bash
python3 scripts/deep_structure_analysis.py
```

### Import data from CSV:
```bash
python3 scripts/csv_import.py data/your_file.csv
```

### 🔍 Verify imported records:
```bash
# Check specific records
python3 scripts/verify_records.py 6822 6823 6824

# Check all records from import report
python3 scripts/verify_records.py --from-report data/import_report_20260228_183026.txt
```

### 🗑️ Delete bad records:
```bash
# Delete specific records (with verification before deletion)
python3 scripts/cleanup_bad_imports.py 6822 6823 6824

# Delete all records from import report
python3 scripts/cleanup_bad_imports.py --from-report data/import_report_20260228_183026.txt
```

### 🔄 Re-import bad files:
```bash
# Complete workflow: delete old records and re-import with fixed parser
python3 scripts/reimport_bad_files.py
```

### Use in your own script:
```python
from config import IIN, PASSWORD
from auth import login
from rgf_api import get_positions, create_position_department

# Login
token, _ = login(IIN, PASSWORD)

# Fetch data
positions = get_positions(token)

# Create record
payload = {
    "positionId": 762,
    "guId": 9,
    "guName": "КГУ \"Управление архитектуры...\"",
    "generalProvisions": "Text...",
    # ... see docs/DATA_STRUCTURE.md for all fields
}
result = create_position_department(token, payload)
```

## 🛠️ Core Modules

- **config.py** - Configuration settings
- **auth.py** - Login and authentication
- **rgf_api.py** - API functions (GET/POST)

## 📁 Data Files

All data files are in the `data/` directory:
- Word documents (`.docx`)
- CSV files (`.csv`)
- GUID lists (`.txt`)

## 🗂️ Organization

Files are organized by purpose:
- **Root** - Core modules
- **docs/** - Documentation
- **examples/** - Demo scripts
- **scripts/** - Import utilities
- **data/** - Source data
- **deprecated/** - Old files (not recommended)

## 💡 Tips

1. **Read the Russian guide first:** [docs/РУКОВОДСТВО_ПОЛЬЗОВАТЕЛЯ.md](docs/РУКОВОДСТВО_ПОЛЬЗОВАТЕЛЯ.md) - Comprehensive guide in Russian
2. **Use the universal importer:** `scripts/import_from_docx.py` auto-detects all document types
3. **Check document structure:** Run `scripts/deep_structure_analysis.py` to see all 25+ documents
4. **Search for companies:** When selecting a company, use search (e.g., "архитектур") instead of scrolling
5. **Review before import:** Always check the preview of extracted data before confirming
6. All scripts can be run from the project root

## 📊 Supported Documents

The universal parser supports **25+ documents** in 3 structure types:

- **11 documents:** CHAPTER-BASED (Глава 1, Глава 2...)
- **8 documents:** NUMBERED-SECTIONS (1. Общие положения, 2. Задачи...)
- **4 documents:** CUSTOM (requires review)

See [docs/DOCUMENT_STRUCTURES.md](docs/DOCUMENT_STRUCTURES.md) for full analysis.

---

**For detailed documentation:**
- 🇷🇺 [Русское руководство](docs/РУКОВОДСТВО_ПОЛЬЗОВАТЕЛЯ.md) - Complete guide in Russian
- 🇬🇧 [API Documentation](docs/README.md) - Technical API reference
