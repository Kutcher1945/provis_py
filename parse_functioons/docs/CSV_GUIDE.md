# CSV Import Guide

## CSV Fields → JSON Mapping

### CSV Column Names (use these exact headers):

```csv
position_id,position_department_id,guid,gu_name,type,staff_numbers,legal_entity,general_provisions,additions,tasks,authorities_law,authorities_responsibilities
```

### Field Mapping:

| CSV Column | JSON Field | Type | Example | Notes |
|------------|------------|------|---------|-------|
| position_id | positionId | integer | 762 | Usually 762 |
| position_department_id | positionDepartmentId | integer | 762 | Usually same as position_id |
| guid | guid | string | 99900000011429 | GUID from GU list |
| gu_name | guName | string | КГУ "Название" | Government unit name |
| type | type | integer | 4 | Usually 4 |
| staff_numbers | staffNumbers | integer | 5 | Number of staff |
| legal_entity | legalEntity | boolean | false | Use: true/false |
| general_provisions | generalProvisions | string | Основные положения... | Main regulations text |
| additions | additions | string | Дополнительная информация | Additional info (optional) |
| tasks | tasks | array | Task1;Task2;Task3 | Semicolon-separated |
| authorities_law | authoritiesLaw | array | Auth1;Auth2 | Semicolon-separated |
| authorities_responsibilities | authoritiesResponsibilities | array | Resp1;Resp2 | Semicolon-separated |

## CSV Format Rules:

1. **Semicolon-separated arrays**: Use `;` to separate multiple items
   ```csv
   "Task 1;Task 2;Task 3"
   ```

2. **Quotes in text**: Use double quotes
   ```csv
   "КГУ ""Управление образования"""
   ```

3. **Multi-line text**: Wrap in quotes
   ```csv
   "1. First paragraph
   2. Second paragraph"
   ```

4. **Boolean values**: Use lowercase
   ```csv
   true,false
   ```

## Complete CSV Example:

```csv
position_id,position_department_id,guid,gu_name,type,staff_numbers,legal_entity,general_provisions,additions,tasks,authorities_law,authorities_responsibilities
762,762,99900000011429,"КГУ ""Управление образования""",4,5,false,"1. Управление образования является государственным органом","Дополнительная информация","Разработка программ;Контроль качества","Утверждать стандарты;Контролировать учреждения","Ответственность за качество;Соблюдение законодательства"
762,762,99900000011429,"КГУ ""Управление культуры""",4,4,false,"1. Управление культуры осуществляет политику в сфере культуры","","Поддержка инициатив;Организация мероприятий","Развивать инфраструктуру;Поддерживать коллективы","Сохранение наследия;Развитие культуры"
```

## How to Use:

### 1. Create your CSV file:
```bash
# Use the template
cp template.csv my_data.csv
# Edit with Excel or text editor
```

### 2. Import the CSV:
```bash
python3 csv_import.py my_data.csv
```

### 3. Or use in your script:
```python
from csv_import import read_csv_data, csv_to_payload
from auth import login
from rgf_api import create_position_department

# Login
token, _ = login(IIN, PASSWORD)

# Read CSV
records = read_csv_data('my_data.csv')

# Create each record
for record in records:
    payload = csv_to_payload(record)
    result = create_position_department(token, payload)
    print(f"Created ID: {result.get('data')}")
```

## Required vs Optional Fields:

### Required (must have values):
- position_id
- position_department_id
- guid
- gu_name
- type
- staff_numbers
- legal_entity
- general_provisions

### Optional (can be empty):
- additions
- tasks
- authorities_law
- authorities_responsibilities

## Tips:

1. **Use UTF-8 encoding** when saving CSV
2. **Test with small dataset first** (1-2 records)
3. **Check GUID values** from `get_gu_list()` function
4. **Keep text concise** - very long texts may cause issues
5. **Validate data** before importing large batches
