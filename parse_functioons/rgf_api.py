"""
RGF Module API functions for planning.gov.kz
"""

import requests
import urllib3
from config import BASE_URL, DEFAULT_LANG, DEFAULT_POSITION_ID, DEFAULT_PARENT_ID, DEFAULT_SELECTED_LEVEL

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _get_rgf_headers(token):
    """Helper function to generate common RGF module headers"""
    return {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}",
        "selectedlevel": DEFAULT_SELECTED_LEVEL,
        "Referer": f"{BASE_URL}/rgffront"
    }


def get_positions(token, position_id=DEFAULT_POSITION_ID, lang=DEFAULT_LANG):
    """
    Get positions data

    Args:
        token (str): Bearer token from login
        position_id (int): Position ID to fetch
        lang (str): Language (ru or kz)

    Returns:
        dict: Position data or None if failed
    """
    url = f"{BASE_URL}/gateway/rgf-module/positions/{position_id}?lang={lang}"
    headers = _get_rgf_headers(token)

    response = requests.get(url, headers=headers, verify=False)
    print(f"\nGet Positions Status: {response.status_code}")

    if response.status_code == 200:
        return response.json()
    return None


def check_is_mio(token, lang=DEFAULT_LANG):
    """
    Check if position-department is MIO

    Args:
        token (str): Bearer token from login
        lang (str): Language (ru or kz)

    Returns:
        dict: MIO status data or None if failed
    """
    url = f"{BASE_URL}/gateway/rgf-module/position-department/isMio?lang={lang}"
    headers = _get_rgf_headers(token)

    response = requests.get(url, headers=headers, verify=False)
    print(f"Check isMio Status: {response.status_code}")

    if response.status_code == 200:
        return response.json()
    return None


def get_gu_list(token, parent_id=DEFAULT_PARENT_ID, has_not_ended=True, lang=DEFAULT_LANG):
    """
    Get GU (government units) list

    Args:
        token (str): Bearer token from login
        parent_id (int): Parent GU ID
        has_not_ended (bool): Filter for active GUs
        lang (str): Language (ru or kz)

    Returns:
        list: List of GU items or None if failed
    """
    url = f"{BASE_URL}/gateway/rgf-module/gu/get?parentId={parent_id}&hasNotEnded={has_not_ended}&lang={lang}"
    headers = _get_rgf_headers(token)

    response = requests.get(url, headers=headers, verify=False)
    print(f"Get GU List Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"  Found {len(data) if isinstance(data, list) else 0} GU items")
        return data
    return None


def get_position_department(token, record_id, lang=DEFAULT_LANG):
    """
    Get a specific position-department record by ID

    Args:
        token (str): Bearer token from login
        record_id (int): Position-department ID
        lang (str): Language (ru or kz)

    Returns:
        dict: Position-department data or None if failed
    """
    url = f"{BASE_URL}/gateway/rgf-module/position-department/{record_id}?lang={lang}"
    headers = _get_rgf_headers(token)

    response = requests.get(url, headers=headers, verify=False)
    print(f"Get Position-Department {record_id} Status: {response.status_code}")

    if response.status_code == 200:
        return response.json()
    return None


def delete_position_department(token, record_id, lang=DEFAULT_LANG):
    """
    Delete a position-department record by ID

    Args:
        token (str): Bearer token from login
        record_id (int): Position-department ID to delete
        lang (str): Language (ru or kz)

    Returns:
        dict: API response or None if failed
    """
    url = f"{BASE_URL}/gateway/rgf-module/position-department/{record_id}?lang={lang}"
    headers = _get_rgf_headers(token)

    response = requests.delete(url, headers=headers, verify=False)
    print(f"DELETE Position-Department {record_id} Status: {response.status_code}")

    if response.status_code == 200:
        try:
            return response.json()
        except:
            return {"success": True, "message": "Record deleted"}
    return None


def create_position_department(token, payload, lang=DEFAULT_LANG):
    """
    Create a new position-department record

    Args:
        token (str): Bearer token from login
        payload (dict): Position-department data
        lang (str): Language (ru or kz)

    Returns:
        dict: API response with created record ID or None if failed
    """
    url = f"{BASE_URL}/gateway/rgf-module/position-department?lang={lang}"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "selectedlevel": DEFAULT_SELECTED_LEVEL,
        "Referer": f"{BASE_URL}/rgffront",
        "Origin": BASE_URL
    }

    response = requests.post(url, json=payload, headers=headers, verify=False)
    print(f"\nPOST Position-Department Status: {response.status_code}")

    try:
        response_data = response.json()
        if response.status_code == 200 and response_data.get('success'):
            record_id = response_data.get('data')
            message = response_data.get('message')
            print(f"✓ {message}")
            print(f"  Created position-department ID: {record_id}")
        else:
            print(f"Response: {response_data}")
        return response_data
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Response Text: {response.text}")
        return None


def create_test_record(token, position_id=DEFAULT_POSITION_ID, lang=DEFAULT_LANG):
    """
    Create a test position-department record

    Args:
        token (str): Bearer token from login
        position_id (int): Position ID
        lang (str): Language (ru or kz)

    Returns:
        dict: API response with created record ID or None if failed
    """
    payload = {
        "positionId": position_id,
        "positionDepartmentId": position_id,
        "departmentId": None,
        "committeeId": None,
        "additions": "TEST API submission",
        "approvals": [],
        "authoritiesLaw": [
            {"authorityText": "TEST - Authority Law"}
        ],
        "authoritiesResponsibilities": [
            {"authorityText": "TEST - Authority Responsibility"}
        ],
        "departmentGuid": None,
        "functions": [],
        "generalProvisions": "TEST - General provisions from API",
        "guId": 99900000011429,  # Send as number, not string
        "guName": "КГУ \"ТЕСТ - Аппарат акима г. Алматы\"",
        "legalEntity": False,
        "staffNumbers": 3,
        "status": "",
        "tasks": [
            {"taskText": "TEST - Task from API"}
        ],
        "type": 4
    }

    return create_position_department(token, payload, lang)
