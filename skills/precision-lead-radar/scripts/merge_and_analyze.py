#!/usr/bin/env python3
"""
B2B Lead Intelligence - Master Database Merger & Analyzer
Merges multiple lead batches, deduplicates, analyzes, and generates statistics.
"""

import csv
import json
import os
import re
import sys
from collections import defaultdict

if len(sys.argv) < 3:
    print("Usage: python merge_and_analyze.py <output_file.csv> <batch1.csv> <batch2.csv> ...")
    sys.exit(1)

OUTPUT_FILE = sys.argv[1]
BATCH_FILES = sys.argv[2:]
STATS_FILE = OUTPUT_FILE.replace(".csv", "_stats.json")

# Standard column names
STANDARD_COLUMNS = [
    "Lead #",
    "Business Name",
    "Decision Maker",
    "Phone",
    "Email",
    "Address",
    "Website",
    "LinkedIn",
    "Category",
    "Size",
    "Description",
    "Pain Points",
    "AI Solutions",
    "Use Cases & ROI",
    "Cost of Doing Nothing",
    "Revenue Potential",
    "Source Batch",
    "Revenue Min",
    "Revenue Max"
]

def parse_revenue(revenue_str):
    """Parse revenue potential string into min/max values"""
    if not revenue_str:
        return 5000, 15000
    
    # Find all dollar amounts
    amounts = re.findall(r'\$[\d,]+', revenue_str)
    if len(amounts) >= 2:
        min_val = int(amounts[0].replace('$', '').replace(',', ''))
        max_val = int(amounts[1].replace('$', '').replace(',', ''))
        return min_val, max_val
    elif len(amounts) == 1:
        val = int(amounts[0].replace('$', '').replace(',', ''))
        return val, val * 2
    return 5000, 15000

def normalize_row(row, batch_name):
    """Normalize a row to standard format"""
    # Handle different column name variations
    col_map = {
        'business_name': 'Business Name',
        'decision_maker': 'Decision Maker', 
        'phone': 'Phone',
        'email': 'Email',
        'address': 'Address',
        'website': 'Website',
        'linkedin': 'LinkedIn',
        'category': 'Category',
        'size': 'Size',
        'description': 'Description',
        'pain_points': 'Pain Points',
        'ai_solutions': 'AI Solutions',
        'use_cases_roi': 'Use Cases & ROI',
        'cost_of_doing_nothing': 'Cost of Doing Nothing',
        'revenue_potential': 'Revenue Potential',
    }
    
    normalized = {}
    for key, value in row.items():
        # Try direct match first
        if key in STANDARD_COLUMNS:
            normalized[key] = value
        # Try lowercase mapping
        elif key.lower().replace(' ', '_') in col_map:
            normalized[col_map[key.lower().replace(' ', '_')]] = value
        # Try other variations
        elif key == 'Use Cases & ROI':
            normalized['Use Cases & ROI'] = value
        elif key == 'Cost of Doing Nothing':
            normalized['Cost of Doing Nothing'] = value
        elif key == 'Revenue Potential':
            normalized['Revenue Potential'] = value
    
    normalized['Source Batch'] = batch_name
    
    # Parse revenue
    rev_str = normalized.get('Revenue Potential', '')
    rev_min, rev_max = parse_revenue(rev_str)
    normalized['Revenue Min'] = rev_min
    normalized['Revenue Max'] = rev_max
    
    return normalized

def is_valid_lead(row):
    """Check if a lead has minimum required data"""
    business_name = row.get('Business Name', '').strip()
    if not business_name or business_name in ['N/A', 'Not found', 'Unknown', '']:
        return False
    if len(business_name) < 3:
        return False
    return True

def deduplicate_leads(leads):
    """Remove duplicate leads based on business name similarity"""
    seen_names = set()
    unique_leads = []
    
    for lead in leads:
        name = lead.get('Business Name', '').lower().strip()
        # Normalize name for comparison
        name_key = re.sub(r'[^a-z0-9]', '', name)
        
        if name_key and name_key not in seen_names:
            seen_names.add(name_key)
            unique_leads.append(lead)
    
    return unique_leads

def main():
    all_leads = []
    batch_counts = {}
    
    print("=" * 60)
    print("B2B LEAD INTELLIGENCE - MASTER DATABASE MERGER & ANALYZER")
    print("=" * 60)
    
    for batch_file in BATCH_FILES:
        if not os.path.exists(batch_file):
            print(f"  WARNING: {batch_file} not found, skipping...")
            continue
        
        batch_name = os.path.basename(batch_file).replace('.csv', '')
        batch_leads = []
        
        try:
            with open(batch_file, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if is_valid_lead(row):
                        normalized = normalize_row(row, batch_name)
                        batch_leads.append(normalized)
        except Exception as e:
            print(f"  ERROR reading {batch_file}: {e}")
            continue
        
        batch_counts[batch_name] = len(batch_leads)
        all_leads.extend(batch_leads)
        print(f"  ✓ {batch_name}: {len(batch_leads)} leads")
    
    print(f"\nTotal before deduplication: {len(all_leads)}")
    
    # Deduplicate
    unique_leads = deduplicate_leads(all_leads)
    print(f"Total after deduplication: {len(unique_leads)}")
    
    # Sort by revenue potential (highest first)
    unique_leads.sort(key=lambda x: x.get('Revenue Max', 0), reverse=True)
    
    # Add lead numbers
    for i, lead in enumerate(unique_leads, 1):
        lead['Lead #'] = i
    
    # Write master CSV
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=STANDARD_COLUMNS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(unique_leads)
    
    print(f"\n✓ Master database written: {OUTPUT_FILE}")
    print(f"  Total leads: {len(unique_leads)}")
    
    # Generate statistics
    stats = generate_stats(unique_leads, batch_counts)
    
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"✓ Statistics written: {STATS_FILE}")
    
    # Print summary
    print_summary(stats, len(unique_leads))
    
    return unique_leads, stats

def generate_stats(leads, batch_counts):
    """Generate comprehensive statistics"""
    stats = {
        "total_leads": len(leads),
        "batch_counts": batch_counts,
        "by_category": defaultdict(lambda: {"count": 0, "revenue_min": 0, "revenue_max": 0}),
        "by_geography": defaultdict(int),
        "revenue_analysis": {
            "total_min": 0,
            "total_max": 0,
            "average_min": 0,
            "average_max": 0,
            "tiers": {
                "starter_1200_5000": 0,
                "growth_5000_15000": 0,
                "professional_15000_30000": 0,
                "enterprise_30000_50000": 0
            }
        },
        "contact_quality": {
            "with_email": 0,
            "with_phone": 0,
            "with_linkedin": 0,
            "with_decision_maker": 0,
            "with_website": 0
        }
    }
    
    total_min = 0
    total_max = 0
    
    for lead in leads:
        # Category stats
        cat = lead.get('Category', 'Unknown')
        # Normalize category
        cat_key = cat.split(' - ')[0] if ' - ' in cat else cat
        stats["by_category"][cat_key]["count"] += 1
        rev_min = lead.get('Revenue Min', 0)
        rev_max = lead.get('Revenue Max', 0)
        stats["by_category"][cat_key]["revenue_min"] += rev_min
        stats["by_category"][cat_key]["revenue_max"] += rev_max
        
        # Geography (dynamically extracted)
        address = lead.get('Address', '')
        city_found = False
        if ',' in address:
            parts = address.split(',')
            if len(parts) > 1:
                city = parts[-2].strip().split(' ')[0]
                if city:
                    stats["by_geography"][city] += 1
                    city_found = True
        if not city_found:
            stats["by_geography"]["Unknown"] += 1
        
        # Revenue tiers
        total_min += rev_min
        total_max += rev_max
        avg_rev = (rev_min + rev_max) / 2
        if avg_rev <= 5000:
            stats["revenue_analysis"]["tiers"]["starter_1200_5000"] += 1
        elif avg_rev <= 15000:
            stats["revenue_analysis"]["tiers"]["growth_5000_15000"] += 1
        elif avg_rev <= 30000:
            stats["revenue_analysis"]["tiers"]["professional_15000_30000"] += 1
        else:
            stats["revenue_analysis"]["tiers"]["enterprise_30000_50000"] += 1
        
        # Contact quality
        if lead.get('Email', '').strip() and lead.get('Email') not in ['Not publicly available', 'N/A', '']:
            stats["contact_quality"]["with_email"] += 1
        if lead.get('Phone', '').strip() and lead.get('Phone') not in ['N/A', '']:
            stats["contact_quality"]["with_phone"] += 1
        if lead.get('LinkedIn', '').strip() and lead.get('LinkedIn') not in ['Not found', 'N/A', '']:
            stats["contact_quality"]["with_linkedin"] += 1
        if lead.get('Decision Maker', '').strip() and lead.get('Decision Maker') not in ['N/A', '']:
            stats["contact_quality"]["with_decision_maker"] += 1
        if lead.get('Website', '').strip() and lead.get('Website') not in ['N/A', '']:
            stats["contact_quality"]["with_website"] += 1
    
    stats["revenue_analysis"]["total_min"] = total_min
    stats["revenue_analysis"]["total_max"] = total_max
    if leads:
        stats["revenue_analysis"]["average_min"] = total_min // len(leads)
        stats["revenue_analysis"]["average_max"] = total_max // len(leads)
    
    # Convert defaultdicts to regular dicts for JSON serialization
    stats["by_category"] = dict(stats["by_category"])
    stats["by_geography"] = dict(stats["by_geography"])
    
    return stats

def print_summary(stats, total):
    print("\n" + "=" * 60)
    print("LEAD DATABASE SUMMARY")
    print("=" * 60)
    print(f"Total Leads: {total:,}")
    print(f"\nRevenue Pipeline:")
    print(f"  Total Min: ${stats['revenue_analysis']['total_min']:,.0f}")
    print(f"  Total Max: ${stats['revenue_analysis']['total_max']:,.0f}")
    print(f"  Avg per Lead: ${stats['revenue_analysis']['average_min']:,.0f} - ${stats['revenue_analysis']['average_max']:,.0f}")
    
    print(f"\nRevenue Tiers:")
    tiers = stats['revenue_analysis']['tiers']
    print(f"  Starter ($1.2K-$5K):      {tiers['starter_1200_5000']:>4} leads")
    print(f"  Growth ($5K-$15K):        {tiers['growth_5000_15000']:>4} leads")
    print(f"  Professional ($15K-$30K): {tiers['professional_15000_30000']:>4} leads")
    print(f"  Enterprise ($30K-$50K):   {tiers['enterprise_30000_50000']:>4} leads")
    
    print(f"\nContact Quality:")
    cq = stats['contact_quality']
    print(f"  With Decision Maker: {cq['with_decision_maker']:>4} ({cq['with_decision_maker']/total*100:.0f}%)")
    print(f"  With Phone:          {cq['with_phone']:>4} ({cq['with_phone']/total*100:.0f}%)")
    print(f"  With Email:          {cq['with_email']:>4} ({cq['with_email']/total*100:.0f}%)")
    print(f"  With LinkedIn:       {cq['with_linkedin']:>4} ({cq['with_linkedin']/total*100:.0f}%)")
    print(f"  With Website:        {cq['with_website']:>4} ({cq['with_website']/total*100:.0f}%)")
    
    print(f"\nTop Categories:")
    sorted_cats = sorted(stats['by_category'].items(), key=lambda x: x[1]['count'], reverse=True)
    for cat, data in sorted_cats[:15]:
        print(f"  {cat[:35]:<35} {data['count']:>4} leads  ${data['revenue_min']:>8,.0f} - ${data['revenue_max']:>9,.0f}")
    
    print(f"\nTop Geographies:")
    sorted_geo = sorted(stats['by_geography'].items(), key=lambda x: x[1], reverse=True)
    for city, count in sorted_geo[:10]:
        print(f"  {city:<20} {count:>4} leads")

if __name__ == "__main__":
    leads, stats = main()
