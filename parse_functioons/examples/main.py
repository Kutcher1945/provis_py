#!/usr/bin/env python3
"""
Main script to demonstrate API usage for planning.gov.kz

This script shows how to:
1. Login and authenticate
2. Fetch positions, GU lists, and MIO status
3. Create new position-department records
"""

from config import IIN, PASSWORD
from auth import login, check_client_requests
from rgf_api import (
    get_positions,
    check_is_mio,
    get_gu_list,
    create_test_record,
    get_position_department
)


def main():
    """Main execution function"""
    # Step 1: Login
    print("="*60)
    print("STEP 1: Authentication")
    print("="*60)
    token, login_data = login(IIN, PASSWORD)

    if not token:
        print("\n✗ Login failed. Exiting.")
        return

    # Step 2: Make API requests
    print("\n" + "="*60)
    print("STEP 2: Fetching Data")
    print("="*60)

    # Check client requests
    check_client_requests(IIN, token)

    # Get positions
    positions = get_positions(token)
    if positions:
        print(f"\n✓ Positions data fetched (ID: {positions.get('id')})")
        print(f"  Status: {positions.get('status')}")
        print(f"  General Provisions: {positions.get('generalProvisions', '')[:100]}...")

    # Check if MIO
    is_mio = check_is_mio(token)
    if is_mio is not None:
        print(f"\n✓ MIO Status: {is_mio}")

    # Get GU list
    gu_list = get_gu_list(token)
    if gu_list:
        print(f"\n✓ GU List fetched ({len(gu_list)} items)")
        print(f"  First 3 items:")
        for i, gu in enumerate(gu_list[:3], 1):
            print(f"    {i}. {gu.get('nameRu', 'N/A')}")

    # Step 3: Create a test record
    print("\n" + "="*60)
    print("STEP 3: Creating Test Record")
    print("="*60)

    post_result = create_test_record(token)

    if post_result and post_result.get('success'):
        created_id = post_result.get('data')
        print(f"\n✓ Test record created successfully!")
        print(f"  You can now fetch it with get_position_department(token, {created_id})")

    print("\n" + "="*60)
    print("Done!")
    print("="*60)


if __name__ == "__main__":
    main()
