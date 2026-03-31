"""
Splits all three lead CSVs into batch files of 50 rows each,
serialized as JSON lines, saved to /home/ubuntu/miami_leads/batches/
Each batch file contains: source_type, batch_id, rows (list of dicts)
"""
import csv
import json
import os

BATCH_SIZE = 50
BATCH_DIR = '/home/ubuntu/miami_leads/batches'
os.makedirs(BATCH_DIR, exist_ok=True)

files = {
    'website': '/home/ubuntu/miami_leads/Miami_Website_Leads_Master.csv',
    'ai':      '/home/ubuntu/miami_leads/Miami_AI_Services_Leads_FINAL.csv',
    'cultural':'/home/ubuntu/miami_leads/Miami_Cultural_Website_Leads_500.csv',
}

batch_manifest = []  # list of file paths for the map tool

for source_type, path in files.items():
    with open(path, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    # Split into batches
    for i in range(0, len(rows), BATCH_SIZE):
        batch_rows = rows[i:i+BATCH_SIZE]
        batch_id = f"{source_type}_{i//BATCH_SIZE + 1:03d}"
        out_path = os.path.join(BATCH_DIR, f"{batch_id}.json")
        with open(out_path, 'w', encoding='utf-8') as out:
            json.dump({
                'source_type': source_type,
                'batch_id': batch_id,
                'rows': batch_rows
            }, out, ensure_ascii=False)
        batch_manifest.append(out_path)
        print(f"Created batch: {out_path} ({len(batch_rows)} rows)")

# Save manifest
manifest_path = '/home/ubuntu/miami_leads/batches/manifest.json'
with open(manifest_path, 'w') as f:
    json.dump(batch_manifest, f, indent=2)

print(f"\nTotal batches: {len(batch_manifest)}")
print(f"Manifest saved to: {manifest_path}")
