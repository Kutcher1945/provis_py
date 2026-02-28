# POST Data Structure for position-department

## Required Fields

```json
{
  "positionId": 762,                    // Required: Position ID (integer)
  "positionDepartmentId": 762,          // Required: Position-Department ID (integer)
  "departmentId": null,                 // Optional: Department ID or null
  "committeeId": null,                  // Optional: Committee ID or null
  "guid": "99900000011429",             // Required: GUID string
  "guName": "КГУ \"Name\"",             // Required: GU name (string)
  "type": 4,                            // Required: Type (integer)
  "staffNumbers": 3,                    // Required: Staff count (integer)
  "legalEntity": false,                 // Required: Legal entity status (boolean)
  "status": "",                         // Required: Status string (can be empty)
  "departmentGuid": null,               // Optional: Department GUID or null

  // Text Fields
  "generalProvisions": "текст...",      // Required: General provisions (long text)
  "additions": "текст...",              // Optional: Additions (text)

  // Array Fields
  "approvals": [],                      // Required: Array of approval objects (can be empty)
  "functions": [],                      // Required: Array of functions (can be empty)

  "tasks": [                            // Required: Array of task objects
    {"taskText": "Задача 1"},
    {"taskText": "Задача 2"}
  ],

  "authoritiesLaw": [                   // Required: Array of authority law objects
    {"authorityText": "Полномочие 1"},
    {"authorityText": "Полномочие 2"}
  ],

  "authoritiesResponsibilities": [      // Required: Array of responsibility objects
    {"authorityText": "Ответственность 1"},
    {"authorityText": "Ответственность 2"}
  ]
}
```

## Field Types

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| positionId | integer | Yes | Position ID (usually 762) |
| positionDepartmentId | integer | Yes | Position-Department ID |
| departmentId | integer/null | No | Department ID |
| committeeId | integer/null | No | Committee ID |
| guid | string | Yes | Government unit GUID |
| guName | string | Yes | Government unit name |
| type | integer | Yes | Record type (usually 4) |
| staffNumbers | integer | Yes | Number of staff |
| legalEntity | boolean | Yes | Legal entity status |
| status | string | Yes | Status (can be empty) |
| generalProvisions | string | Yes | Main regulations text |
| additions | string | No | Additional information |
| tasks | array | Yes | List of tasks (can be empty) |
| authoritiesLaw | array | Yes | Legal authorities (can be empty) |
| authoritiesResponsibilities | array | Yes | Responsibilities (can be empty) |
| approvals | array | Yes | Approvals (can be empty) |
| functions | array | Yes | Functions (can be empty) |

## Minimal Valid Example

```json
{
  "positionId": 762,
  "positionDepartmentId": 762,
  "departmentId": null,
  "committeeId": null,
  "guid": "99900000011429",
  "guName": "КГУ \"Тестовое подразделение\"",
  "type": 4,
  "staffNumbers": 3,
  "legalEntity": false,
  "status": "",
  "departmentGuid": null,
  "generalProvisions": "Основные положения",
  "additions": "",
  "approvals": [],
  "functions": [],
  "tasks": [],
  "authoritiesLaw": [],
  "authoritiesResponsibilities": []
}
```
