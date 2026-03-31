"""
Reads the parallel map output JSON, skips any failed batches,
and compiles all successful Markdown entries into one unified file.
"""
import json

json_path = '/home/ubuntu/miami_md_playbook_generation.json'
output_path = '/home/ubuntu/miami_leads/Miami_Sales_Playbook.md'

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

results = data.get('results', [])

# Build header
header = """# Miami Sales Playbook
### All Leads — Website Development | AI Services | Cultural Websites

> **How to use this playbook:** Find your lead, read the Opening Line out loud before you call or walk in, then follow the conversation naturally using the Pain Points and Objection Handling sections. Everything is written so you can sell without any technical knowledge.

---

"""

sections = {
    'website': [],
    'ai': [],
    'cultural': [],
}

skipped = 0
total_entries = 0

for result in results:
    if result.get('error'):
        skipped += 1
        continue
    output = result.get('output', {})
    md_text = output.get('markdown_text', '').strip()
    batch_id = output.get('batch_id', '')
    count = output.get('entry_count', 0)

    if not md_text:
        skipped += 1
        continue

    # Determine section from batch_id
    if batch_id.startswith('website'):
        sections['website'].append(md_text)
    elif batch_id.startswith('ai'):
        sections['ai'].append(md_text)
    elif batch_id.startswith('cultural'):
        sections['cultural'].append(md_text)
    else:
        # Try to infer from input path
        inp = result.get('input', '')
        if 'website' in inp:
            sections['website'].append(md_text)
        elif 'ai' in inp:
            sections['ai'].append(md_text)
        elif 'cultural' in inp:
            sections['cultural'].append(md_text)

    total_entries += count

# Assemble the full document
full_doc = header

# Section 1: Website Development Leads
if sections['website']:
    full_doc += "# SECTION 1: WEBSITE DEVELOPMENT LEADS\n\n"
    full_doc += "_These businesses need a new or redesigned website. You are selling a professional website build._\n\n"
    full_doc += "\n\n".join(sections['website'])
    full_doc += "\n\n"

# Section 2: AI Services Leads
if sections['ai']:
    full_doc += "---\n\n# SECTION 2: AI SERVICES LEADS\n\n"
    full_doc += "_These businesses need automation and AI tools. You are selling GoHighLevel CRM, AI chatbots, automated follow-up, and workflow tools._\n\n"
    full_doc += "\n\n".join(sections['ai'])
    full_doc += "\n\n"

# Section 3: Cultural Website Leads
if sections['cultural']:
    full_doc += "---\n\n# SECTION 3: CULTURAL WEBSITE LEADS\n\n"
    full_doc += "_These are minority-owned businesses with strong cultural identities. You are selling a website that tells their cultural story and drives online orders or bookings._\n\n"
    full_doc += "\n\n".join(sections['cultural'])
    full_doc += "\n\n"

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(full_doc)

print(f"Playbook compiled successfully.")
print(f"Total entries: ~{total_entries}")
print(f"Skipped batches: {skipped}")
print(f"Output: {output_path}")
print(f"File size: {len(full_doc):,} characters")
