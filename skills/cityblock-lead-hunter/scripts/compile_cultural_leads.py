'''
This script compiles the results from the parallel cultural lead generation task.
It reads the JSON output, parses the CSV data from each sub-task, cleans it,
assigns a final sequential rank, and saves it to a master CSV file.
'''
import json
import csv
import io

# Define file paths
json_input_path = '/home/ubuntu/miami_cultural_leads_generation.json'
csv_output_path = '/home/ubuntu/miami_leads/Miami_Cultural_Website_Leads_500.csv'

# Load the parallel generation results from the JSON file
with open(json_input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

results = data.get('results', [])

# Define the exact header for the final CSV file
header = [
    'rank', 'priority_tier', 'priority_score', 'business_name', 'category_consolidated',
    'category', 'decision_maker', 'phone', 'email', 'address', 'website',
    'instagram_handle', 'website_quality_score', 'website_issues', 'business_description',
    'pain_points', 'website_roi_case', 'revenue_potential', 'urgency_trigger', 'outreach_hook'
]

all_rows = []

# Process each result from the parallel tasks
for result in results:
    if result.get('error'):
        print(f"Skipping batch due to error: {result.get('input')}")
        continue
    
    output = result.get('output', {})
    csv_rows_text = output.get('csv_rows', '')
    
    if not csv_rows_text:
        print(f"Skipping batch with no CSV data: {result.get('input')}")
        continue
    
    # Use the csv module to handle parsing, which correctly handles quoted fields
    reader = csv.reader(io.StringIO(csv_rows_text))
    for row in reader:
        # Basic validation: ensure the row is not empty and has a reasonable number of columns
        if row and len(row) >= 18:
            # Ensure the row has exactly 20 columns, padding with empty strings if necessary
            while len(row) < 20:
                row.append('')
            all_rows.append(row[:20])

# Sort all collected leads by priority_score in descending order
# The priority score is the 3rd column (index 2)
all_rows.sort(key=lambda x: int(x[2]) if x[2].isdigit() else 0, reverse=True)

# Re-assign the final rank based on the sorted order
for i, row in enumerate(all_rows):
    row[0] = i + 1

print(f"Total cultural leads compiled: {len(all_rows)}")

# Write the final, sorted, and re-ranked data to the master CSV file
with open(csv_output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(all_rows)

print(f"Master cultural leads file created at: {csv_output_path}")
