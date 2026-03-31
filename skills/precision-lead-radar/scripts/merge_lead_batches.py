#!/usr/bin/env python3
"""
Merge Lead Batches Script
Combines multiple CSV lead batches into a single master file
"""

import csv
import sys
from pathlib import Path
from typing import List, Set

def merge_csv_files(input_files: List[str], output_file: str, remove_duplicates: bool = True) -> dict:
    """
    Merge multiple CSV files into one master file
    
    Args:
        input_files: List of input CSV file paths
        output_file: Output master CSV file path
        remove_duplicates: Whether to remove duplicate rows based on business name
        
    Returns:
        Dictionary with merge statistics
    """
    
    if not input_files:
        print("Error: No input files provided")
        sys.exit(1)
    
    # Read header from first file
    with open(input_files[0], 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
    
    # Track statistics
    stats = {
        "total_rows": 0,
        "unique_rows": 0,
        "duplicates_removed": 0,
        "errors": 0,
        "files_processed": 0
    }
    
    # Store all rows
    all_rows = []
    seen_businesses: Set[str] = set()
    
    # Process each input file
    for file_path in input_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    stats["total_rows"] += 1
                    
                    # Skip rows with errors
                    if row.get('Error'):
                        stats["errors"] += 1
                        continue
                    
                    # Check for duplicates based on business name
                    business_name = row.get('Business Name', '').strip().lower()
                    
                    if remove_duplicates and business_name in seen_businesses:
                        stats["duplicates_removed"] += 1
                        continue
                    
                    if business_name:
                        seen_businesses.add(business_name)
                    
                    all_rows.append(row)
                    stats["unique_rows"] += 1
            
            stats["files_processed"] += 1
            print(f"✓ Processed: {file_path}")
            
        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            continue
    
    # Write merged output
    if all_rows:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            writer.writerows(all_rows)
        
        print(f"\n✓ Merged file created: {output_file}")
    else:
        print("\n✗ No valid rows to write")
        sys.exit(1)
    
    return stats


def main():
    if len(sys.argv) < 3:
        print("Usage: python merge_lead_batches.py <output_file> <input_file1> <input_file2> ...")
        print("Example: python merge_lead_batches.py master.csv batch1.csv batch2.csv batch3.csv")
        sys.exit(1)
    
    output_file = sys.argv[1]
    input_files = sys.argv[2:]
    
    print("=" * 80)
    print("MERGING LEAD BATCHES")
    print("=" * 80)
    print(f"Output file: {output_file}")
    print(f"Input files: {len(input_files)}")
    print()
    
    stats = merge_csv_files(input_files, output_file)
    
    print("\n" + "=" * 80)
    print("MERGE STATISTICS")
    print("=" * 80)
    print(f"Files processed: {stats['files_processed']}")
    print(f"Total rows read: {stats['total_rows']}")
    print(f"Unique rows written: {stats['unique_rows']}")
    print(f"Duplicates removed: {stats['duplicates_removed']}")
    print(f"Errors skipped: {stats['errors']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
