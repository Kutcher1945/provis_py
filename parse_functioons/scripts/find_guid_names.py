#!/usr/bin/env python3
"""
Find names for GUIDs from guids.txt file
"""

from config import IIN, PASSWORD
from auth import login
from rgf_api import get_gu_list


def find_guid_names():
    """Find names for all GUIDs in guids.txt"""

    # Read GUIDs from file
    print("Reading guids.txt...")
    with open('guids.txt', 'r') as f:
        guids = [int(line.strip()) for line in f if line.strip()]

    print(f"Found {len(guids)} GUIDs to lookup\n")

    # Login
    print("Logging in...")
    token, _ = login(IIN, PASSWORD)

    if not token:
        print("✗ Login failed")
        return

    # Get GU list
    print("\nFetching GU list...")
    gu_list = get_gu_list(token, parent_id=85750)

    if not gu_list:
        print("✗ Failed to fetch GU list")
        return

    # Create GUID -> Name mapping
    guid_map = {}
    for gu in gu_list:
        gu_id = gu.get('id')
        gu_name = gu.get('nameRu', '')
        if gu_id:
            guid_map[gu_id] = gu_name

    # Match GUIDs
    print("\n" + "="*70)
    print("GUID -> NAME MAPPING")
    print("="*70)

    found_count = 0
    not_found = []

    for guid in guids:
        if guid in guid_map:
            found_count += 1
            print(f"{guid:15d} → {guid_map[guid]}")
        else:
            not_found.append(guid)
            print(f"{guid:15d} → ❌ NOT FOUND")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total GUIDs: {len(guids)}")
    print(f"Found: {found_count}")
    print(f"Not Found: {len(not_found)}")

    if not_found:
        print(f"\nNot found GUIDs: {not_found}")

    # Save results to file
    output_file = 'guid_names.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("GUID → Name Mapping\n")
        f.write("="*70 + "\n\n")
        for guid in guids:
            if guid in guid_map:
                f.write(f"{guid}\t{guid_map[guid]}\n")
            else:
                f.write(f"{guid}\tNOT FOUND\n")

    print(f"\n✓ Results saved to {output_file}")


if __name__ == "__main__":
    find_guid_names()
