import json
import csv
import re
import io

# Load parallel results
with open('/home/ubuntu/miami_website_leads_generation.json', 'r') as f:
    data = json.load(f)

results = data['results']

header = [
    'Lead ID', 'Lead Type', 'Business Name', 'Category', 'Address', 'Phone', 'Email',
    'Website Status', 'Current Website URL', 'Decision Maker', 'LinkedIn',
    'Business Size', 'Years in Business', 'Pain Points', 'Price Tier',
    'Recommended Website Package', 'Est Monthly Revenue Loss ($)', 'Outreach Hook'
]

all_rows = []
lead_counter = 1

for result in results:
    if result.get('error'):
        print(f"Error in batch: {result['error']}")
        continue
    
    output = result.get('output', {})
    csv_rows = output.get('csv_rows', '')
    category_name = output.get('category_name', '')
    
    if not csv_rows:
        print(f"No CSV rows for: {result['input']}")
        continue
    
    # Parse CSV rows
    reader = csv.reader(io.StringIO(csv_rows))
    for row in reader:
        if not row or len(row) < 2:
            continue
        # Skip any accidental header rows
        if row[0].strip().lower() in ['lead id', 'lead_id', '#']:
            continue
        
        # Ensure exactly 18 fields
        while len(row) < 18:
            row.append('')
        row = row[:18]
        
        # Re-assign Lead ID sequentially
        row[0] = f'MIA-{lead_counter:04d}'
        lead_counter += 1
        
        all_rows.append(row)

print(f"Total leads compiled: {len(all_rows)}")

# Write master CSV
output_path = '/home/ubuntu/miami_leads/Miami_Website_Leads_Master.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(all_rows)

print(f"Written to: {output_path}")

# Print category breakdown
categories = {}
lead_types = {}
for row in all_rows:
    cat = row[3] if len(row) > 3 else 'Unknown'
    lt = row[1] if len(row) > 1 else 'Unknown'
    categories[cat] = categories.get(cat, 0) + 1
    lead_types[lt] = lead_types.get(lt, 0) + 1

print("\nCategory breakdown:")
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")

print("\nLead type breakdown:")
for lt, count in sorted(lead_types.items(), key=lambda x: -x[1]):
    print(f"  {lt}: {count}")
