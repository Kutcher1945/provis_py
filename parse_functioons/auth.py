"""
Authentication module for planning.gov.kz API
"""

import requests
import urllib3
from config import BASE_URL, COMMON_HEADERS

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def login(iin, password):
    """
    Login to the API and return the Bearer token

    Args:
        iin (str): User's IIN (identification number)
        password (str): User's password

    Returns:
        tuple: (token, user_data) if successful, (None, None) if failed
    """
    url = f"{BASE_URL}/sso/api/account/login"

    payload = {
        "username": iin,  # API expects "username" not "iin"
        "password": password
    }

    headers = {
        **COMMON_HEADERS,
        "Content-Type": "application/json",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    }

    response = requests.post(url, json=payload, headers=headers, verify=False)

    print(f"Login Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        user = data.get('user', {})
        print(f"✓ Login successful!")
        print(f"User: {user.get('fullName')} (IIN: {user.get('iin')})")
        print(f"Email: {user.get('email')}")
        print(f"Token: {token[:50]}..." if token else "Token not found in response")
        return token, data
    else:
        try:
            error_data = response.json()
            print(f"✗ Login failed: {error_data.get('errorMsg', 'Unknown error')}")
            print(f"Full response: {error_data}")
        except:
            print(f"✗ Login failed: {response.text}")
        return None, None


def check_client_requests(iin, token):
    """
    Check client open requests using the Bearer token

    Args:
        iin (str): User's IIN
        token (str): Bearer token from login

    Returns:
        dict: API response
    """
    url = f"{BASE_URL}/gateway/system-info/api/support/checkClientOpenRequest/{iin}"

    headers = {
        **COMMON_HEADERS,
        "Authorization": f"Bearer {token}",
        "Referer": f"{BASE_URL}/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    }

    response = requests.get(url, headers=headers, verify=False)

    print(f"\nAPI Request Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()
