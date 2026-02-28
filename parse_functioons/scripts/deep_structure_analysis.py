#!/usr/bin/env python3
"""
Deep analysis to find common patterns across all DOCX files
"""

import sys
from docx import Document
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

DATA_DIR = Path(__file__).parent.parent / "data"


def find_key_sections(doc_path):
    """Find key sections in a document"""

    try:
        doc = Document(doc_path)
    except Exception as e:
        return None

    sections = {
        'general_provisions': None,
        'tasks': None,
        'authorities': None,
        'functions': None,
        'structure_type': None
    }

    all_text = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            all_text.append(text)

    full_text = '\n'.join(all_text).lower()

    # Detect structure type
    if 'глава 1' in full_text and 'глава 2' in full_text:
        sections['structure_type'] = 'CHAPTER-BASED (Глава 1, Глава 2...)'
    elif '1. общие положения' in full_text or '1.общие положения' in full_text:
        sections['structure_type'] = 'NUMBERED SECTIONS (1. 2. 3...)'
    else:
        sections['structure_type'] = 'CUSTOM/UNKNOWN'

    # Find key section markers
    for i, text in enumerate(all_text):
        text_lower = text.lower()

        # General Provisions
        if not sections['general_provisions']:
            if ('общие положения' in text_lower or
                'общие положение' in text_lower or
                'глава 1' in text_lower):
                sections['general_provisions'] = {'line': i, 'text': text[:60]}

        # Tasks
        if not sections['tasks']:
            if ('задачи' in text_lower and
                ('.' in text[:5] or 'глава' in text_lower or len(text) < 50)):
                sections['tasks'] = {'line': i, 'text': text[:60]}

        # Authorities/Полномочия
        if not sections['authorities']:
            if ('полномочия' in text_lower and
                ('.' in text[:5] or 'глава' in text_lower or len(text) < 80)):
                sections['authorities'] = {'line': i, 'text': text[:60]}

        # Functions
        if not sections['functions']:
            if ('функции' in text_lower and
                ('.' in text[:5] or 'глава' in text_lower or len(text) < 50)):
                sections['functions'] = {'line': i, 'text': text[:60]}

    return sections


def analyze_all_documents():
    """Analyze all DOCX files in data directory"""

    print(f"\n{'='*90}")
    print("ANALYZING ALL ПОЛОЖЕНИЕ DOCUMENTS")
    print(f"{'='*90}\n")

    docx_files = sorted(DATA_DIR.glob("Положение*.docx"))

    results = []

    for doc_path in docx_files:
        sections = find_key_sections(doc_path)

        if sections:
            results.append({
                'filename': doc_path.name,
                'sections': sections
            })

            print(f"📄 {doc_path.name}")
            print(f"   Type: {sections['structure_type']}")

            if sections['general_provisions']:
                print(f"   ✓ General: Line {sections['general_provisions']['line']:3d} - {sections['general_provisions']['text']}")
            else:
                print(f"   ✗ General: NOT FOUND")

            if sections['tasks']:
                print(f"   ✓ Tasks:   Line {sections['tasks']['line']:3d} - {sections['tasks']['text']}")
            else:
                print(f"   ✗ Tasks:   NOT FOUND")

            if sections['authorities']:
                print(f"   ✓ Author:  Line {sections['authorities']['line']:3d} - {sections['authorities']['text']}")
            else:
                print(f"   ✗ Author:  NOT FOUND")

            if sections['functions']:
                print(f"   ✓ Func:    Line {sections['functions']['line']:3d} - {sections['functions']['text']}")
            else:
                print(f"   ✗ Func:    NOT FOUND")

            print()

    # Summary
    print(f"\n{'='*90}")
    print("STRUCTURE TYPE SUMMARY")
    print(f"{'='*90}\n")

    structure_types = {}
    for r in results:
        stype = r['sections']['structure_type']
        if stype not in structure_types:
            structure_types[stype] = []
        structure_types[stype].append(r['filename'])

    for stype, files in structure_types.items():
        print(f"\n{stype}:")
        for f in files:
            print(f"  - {f}")

    # Recommendations
    print(f"\n\n{'='*90}")
    print("RECOMMENDATIONS FOR PARSING")
    print(f"{'='*90}\n")

    print("""
Based on the analysis, documents fall into different structure types:

1. CHAPTER-BASED (Глава 1, Глава 2, etc.):
   - Use current parsing logic (import_from_docx.py)
   - Detect chapters: "Глава 1", "Глава 2", etc.
   - Sections: "12. Задачи", "13. Полномочия", "14. Функции"

2. NUMBERED SECTIONS (1. 2. 3. etc.):
   - Need new parsing logic
   - Detect bold headers: "1. Общие положения", "2. Задачи и полномочия"
   - Sections might be combined (e.g., "Задачи и полномочия" in one section)

3. CUSTOM/UNKNOWN:
   - May need manual review
   - Might have all sections combined in one place

RECOMMENDED APPROACH:
- Create a flexible parser that can detect document structure type
- Use different extraction strategies based on structure type
- Fall back to keyword-based extraction for unusual formats
    """)


if __name__ == "__main__":
    analyze_all_documents()
