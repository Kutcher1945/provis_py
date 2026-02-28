#!/usr/bin/env python3
"""
Analyze structure of multiple DOCX files to identify common patterns
"""

import sys
from docx import Document
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

DATA_DIR = Path(__file__).parent.parent / "data"


def analyze_document(docx_path):
    """Analyze a single DOCX file and extract its structure"""

    print(f"\n{'='*80}")
    print(f"ANALYZING: {docx_path.name}")
    print(f"{'='*80}")

    try:
        doc = Document(docx_path)
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return None

    structure = {
        'chapters': [],
        'numbered_sections': [],
        'bold_headers': [],
        'all_paragraphs': []
    }

    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text:
            continue

        structure['all_paragraphs'].append(text)

        # Detect chapters (Глава)
        if 'Глава' in text or 'ГЛАВА' in text:
            structure['chapters'].append({
                'line': i,
                'text': text
            })

        # Detect numbered sections (like "12. Задачи", "13. Полномочия")
        if text and len(text) > 2 and text[0].isdigit() and '.' in text[:5]:
            # Check if it's a section header (short text after number)
            parts = text.split('.', 1)
            if len(parts) == 2 and len(parts[1].strip()) < 100:
                structure['numbered_sections'].append({
                    'line': i,
                    'number': parts[0],
                    'text': text
                })

        # Detect bold paragraphs (potential headers)
        if any(run.bold for run in para.runs if run.bold):
            structure['bold_headers'].append({
                'line': i,
                'text': text
            })

    # Print structure summary
    print(f"\nTotal paragraphs: {len(structure['all_paragraphs'])}")

    print(f"\n📖 CHAPTERS ({len(structure['chapters'])}):")
    for ch in structure['chapters']:
        print(f"  Line {ch['line']:4d}: {ch['text'][:80]}")

    print(f"\n🔢 NUMBERED SECTIONS ({len(structure['numbered_sections'])}):")
    for sec in structure['numbered_sections']:
        print(f"  Line {sec['line']:4d}: {sec['text'][:80]}")

    print(f"\n📝 BOLD HEADERS ({len(structure['bold_headers'])}):")
    for i, header in enumerate(structure['bold_headers'][:10]):  # First 10 only
        print(f"  Line {header['line']:4d}: {header['text'][:80]}")
    if len(structure['bold_headers']) > 10:
        print(f"  ... and {len(structure['bold_headers']) - 10} more")

    # Show first 20 paragraphs for context
    print(f"\n📄 FIRST 20 PARAGRAPHS:")
    for i, text in enumerate(structure['all_paragraphs'][:20]):
        print(f"  {i+1:3d}: {text[:100]}")

    return structure


def compare_structures(structures):
    """Compare multiple document structures to find common patterns"""

    print(f"\n\n{'='*80}")
    print("COMPARISON SUMMARY")
    print(f"{'='*80}")

    for filename, struct in structures.items():
        if struct:
            print(f"\n{filename}:")
            print(f"  - Chapters: {len(struct['chapters'])}")
            print(f"  - Numbered sections: {len(struct['numbered_sections'])}")
            print(f"  - Bold headers: {len(struct['bold_headers'])}")
            print(f"  - Total paragraphs: {len(struct['all_paragraphs'])}")


if __name__ == "__main__":
    # Analyze a few representative documents
    documents_to_analyze = [
        "Положение УАиГ.docx",
        "Положение Аппарата акима города Алматы.doc",
        "Положение УВП 2025.docx",
        "Положение УГА.docx",
        "Положение УКИЖИ.docx"
    ]

    structures = {}

    for doc_name in documents_to_analyze:
        doc_path = DATA_DIR / doc_name
        if doc_path.exists():
            structures[doc_name] = analyze_document(doc_path)
        else:
            print(f"\n✗ File not found: {doc_name}")

    # Compare
    compare_structures(structures)

    print(f"\n{'='*80}")
    print("COMMON PATTERNS TO LOOK FOR:")
    print(f"{'='*80}")
    print("""
    1. Chapter markers: "Глава 1", "Глава 2", etc.
    2. Numbered sections: "12. Задачи", "13. Полномочия", "14. Функции"
    3. Sub-sections under Полномочия: "1) права:", "2) обязанности:"
    4. Numbered items: "1)", "2)", "3)" for tasks/functions
    5. Numbered items: "1.", "2.", "3." for authorities (права/обязанности)
    """)
