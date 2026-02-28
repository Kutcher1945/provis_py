# Parser Fixes Summary

## Problem
Many imported documents were missing **права** (rights) and **обязанности** (responsibilities) data because the parser only collected numbered items like `1.`, `2.`, `3.`, but many documents use unnumbered paragraphs.

## What Was Fixed

### 1. Parser Improvements (universal_docx_parser.py)

#### CHAPTER-BASED Documents
- **Before**: Only collected numbered items (`1.`, `2.`, `3.`)
- **After**: Collects ALL paragraphs under права/обязанности sections
- **Fixed files**: УМП, УМПТиГР, УРОП, УТ, УЭиВ, УЭиОС, УДР

#### NUMBERED-SECTIONS Documents
- **Before**: Required bold headers, only numbered items, section detection too broad
- **After**:
  - Removed bold requirement for section headers
  - Collects all paragraphs (numbered and unnumbered)
  - Fixed section 3+ detection to avoid false positives
  - Added support for unnumbered subsections ("Задачи:" instead of "14. Задачи:")
  - Added support for combined "Права и обязанности" sections
- **Fixed files**: УВП 2026, УГК, Аппарат акима

#### CUSTOM Documents
- **Before**: Only collected numbered items
- **After**: Collects all paragraphs under права/обязанности
- **Fixed files**: УКИЖИ, УСтроительства

#### Edge Cases
- **Права on same line as Полномочия**: Fixed for cases where "права:" appears on the same line as "Полномочия:"
- **Length filtering**: Added to skip formatting artifacts (lines < 10 chars)

## Results

### ✅ Successfully Fixed: 12 files (63%)
- Положение УВП 2026.docx (6 права, 7 обязанности)
- Положение УДР.docx (10 права, 19 обязанности)
- Положение УГК.docx (14 права, 22 обязанности)
- Положение УКИЖИ.docx (9 права, 7 обязанности)
- Положение УМП.docx (10 права, 6 обязанности)
- Положение УМПТиГР.docx (13 права, 6 обязанности)
- Положение УРОП.docx (10 права, 3 обязанности)
- Положение УСтроительства.docx (7 права, 5 обязанности)
- Положение УТ.docx (9 права, 21 обязанности)
- Положение о «Аппарат акима города Алматы».docx (14 права, 6 обязанности)
- Положение УЭиОС.docx (11 права, 5 обязанности)
- Положение УЭиВ.docx (12 права, 6 обязанности)

### ⚠️ Partially Fixed: 1 file (5%)
- Положение УК.docx (7 права, 0 обязанности) - has права but missing обязанности

### ✗ Still Need Work: 6 files (32%)
- Положение УГА.docx (0, 0) - CUSTOM structure
- Положение УЗО.docx (0, 0) - Uses combined "Права и обязанности" section
- Положение УО.docx (0, 0) - NUMBERED-SECTIONS
- Положение УОДДиПТ.docx (0, 0) - CHAPTER-BASED
- Положение УОЗ.docx (0, 0) - CHAPTER-BASED
- Положение УРДИ.docx (0, 0) - CHAPTER-BASED

## New Tools Created

### 1. verify_records.py
**Purpose**: Check what data is in imported records

**Usage**:
```bash
# Check specific records
python3 scripts/verify_records.py 6822 6823 6824

# Check all from import report
python3 scripts/verify_records.py --from-report data/import_report_20260228_183026.txt
```

**Output**: Table showing права, обязанности, задачи, функции counts for each record

### 2. cleanup_bad_imports.py
**Purpose**: Delete bad records from the API

**Usage**:
```bash
# Delete specific records (verifies before deleting)
python3 scripts/cleanup_bad_imports.py 6822 6823 6824

# Delete all from import report
python3 scripts/cleanup_bad_imports.py --from-report data/import_report_20260228_183026.txt
```

**Features**:
- Checks each record before deletion
- Shows which records are problematic
- Asks for confirmation before deleting

### 3. reimport_bad_files.py
**Purpose**: Complete workflow to fix bad imports

**Usage**:
```bash
python3 scripts/reimport_bad_files.py
```

**What it does**:
1. Shows list of files that need re-importing
2. Optionally deletes old bad records
3. Re-imports all files with the fixed parser
4. Generates final report showing what was fixed

### 4. New API Functions (rgf_api.py)

Added two new functions:

**get_position_department(token, record_id)**
- GET a specific record by ID
- See what data is in the record

**delete_position_department(token, record_id)**
- DELETE a record by ID
- Clean up bad imports

## Workflow to Fix Bad Imports

### Step 1: Verify which records are bad
```bash
python3 scripts/verify_records.py --from-report data/import_report_20260228_183026.txt
```

This shows which records are missing права/обязанности.

### Step 2: Delete bad records
```bash
python3 scripts/cleanup_bad_imports.py --from-report data/import_report_20260228_183026.txt
```

### Step 3: Re-import with fixed parser

**Option A: Use bulk import**
```bash
python3 scripts/bulk_import.py
# Select the files that were badly imported
# Use Mode 3 (automatic) to auto-detect organizations
```

**Option B: Use re-import script**
```bash
python3 scripts/reimport_bad_files.py
# Handles everything automatically
```

## Remaining Issues

6 files still need parser improvements:

1. **УГА, УК** (CUSTOM) - Complex custom structures need investigation
2. **УЗО, УО** (NUMBERED-SECTIONS) - Use "Права и обязанности" combined section without separate права:/обязанности: markers
3. **УОДДиПТ, УОЗ, УРДИ** (CHAPTER-BASED) - Need investigation to understand their structure

These files can still be imported but права/обязанности data will be incomplete. They will require manual entry or further parser enhancements.

## Documentation Updates

Updated files:
- ✅ README.md - Added cleanup tools section
- ✅ PARSER_FIXES_SUMMARY.md - This file
- ✅ rgf_api.py - Added GET and DELETE functions

## Testing Recommendations

Before re-importing all files:

1. **Test on 1-2 files first**:
   ```bash
   python3 scripts/import_from_docx.py "Положение УМП.docx"
   ```

2. **Verify the data was imported correctly**:
   ```bash
   python3 scripts/verify_records.py [new_record_id]
   ```

3. **If successful, proceed with bulk re-import**

## API Endpoints Used

### GET Record
```
GET https://planning.gov.kz/gateway/rgf-module/position-department/{id}?lang=ru
Authorization: Bearer {token}
```

### DELETE Record
```
DELETE https://planning.gov.kz/gateway/rgf-module/position-department/{id}?lang=ru
Authorization: Bearer {token}
```

## Summary

**Before fixes**: 19 files with missing права/обязанности
**After fixes**: 12 files fully fixed, 1 partial, 6 still need work

**Success rate**: 63% fully fixed, 68% at least partially working

The parser is now much more robust and handles the majority of document structures correctly!
