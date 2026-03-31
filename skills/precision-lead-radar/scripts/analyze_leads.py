#!/usr/bin/env python3
"""
Lead Database Analysis Script
Generates statistics and insights from collected leads
"""

import csv
import json
from collections import defaultdict
from typing import Dict, List

def analyze_leads(csv_file: str) -> Dict:
    """Analyze lead database and generate statistics"""
    
    stats = {
        "total_leads": 0,
        "by_category": defaultdict(int),
        "by_size": defaultdict(int),
        "revenue_potential": {
            "total_min": 0,
            "total_max": 0,
            "by_category": defaultdict(lambda: {"min": 0, "max": 0, "count": 0})
        },
        "contact_quality": {
            "with_email": 0,
            "with_linkedin": 0,
            "with_decision_maker": 0
        }
    }
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if row.get('Error'):
                continue
                
            stats["total_leads"] += 1
            
            # Category breakdown
            category = row.get('Category', 'Unknown')
            stats["by_category"][category] += 1
            
            # Size breakdown
            size = row.get('Size', 'Unknown')
            stats["by_size"][size] += 1
            
            # Revenue potential
            rev_pot = row.get('Revenue Potential', '')
            if rev_pot and '$' in rev_pot:
                try:
                    # Parse revenue range like "$8,000-15,000"
                    rev_pot = rev_pot.replace('$', '').replace(',', '')
                    if '-' in rev_pot:
                        min_val, max_val = rev_pot.split('-')
                        min_val = int(min_val.strip())
                        max_val = int(max_val.strip())
                        
                        stats["revenue_potential"]["total_min"] += min_val
                        stats["revenue_potential"]["total_max"] += max_val
                        
                        stats["revenue_potential"]["by_category"][category]["min"] += min_val
                        stats["revenue_potential"]["by_category"][category]["max"] += max_val
                        stats["revenue_potential"]["by_category"][category]["count"] += 1
                except:
                    pass
            
            # Contact quality
            if row.get('Email') and row['Email'] != 'Not publicly available':
                stats["contact_quality"]["with_email"] += 1
            
            if row.get('LinkedIn') and row['LinkedIn'] != 'Not found':
                stats["contact_quality"]["with_linkedin"] += 1
            
            if row.get('Decision Maker'):
                stats["contact_quality"]["with_decision_maker"] += 1
    
    return stats

def main():
    stats = analyze_leads('/home/ubuntu/atlanta_leads_master.csv')
    
    print("=" * 80)
    print("ATLANTA LEADS DATABASE - ANALYSIS REPORT")
    print("=" * 80)
    print(f"\nTotal Qualified Leads: {stats['total_leads']}")
    print(f"\nRevenue Potential:")
    print(f"  Minimum Total: ${stats['revenue_potential']['total_min']:,}")
    print(f"  Maximum Total: ${stats['revenue_potential']['total_max']:,}")
    print(f"  Average per Lead: ${stats['revenue_potential']['total_min']//stats['total_leads']:,} - ${stats['revenue_potential']['total_max']//stats['total_leads']:,}")
    
    print(f"\n{'='*80}")
    print("LEADS BY CATEGORY")
    print(f"{'='*80}")
    for category in sorted(stats['by_category'].keys()):
        count = stats['by_category'][category]
        pct = (count / stats['total_leads'] * 100)
        
        cat_rev = stats['revenue_potential']['by_category'].get(category, {})
        if cat_rev.get('count', 0) > 0:
            avg_min = cat_rev['min'] // cat_rev['count']
            avg_max = cat_rev['max'] // cat_rev['count']
            print(f"{category:40s} {count:3d} ({pct:5.1f}%)  Avg: ${avg_min:,}-${avg_max:,}")
        else:
            print(f"{category:40s} {count:3d} ({pct:5.1f}%)")
    
    print(f"\n{'='*80}")
    print("CONTACT DATA QUALITY")
    print(f"{'='*80}")
    print(f"Leads with Decision Maker: {stats['contact_quality']['with_decision_maker']} ({stats['contact_quality']['with_decision_maker']/stats['total_leads']*100:.1f}%)")
    print(f"Leads with Email: {stats['contact_quality']['with_email']} ({stats['contact_quality']['with_email']/stats['total_leads']*100:.1f}%)")
    print(f"Leads with LinkedIn: {stats['contact_quality']['with_linkedin']} ({stats['contact_quality']['with_linkedin']/stats['total_leads']*100:.1f}%)")
    
    print(f"\n{'='*80}")
    print("BUSINESS SIZE DISTRIBUTION")
    print(f"{'='*80}")
    for size in sorted(stats['by_size'].keys()):
        count = stats['by_size'][size]
        pct = (count / stats['total_leads'] * 100)
        print(f"{size:30s} {count:3d} ({pct:5.1f}%)")
    
    # Save detailed stats
    with open('/home/ubuntu/lead_stats.json', 'w') as f:
        # Convert defaultdict to regular dict for JSON serialization
        stats_json = {
            "total_leads": stats["total_leads"],
            "by_category": dict(stats["by_category"]),
            "by_size": dict(stats["by_size"]),
            "revenue_potential": {
                "total_min": stats["revenue_potential"]["total_min"],
                "total_max": stats["revenue_potential"]["total_max"],
                "by_category": {k: dict(v) for k, v in stats["revenue_potential"]["by_category"].items()}
            },
            "contact_quality": stats["contact_quality"]
        }
        json.dump(stats_json, f, indent=2)
    
    print(f"\n{'='*80}")
    print("Detailed statistics saved to: /home/ubuntu/lead_stats.json")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
