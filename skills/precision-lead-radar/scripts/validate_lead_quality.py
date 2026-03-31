#!/usr/bin/env python3
"""
Lead Quality Validation Script
Checks completeness and quality of lead data
"""

import csv
import re
import sys
from typing import Dict, List

def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email or email == 'Not publicly available':
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone format"""
    if not phone:
        return False
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    # Check if it's a valid length (10-15 digits)
    return len(cleaned) >= 10 and cleaned.isdigit()

def validate_url(url: str) -> bool:
    """Validate URL format"""
    if not url or url == 'Not found':
        return False
    return url.startswith('http://') or url.startswith('https://')

def calculate_lead_score(row: Dict) -> Dict:
    """
    Calculate quality score for a lead (0-100)
    
    Scoring criteria:
    - Business Name: 10 points
    - Decision Maker: 15 points
    - Phone: 10 points
    - Email: 15 points (higher value)
    - Address: 5 points
    - Website: 10 points
    - LinkedIn: 10 points
    - Pain Points: 10 points
    - AI Solutions: 10 points
    - Use Cases & ROI: 10 points
    - Revenue Potential: 5 points
    """
    
    score = 0
    issues = []
    
    # Business Name (10 points)
    if row.get('Business Name'):
        score += 10
    else:
        issues.append("Missing business name")
    
    # Decision Maker (15 points)
    if row.get('Decision Maker'):
        score += 15
    else:
        issues.append("Missing decision maker")
    
    # Phone (10 points)
    if validate_phone(row.get('Phone', '')):
        score += 10
    else:
        issues.append("Invalid or missing phone")
    
    # Email (15 points - high value)
    if validate_email(row.get('Email', '')):
        score += 15
    else:
        issues.append("Invalid or missing email")
    
    # Address (5 points)
    if row.get('Address'):
        score += 5
    else:
        issues.append("Missing address")
    
    # Website (10 points)
    if validate_url(row.get('Website', '')):
        score += 10
    else:
        issues.append("Invalid or missing website")
    
    # LinkedIn (10 points)
    if validate_url(row.get('LinkedIn', '')):
        score += 10
    else:
        issues.append("Missing LinkedIn profile")
    
    # Pain Points (10 points)
    pain_points = row.get('Pain Points', '')
    if pain_points and len(pain_points) > 50:
        score += 10
    else:
        issues.append("Insufficient pain points detail")
    
    # AI Solutions (10 points)
    solutions = row.get('AI Solutions', '')
    if solutions and len(solutions) > 50:
        score += 10
    else:
        issues.append("Insufficient solution detail")
    
    # Use Cases & ROI (10 points)
    use_cases = row.get('Use Cases & ROI', '')
    if use_cases and len(use_cases) > 50:
        score += 10
    else:
        issues.append("Insufficient use case detail")
    
    # Revenue Potential (5 points)
    rev_pot = row.get('Revenue Potential', '')
    if rev_pot and '$' in rev_pot:
        score += 5
    else:
        issues.append("Missing revenue potential")
    
    return {
        "score": score,
        "grade": get_grade(score),
        "issues": issues
    }

def get_grade(score: int) -> str:
    """Convert score to letter grade"""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"

def validate_leads(csv_file: str) -> Dict:
    """Validate all leads in CSV file"""
    
    results = {
        "total_leads": 0,
        "scores": [],
        "grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
        "common_issues": {},
        "leads_with_issues": []
    }
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            if row.get('Error'):
                continue
            
            results["total_leads"] += 1
            
            validation = calculate_lead_score(row)
            score = validation["score"]
            grade = validation["grade"]
            issues = validation["issues"]
            
            results["scores"].append(score)
            results["grade_distribution"][grade] += 1
            
            # Track common issues
            for issue in issues:
                results["common_issues"][issue] = results["common_issues"].get(issue, 0) + 1
            
            # Track leads with significant issues (score < 70)
            if score < 70:
                results["leads_with_issues"].append({
                    "row": idx,
                    "business": row.get('Business Name', 'Unknown'),
                    "score": score,
                    "grade": grade,
                    "issues": issues
                })
    
    # Calculate average score
    if results["scores"]:
        results["average_score"] = sum(results["scores"]) / len(results["scores"])
    else:
        results["average_score"] = 0
    
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_lead_quality.py <lead_database.csv>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    print("=" * 80)
    print("LEAD QUALITY VALIDATION REPORT")
    print("=" * 80)
    print(f"File: {csv_file}\n")
    
    results = validate_leads(csv_file)
    
    print(f"Total Leads Analyzed: {results['total_leads']}")
    print(f"Average Quality Score: {results['average_score']:.1f}/100\n")
    
    print("=" * 80)
    print("GRADE DISTRIBUTION")
    print("=" * 80)
    for grade in ["A", "B", "C", "D", "F"]:
        count = results["grade_distribution"][grade]
        pct = (count / results["total_leads"] * 100) if results["total_leads"] > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"{grade}: {count:3d} ({pct:5.1f}%) {bar}")
    
    print("\n" + "=" * 80)
    print("COMMON ISSUES (Top 10)")
    print("=" * 80)
    sorted_issues = sorted(results["common_issues"].items(), key=lambda x: x[1], reverse=True)
    for issue, count in sorted_issues[:10]:
        pct = (count / results["total_leads"] * 100) if results["total_leads"] > 0 else 0
        print(f"{issue:40s} {count:3d} ({pct:5.1f}%)")
    
    if results["leads_with_issues"]:
        print("\n" + "=" * 80)
        print(f"LEADS REQUIRING ATTENTION (Score < 70): {len(results['leads_with_issues'])}")
        print("=" * 80)
        for lead in results["leads_with_issues"][:10]:  # Show first 10
            print(f"\nRow {lead['row']}: {lead['business']} (Score: {lead['score']}, Grade: {lead['grade']})")
            for issue in lead["issues"]:
                print(f"  - {issue}")
        
        if len(results["leads_with_issues"]) > 10:
            print(f"\n... and {len(results['leads_with_issues']) - 10} more")
    
    print("\n" + "=" * 80)
    print("QUALITY ASSESSMENT")
    print("=" * 80)
    
    avg_score = results["average_score"]
    if avg_score >= 85:
        print("✓ EXCELLENT: Lead database is high quality and ready for outreach")
    elif avg_score >= 75:
        print("✓ GOOD: Lead database is solid, minor improvements recommended")
    elif avg_score >= 65:
        print("⚠ FAIR: Lead database needs improvement in several areas")
    else:
        print("✗ POOR: Lead database requires significant enrichment before use")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
