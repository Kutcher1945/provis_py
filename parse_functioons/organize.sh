#!/bin/bash
# Organize the project folder

echo "Organizing project structure..."

# Create directories
mkdir -p docs
mkdir -p examples
mkdir -p data
mkdir -p scripts
mkdir -p deprecated

# Move documentation
mv README.md DATA_STRUCTURE.md CSV_GUIDE.md docs/ 2>/dev/null

# Move example/demo scripts
mv main.py example_usage.py send_test.py test_post.py compare_records.py examples/ 2>/dev/null

# Move data files
mv "Положение УАиГ.docx" "Прил. 2 УАиГ.xlsx" parsed_output.csv template.csv guids.txt guid_names.txt data/ 2>/dev/null
rm -f "~$ложение УАиГ.docx" 2>/dev/null  # Remove temp Word file

# Move import scripts to scripts/
mv import_from_docx.py import_parsed_data.py csv_import.py find_guid_names.py scripts/ 2>/dev/null

# Move deprecated files
mv login.py parse.py deprecated/ 2>/dev/null

echo "✓ Organization complete!"
echo ""
echo "New structure:"
echo "├── Core modules (root):"
echo "│   ├── config.py"
echo "│   ├── auth.py"
echo "│   └── rgf_api.py"
echo "├── docs/"
echo "│   ├── README.md"
echo "│   ├── DATA_STRUCTURE.md"
echo "│   └── CSV_GUIDE.md"
echo "├── examples/"
echo "│   ├── main.py"
echo "│   ├── example_usage.py"
echo "│   ├── send_test.py"
echo "│   ├── test_post.py"
echo "│   └── compare_records.py"
echo "├── scripts/"
echo "│   ├── import_from_docx.py"
echo "│   ├── import_parsed_data.py"
echo "│   ├── csv_import.py"
echo "│   └── find_guid_names.py"
echo "├── data/"
echo "│   ├── Положение УАиГ.docx"
echo "│   ├── parsed_output.csv"
echo "│   ├── template.csv"
echo "│   ├── guids.txt"
echo "│   └── guid_names.txt"
echo "└── deprecated/"
echo "    ├── login.py"
echo "    └── parse.py"
