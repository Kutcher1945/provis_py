#!/usr/bin/env python3
"""
List all Government Units (GU) with their IDs and names

This helps you find the correct GUID for your document.
"""

from pathlib import Path
import sys

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import IIN, PASSWORD
from auth import login
from rgf_api import get_gu_list


def list_all_gus():
    """List all GU units with their IDs and names"""

    print("="*70)
    print("LISTING ALL GOVERNMENT UNITS (GU)")
    print("="*70)

    # Login
    print("\nLogging in...")
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

    # Display all GUs
    print("\n" + "="*70)
    print(f"Found {len(gu_list)} Government Units")
    print("="*70)
    print(f"{'ID':<20} {'Name'}")
    print("-" * 70)

    for gu in sorted(gu_list, key=lambda x: x.get('id', 0)):
        gu_id = gu.get('id', 'N/A')
        gu_name = gu.get('nameRu', 'N/A')
        print(f"{gu_id:<20} {gu_name}")

    # Search functionality
    print("\n" + "="*70)
    print("SEARCH")
    print("="*70)

    search_term = input("\nEnter search term (or press Enter to skip): ").strip()

    if search_term:
        print(f"\nSearching for '{search_term}'...")
        print("-" * 70)

        matches = []
        for gu in gu_list:
            gu_id = gu.get('id')
            gu_name = gu.get('nameRu', '')
            if search_term.lower() in gu_name.lower():
                matches.append((gu_id, gu_name))
                print(f"{gu_id:<20} {gu_name}")

        if not matches:
            print(f"No matches found for '{search_term}'")
        else:
            print(f"\nFound {len(matches)} match(es)")

    # Save to file
    output_file = Path(__file__).parent.parent / 'data' / 'all_gus.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("ID → Name Mapping\n")
        f.write("="*70 + "\n\n")
        for gu in sorted(gu_list, key=lambda x: x.get('id', 0)):
            gu_id = gu.get('id', 'N/A')
            gu_name = gu.get('nameRu', 'N/A')
            f.write(f"{gu_id}\t{gu_name}\n")

    print(f"\n✓ Full list saved to {output_file}")


if __name__ == "__main__":
    list_all_gus()
