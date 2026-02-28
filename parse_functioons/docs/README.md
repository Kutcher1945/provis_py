# Planning.gov.kz API Client

Python client for interacting with the planning.gov.kz RGF Module API.

## Project Structure

```
polozhenia/parse_functioons/
├── config.py          # Configuration settings (credentials, URLs)
├── auth.py            # Authentication functions
├── rgf_api.py         # RGF Module API functions
├── main.py            # Main demo script
├── login.py           # Legacy single-file version (deprecated)
└── README.md          # This file
```

## Modules

### config.py
Contains all configuration settings:
- `BASE_URL` - API base URL
- `IIN` - Your identification number
- `PASSWORD` - Your password
- Default parameters for API calls

### auth.py
Authentication functions:
- `login(iin, password)` - Login and get Bearer token
- `check_client_requests(iin, token)` - Check open support requests

### rgf_api.py
RGF Module API functions:
- `get_positions(token, position_id)` - Get position data
- `check_is_mio(token)` - Check MIO status
- `get_gu_list(token, parent_id)` - Get government units list
- `get_position_department(token, record_id)` - Get specific record
- `create_position_department(token, payload)` - Create new record
- `create_test_record(token)` - Create a test record

## Quick Start

### Run the demo script:

```bash
python3 main.py
```

### Use in your own scripts:

```python
from config import IIN, PASSWORD
from auth import login
from rgf_api import get_positions, get_gu_list, create_position_department

# Login
token, _ = login(IIN, PASSWORD)

# Fetch data
positions = get_positions(token)
gu_list = get_gu_list(token, parent_id=85750)

# Create a record
payload = {
    "positionId": 762,
    "generalProvisions": "My custom data",
    "tasks": [{"taskText": "Task 1"}],
    # ... other fields
}
result = create_position_department(token, payload)
```

## API Functions Reference

### Authentication

```python
token, user_data = login(iin, password)
# Returns: (token_string, user_dict) or (None, None) if failed
```

### Read Operations

```python
# Get position data
positions = get_positions(token, position_id=762, lang="ru")

# Check MIO status
mio_status = check_is_mio(token, lang="ru")

# Get GU list
gu_list = get_gu_list(token, parent_id=85750, has_not_ended=True, lang="ru")

# Get specific position-department record
record = get_position_department(token, record_id=6722, lang="ru")
```

### Write Operations

```python
# Create a test record
result = create_test_record(token, position_id=762, lang="ru")

# Create a custom record
payload = {
    "positionId": 762,
    "positionDepartmentId": 762,
    "departmentId": None,
    "committeeId": None,
    "additions": "Your additions text",
    "approvals": [],
    "authoritiesLaw": [{"authorityText": "Authority 1"}],
    "authoritiesResponsibilities": [{"authorityText": "Responsibility 1"}],
    "functions": [],
    "generalProvisions": "General provisions text",
    "guid": "99900000011429",
    "guName": "КГУ \"Name\"",
    "legalEntity": False,
    "staffNumbers": 3,
    "status": "",
    "tasks": [{"taskText": "Task 1"}],
    "type": 4
}
result = create_position_department(token, payload, lang="ru")
```

## Configuration

Edit `config.py` to change credentials and defaults:

```python
IIN = "your_iin_here"
PASSWORD = "your_password_here"
DEFAULT_POSITION_ID = 762
DEFAULT_PARENT_ID = 85750
```

## Error Handling

All functions return `None` on failure. Always check return values:

```python
token, _ = login(IIN, PASSWORD)
if not token:
    print("Login failed!")
    exit(1)

positions = get_positions(token)
if positions is None:
    print("Failed to fetch positions")
```

## Examples

### Basic Usage
See `main.py` for a complete working example showing authentication and basic CRUD operations.

### Advanced Examples
- `example_usage.py` - Shows various use cases:
  - Simple data fetching
  - Creating custom records
  - Bulk record creation

### CSV Import
- `csv_import.py` - Import records from CSV file

Run CSV import:
```bash
# Create and import sample CSV
python3 csv_import.py

# Import from your own CSV file
python3 csv_import.py your_data.csv
```

CSV format:
```csv
name,general_provisions,tasks,authorities,staff_numbers
"Dept 1","Provisions text","Task1;Task2","Auth1;Auth2",5
"Dept 2","Provisions text","Task1","Auth1",3
```
