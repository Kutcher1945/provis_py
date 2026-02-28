import requests
import urllib3

# Suppress SSL warnings (since we're disabling verification below)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# Configuration
# ============================================================
BASE_URL = "https://planning.gov.kz"
IIN = "990814300025"  # Change to your actual IIN
PASSWORD = "Alm@ty#365!"  # Change to your actual password

# ============================================================
# Step 1: Login and get Bearer token
# ============================================================
def login(iin, password):
    """Login and return the Bearer token"""
    url = f"{BASE_URL}/sso/api/account/login"

    payload = {
        "username": iin,  # API expects "username" not "iin"
        "password": password
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
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
        error_data = response.json()
        print(f"✗ Login failed: {error_data.get('errorMsg', 'Unknown error')}")
        print(f"Full response: {error_data}")
        return None, None


# ============================================================
# Step 2: Make authenticated API request
# ============================================================
def check_client_requests(iin, token):
    """Check client open requests using the Bearer token"""
    url = f"{BASE_URL}/gateway/system-info/api/support/checkClientOpenRequest/{iin}"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru",
        "Authorization": f"Bearer {token}",
        "Referer": f"{BASE_URL}/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    }

    response = requests.get(url, headers=headers, verify=False)

    print(f"\nAPI Request Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()


# ============================================================
# Step 3: RGF Module API functions
# ============================================================
def get_positions(token, position_id=762, lang="ru"):
    """Get positions data"""
    url = f"{BASE_URL}/gateway/rgf-module/positions/{position_id}?lang={lang}"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}",
        "selectedlevel": "RGF_GU",
        "Referer": f"{BASE_URL}/rgffront"
    }

    response = requests.get(url, headers=headers, verify=False)
    print(f"\nGet Positions Status: {response.status_code}")
    if response.status_code == 200:
        return response.json()
    return None


def check_is_mio(token, lang="ru"):
    """Check if position-department is MIO"""
    url = f"{BASE_URL}/gateway/rgf-module/position-department/isMio?lang={lang}"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}",
        "selectedlevel": "RGF_GU",
        "Referer": f"{BASE_URL}/rgffront"
    }

    response = requests.get(url, headers=headers, verify=False)
    print(f"Check isMio Status: {response.status_code}")
    if response.status_code == 200:
        return response.json()
    return None


def get_gu_list(token, parent_id=85750, has_not_ended=True, lang="ru"):
    """Get GU (government units) list"""
    url = f"{BASE_URL}/gateway/rgf-module/gu/get?parentId={parent_id}&hasNotEnded={has_not_ended}&lang={lang}"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}",
        "selectedlevel": "RGF_GU",
        "Referer": f"{BASE_URL}/rgffront"
    }

    response = requests.get(url, headers=headers, verify=False)
    print(f"Get GU List Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Found {len(data) if isinstance(data, list) else 0} GU items")
        return data
    return None


def post_test_record(token, position_id=762, lang="ru"):
    """POST a test position-department record to the API"""
    url = f"{BASE_URL}/gateway/rgf-module/position-department?lang={lang}"

    # Test payload based on actual API structure
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
        "guid": "99900000011429",
        "guName": "КГУ \"Аппарат акима г. Алматы\"",
        "legalEntity": False,
        "staffNumbers": 3,
        "status": "",
        "tasks": [
            {"taskText": "TEST - Task from API"}
        ],
        "type": 4
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "selectedlevel": "RGF_GU",
        "Referer": f"{BASE_URL}/rgffront",
        "Origin": BASE_URL
    }

    response = requests.post(url, json=payload, headers=headers, verify=False)
    print(f"\nPOST Test Record Status: {response.status_code}")

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


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    # Login
    token, login_data = login(IIN, PASSWORD)

    # If login successful, make API requests
    if token:
        print("\n" + "="*50)
        print("Making RGF Module API Requests...")
        print("="*50)

        # Check client requests
        check_client_requests(IIN, token)

        # Get positions
        positions = get_positions(token)
        if positions:
            print(f"Positions data: {positions}")

        # Check if MIO
        is_mio = check_is_mio(token)
        if is_mio is not None:
            print(f"Is MIO: {is_mio}")

        # Get GU list
        gu_list = get_gu_list(token)
        if gu_list:
            print(f"GU List (first 3): {gu_list[:3] if isinstance(gu_list, list) else gu_list}")

        # Try to POST a test record
        print("\n" + "="*50)
        print("Testing POST request...")
        print("="*50)
        post_result = post_test_record(token)
        if post_result:
            print(f"POST successful!")
        else:
            print(f"POST failed or returned no data")
