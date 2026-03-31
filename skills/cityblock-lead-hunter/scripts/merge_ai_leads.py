import pandas as pd
import os

# Define file paths
main_file = '/home/ubuntu/miami_leads/Miami_AI_Services_1000_Leads_MASTER.csv'
supplemental_json = '/home/ubuntu/miami_ai_leads_supplemental.json'
output_file = '/home/ubuntu/miami_leads/Miami_AI_Services_Leads_FINAL.csv'

# Load the main CSV into a DataFrame
if not os.path.exists(main_file):
    print(f"Main file not found: {main_file}")
    exit()

df_main = pd.read_csv(main_file)
print(f"Loaded {len(df_main)} leads from the main file.")

# Load and parse the supplemental JSON data
import json
import csv
import io

if not os.path.exists(supplemental_json):
    print(f"Supplemental file not found: {supplemental_json}")
    exit()

with open(supplemental_json, 'r') as f:
    supp_data = json.load(f)

supp_rows = []
header = df_main.columns.tolist()

for result in supp_data.get('results', []):
    if result.get('error'):
        continue
    output = result.get('output', {})
    csv_rows_text = output.get('csv_rows', '')
    if not csv_rows_text:
        continue
    
    reader = csv.reader(io.StringIO(csv_rows_text))
    for row in reader:
        if row and len(row) == len(header):
            supp_rows.append(row)

if supp_rows:
    df_supp = pd.DataFrame(supp_rows, columns=header)
    print(f"Loaded {len(df_supp)} leads from the supplemental file.")

    # Append supplemental leads to the main dataframe
    df_combined = pd.concat([df_main, df_supp], ignore_index=True)
else:
    df_combined = df_main
    print("No valid supplemental leads to append.")

# Reset the Lead ID to be sequential
for i in range(len(df_combined)):
    df_combined.loc[i, 'Lead ID'] = f'MIA-AI-{i + 1:04d}'

# Save the final combined data to a new CSV
df_combined.to_csv(output_file, index=False)

print(f"Successfully merged all AI leads. Total: {len(df_combined)}.")
print(f"Final master file saved to: {output_file}")
