---
name: boblore
description: Generate IBM Project Bob branded LinkedIn posts in the BobLore style. Use when a user asks to create, write, or generate BobLore posts, #ShouldveGotBOB content, #HeUsesBOB or #SheUsesBOB posts, #HeIsBOB posts, or any IBM Project Bob social media content. Also use when asked to write LinkedIn content for IBM Bob, generate enterprise software humor posts, or create content for the IBM Bob campaign.
---

# BobLore Skill

Generate IBM Project Bob branded LinkedIn posts across four archetypes. All posts follow the canonical two-line format with hashtag and URL.

## Canonical Post Format

Every post MUST follow this exact structure — no exceptions:

```
{SETUP_LINE_1}
{SETUP_LINE_2}

#{HASHTAG}

https://lnkd.in/eS9uw5qt
```

**Example (the gold standard):**
```
You hire a senior COBOL developer.
Day one, they call it "Cobalt."

#ShouldveGotBOB

https://lnkd.in/eS9uw5qt
```

Rules:
- Exactly **two setup lines** — scene-setter and punchline/consequence.
- Blank line between setup and hashtag. Blank line between hashtag and URL.
- URL is always `https://lnkd.in/eS9uw5qt`.
- Hashtag casing: `#ShouldveGotBOB`, `#HeUsesBOB`, `#SheUsesBOB`, `#HeIsBOB`.

## The Four Archetypes

| Archetype | Hashtag | Voice | Purpose |
|---|---|---|---|
| Pain Point | `#ShouldveGotBOB` | Dry, deadpan corporate tragedy | Enterprise software failures that Bob would have prevented |
| Legendary Developer (male) | `#HeUsesBOB` | Mythological, Chuck Norris-style | Superhuman male developer whose powers are amplified by Bob |
| Legendary Developer (female) | `#SheUsesBOB` | Mythological, Chuck Norris-style | Superhuman female developer whose powers are amplified by Bob |
| Bob Personified | `#HeIsBOB` | Reverent, transcendent | Bob himself as a legendary AI entity beyond category |

For full examples, voice rules, and pain-point taxonomy for each archetype, read:
`/home/ubuntu/skills/boblore/references/boblore_library.md`

## Workflow

### Option A: Use the Generation Script (Recommended for Batches)

```bash
# Generate 5 #ShouldveGotBOB posts
python /home/ubuntu/skills/boblore/scripts/generate_posts.py --archetype shouldvegotbob --count 5

# Generate 3 posts focused on a specific topic
python /home/ubuntu/skills/boblore/scripts/generate_posts.py --archetype shouldvegotbob --topic "cloud migration" --count 3

# Generate posts for all archetypes
python /home/ubuntu/skills/boblore/scripts/generate_posts.py --archetype all --count 5

# Available archetypes: shouldvegotbob | heusesbob | sheusesbob | heisbob | all
```

The script outputs fully formatted posts, separated by `---`, ready to copy-paste to LinkedIn.

### Option B: Write Manually (For Single Posts or Custom Requests)

1. Read `boblore_library.md` to select the right archetype and draw from the pain-point or skill-domain taxonomy.
2. Write exactly two lines following the voice rules for the chosen archetype.
3. Apply the canonical format: two lines, blank line, hashtag, blank line, URL.

## Quality Standards

- **Specificity over generality.** "Your app crashed" is weak. "Your app crashes if the user's name contains a vowel" is BobLore.
- **Absurd but plausible.** The punchline should feel like something that could actually happen in enterprise software, taken one step further.
- **Never mention competitors.** Only IBM Project Bob exists in the BobLore universe.
- **Rotate gender** between `#HeUsesBOB` and `#SheUsesBOB` for inclusivity.
- **BOB is always capitalized** in hashtags.
