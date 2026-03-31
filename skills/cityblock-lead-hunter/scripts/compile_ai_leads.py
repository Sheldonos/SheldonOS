import json
import csv
import io
import re

# Load parallel results
with open('/home/ubuntu/miami_ai_leads_generation.json', 'r') as f:
    data = json.load(f)

results = data['results']

header = [
    'Lead ID', 'Business Name', 'Decision Maker', 'Phone', 'Email', 'Address',
    'Website', 'LinkedIn', 'Category', 'Size', 'Description', 'Pain Points',
    'AI Solutions', 'Use Cases & ROI', 'Cost of Doing Nothing', 'Revenue Potential', 'Vertical'
]

# Valid categories from our batches
valid_categories = {
    'Healthcare & Medical Practices',
    'Law Firms & Legal Services',
    'Real Estate Brokerages & Agents',
    'Home Services (HVAC, Plumbing, Electrical)',
    'Financial Services & Accounting',
    'Beauty & Personal Care',
    'Fitness & Wellness',
    'Restaurants & Food Service',
    'Retail & E-commerce',
    'Professional Services & Consulting',
    'Construction & Contractors',
    'Automotive Services',
    'Education & Childcare',
    'Hospitality & Hotels',
    'Immigration & International Trade',
    'Insurance Agencies',
    'Dental & Medical Specialty',
    'Marketing & Creative Agencies',
    'Logistics & Transportation',
    'Pet Services & Veterinary',
}

valid_sizes = {'Small (1-10)', 'Medium (11-50)', 'Large (51-200)', 'Small', 'Medium', 'Large'}

valid_verticals = {
    'Healthcare & Medical',
    'Legal, Financial & Professional Services',
    'Real Estate & Construction',
    'Home Services & Trades',
    'Hospitality & Food Service',
    'Retail & Consumer',
    'Education & Childcare',
    'Technology & Professional Services',
}

all_rows = []
lead_counter = 1
skipped = 0

for result in results:
    if result.get('error'):
        print(f"Error in batch: {result['error']}")
        continue
    
    output = result.get('output', {})
    csv_rows_text = output.get('csv_rows', '')
    category_name = output.get('category_name', '')
    
    if not csv_rows_text:
        print(f"No CSV rows for: {result['input']}")
        continue
    
    # Parse CSV rows
    reader = csv.reader(io.StringIO(csv_rows_text))
    batch_rows = []
    for row in reader:
        if not row or len(row) < 5:
            continue
        # Skip any accidental header rows
        if row[0].strip().lower() in ['lead id', 'lead_id', '#', 'lead #', 'lead']:
            continue
        # Skip rows where field 8 (Category) is not a valid category
        # This filters out malformed rows
        if len(row) >= 9:
            cat_field = row[8].strip().strip('"')
            if cat_field not in valid_categories:
                # Try to check if it looks like a valid row (has phone-like field)
                phone_field = row[3].strip() if len(row) > 3 else ''
                if not re.search(r'\(?\d{3}\)?[\s\-]\d{3}[\s\-]\d{4}', phone_field):
                    skipped += 1
                    continue
        
        # Ensure exactly 17 fields
        while len(row) < 17:
            row.append('')
        row = row[:17]
        
        # Clean up size field - normalize
        size_field = row[9].strip().strip('"')
        if not any(v in size_field for v in ['Small', 'Medium', 'Large']):
            row[9] = 'Small (1-10)'
        elif 'Small' in size_field and '(' not in size_field:
            row[9] = 'Small (1-10)'
        elif 'Medium' in size_field and '(' not in size_field:
            row[9] = 'Medium (11-50)'
        elif 'Large' in size_field and '(' not in size_field:
            row[9] = 'Large (51-200)'
        
        # Clean up vertical field
        vert_field = row[16].strip().strip('"')
        if vert_field not in valid_verticals:
            # Map category to vertical
            cat = row[8].strip().strip('"')
            if 'Healthcare' in cat or 'Medical' in cat or 'Dental' in cat:
                row[16] = 'Healthcare & Medical'
            elif 'Law' in cat or 'Legal' in cat or 'Financial' in cat or 'Insurance' in cat or 'Accounting' in cat:
                row[16] = 'Legal, Financial & Professional Services'
            elif 'Real Estate' in cat or 'Construction' in cat:
                row[16] = 'Real Estate & Construction'
            elif 'Home Services' in cat or 'Plumbing' in cat or 'HVAC' in cat or 'Automotive' in cat or 'Landscaping' in cat:
                row[16] = 'Home Services & Trades'
            elif 'Restaurant' in cat or 'Food' in cat or 'Hospitality' in cat or 'Hotel' in cat:
                row[16] = 'Hospitality & Food Service'
            elif 'Retail' in cat or 'Beauty' in cat or 'Pet' in cat or 'Fitness' in cat:
                row[16] = 'Retail & Consumer'
            elif 'Education' in cat or 'Childcare' in cat:
                row[16] = 'Education & Childcare'
            else:
                row[16] = 'Technology & Professional Services'
        
        # Re-assign Lead ID sequentially
        row[0] = f'MIA-AI-{lead_counter:04d}'
        lead_counter += 1
        
        batch_rows.append(row)
    
    all_rows.extend(batch_rows)

print(f"Total AI leads compiled: {len(all_rows)}")
print(f"Skipped malformed rows: {skipped}")

# Write master CSV
output_path = '/home/ubuntu/miami_leads/Miami_AI_Services_1000_Leads_MASTER.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(all_rows)

print(f"Written to: {output_path}")

# Print category breakdown
categories = {}
verticals = {}
revenue_min_total = 0
revenue_max_total = 0
revenue_count = 0

for row in all_rows:
    cat = row[8].strip().strip('"') if len(row) > 8 else 'Unknown'
    vert = row[16].strip().strip('"') if len(row) > 16 else 'Unknown'
    categories[cat] = categories.get(cat, 0) + 1
    verticals[vert] = verticals.get(vert, 0) + 1
    
    # Parse revenue potential
    rev = row[15] if len(row) > 15 else ''
    nums = re.findall(r'[\d,]+', rev.replace('$', ''))
    if len(nums) >= 2:
        try:
            v1 = int(nums[0].replace(',', ''))
            v2 = int(nums[1].replace(',', ''))
            if 500 <= v1 <= 200000 and 500 <= v2 <= 200000:
                revenue_min_total += min(v1, v2)
                revenue_max_total += max(v1, v2)
                revenue_count += 1
        except:
            pass

print("\nCategory breakdown:")
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")

print("\nVertical breakdown:")
for v, count in sorted(verticals.items(), key=lambda x: -x[1]):
    print(f"  {v}: {count}")

print(f"\nTotal pipeline: ${revenue_min_total:,} - ${revenue_max_total:,}")
if revenue_count > 0:
    print(f"Average deal size: ${revenue_min_total//revenue_count:,} - ${revenue_max_total//revenue_count:,}")
