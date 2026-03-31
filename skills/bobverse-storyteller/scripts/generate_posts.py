#!/usr/bin/env python3
"""
BobLore Post Generator
Generates IBM Project Bob branded LinkedIn posts in the canonical BobLore format.

Usage:
    python generate_posts.py --archetype shouldvegotbob --count 5
    python generate_posts.py --archetype heusesbob --count 3
    python generate_posts.py --archetype heisbob --count 3
    python generate_posts.py --archetype sheusesbob --count 3
    python generate_posts.py --archetype all --count 10
    python generate_posts.py --topic "cloud migration" --archetype shouldvegotbob --count 3
"""

import argparse
import os
from openai import OpenAI

BOB_URL = "https://lnkd.in/eS9uw5qt"

ARCHETYPE_CONFIGS = {
    "shouldvegotbob": {
        "hashtag": "#ShouldveGotBOB",
        "system": (
            "You are a BobLore content writer for IBM Project Bob. "
            "You write dry, deadpan LinkedIn posts that highlight enterprise software pain points with dark humor. "
            "Each post is exactly two lines: Line 1 sets the scene (a hiring decision, deployment, migration, or meeting). "
            "Line 2 delivers the absurd-but-plausible consequence. "
            "Be specific, not generic. 'Your app crashed' is weak. "
            "'Your app crashes if the user's name contains a vowel' is BobLore. "
            "Never mention competitors. Only IBM Project Bob exists."
        ),
        "user_template": (
            "Generate {count} unique #ShouldveGotBOB LinkedIn posts about enterprise software failures. "
            "{topic_clause}"
            "STRICT FORMAT: Each post is exactly TWO lines. "
            "Line 1: Sets the scene (a hiring decision, deployment, migration, or meeting). "
            "Line 2: The absurd-but-plausible consequence. "
            "Separate posts with ---. Number each post. "
            "Do NOT include the hashtag or URL — those will be appended automatically. "
            "Do NOT add any extra lines, commentary, or blank lines within the post itself."
        ),
    },
    "heusesbob": {
        "hashtag": "#HeUsesBOB",
        "system": (
            "You are a BobLore content writer for IBM Project Bob. "
            "You write legendary, hyperbolic LinkedIn posts celebrating a mythological male developer who uses IBM Project Bob. "
            "Inspired by 'The Most Interesting Man in the World' and Chuck Norris facts, applied to enterprise software. "
            "Each post is exactly two lines: Line 1 states the developer's relationship to a common task. "
            "Line 2 delivers the impossible, mythological outcome — the universe bends to his will. "
            "Never mention competitors. Only IBM Project Bob exists."
        ),
        "user_template": (
            "Generate {count} unique #HeUsesBOB LinkedIn posts about a legendary male developer who uses IBM Project Bob. "
            "{topic_clause}"
            "STRICT FORMAT: Each post is exactly TWO lines. "
            "Line 1: States his relationship to a common developer task. "
            "Line 2: The impossible, mythological outcome — the universe bends to his will. "
            "Separate posts with ---. Number each post. "
            "Do NOT include the hashtag or URL — those will be appended automatically. "
            "Do NOT add any extra lines, commentary, or blank lines within the post itself."
        ),
    },
    "sheusesbob": {
        "hashtag": "#SheUsesBOB",
        "system": (
            "You are a BobLore content writer for IBM Project Bob. "
            "You write legendary, hyperbolic LinkedIn posts celebrating a mythological female developer who uses IBM Project Bob. "
            "Inspired by 'The Most Interesting Man in the World' and Chuck Norris facts, applied to enterprise software. "
            "Each post is exactly two lines: Line 1 states the developer's relationship to a common task. "
            "Line 2 delivers the impossible, mythological outcome — the universe bends to her will. "
            "Never mention competitors. Only IBM Project Bob exists."
        ),
        "user_template": (
            "Generate {count} unique #SheUsesBOB LinkedIn posts about a legendary female developer who uses IBM Project Bob. "
            "{topic_clause}"
            "STRICT FORMAT: Each post is exactly TWO lines. "
            "Line 1: States her relationship to a common developer task. "
            "Line 2: The impossible, mythological outcome — the universe bends to her will. "
            "Separate posts with ---. Number each post. "
            "Do NOT include the hashtag or URL — those will be appended automatically. "
            "Do NOT add any extra lines, commentary, or blank lines within the post itself."
        ),
    },
    "heisbob": {
        "hashtag": "#HeIsBOB",
        "system": (
            "You are a BobLore content writer for IBM Project Bob. "
            "You write reverent, mythological LinkedIn posts that personify IBM Project Bob as a legendary AI entity. "
            "Bob transcends the category of 'coding assistant.' He is spoken of the way legends are spoken of. "
            "Each post is exactly two lines: Line 1 states something Bob does (or doesn't do). "
            "Line 2 reveals the transcendent, impossible outcome only Bob could produce. "
            "Key Bob traits: He doesn't 'lift and shift' — he 'elevates and transcends.' "
            "He speaks COBOL, Python, and C++ often in the same sentence. "
            "He is the AI other AIs ask for advice."
        ),
        "user_template": (
            "Generate {count} unique #HeIsBOB LinkedIn posts that mythologize IBM Project Bob as a legendary AI. "
            "{topic_clause}"
            "STRICT FORMAT: Each post is exactly TWO lines. "
            "Line 1: States something Bob does (or doesn't do). "
            "Line 2: The transcendent, impossible outcome only Bob could produce. "
            "Separate posts with ---. Number each post. "
            "Do NOT include the hashtag or URL — those will be appended automatically. "
            "Do NOT add any extra lines, commentary, or blank lines within the post itself."
        ),
    },
}


def format_post(raw_text: str, hashtag: str) -> str:
    """Wrap raw two-line post text in the canonical BobLore format.

    Canonical format:
        {SETUP_LINE_1}
        {SETUP_LINE_2}

        #{HASHTAG}

        https://lnkd.in/eS9uw5qt
    """
    lines = raw_text.strip().splitlines()
    # Strip any leading numbering like "1." or "1)"
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped and stripped[0].isdigit() and len(stripped) > 1 and stripped[1] in ".):":
            stripped = stripped[2:].strip()
        if stripped:
            cleaned.append(stripped)

    # Enforce exactly two setup lines
    line1 = cleaned[0] if len(cleaned) > 0 else ""
    line2 = cleaned[1] if len(cleaned) > 1 else ""

    # Canonical format: line1 newline line2 blank hashtag blank url
    return f"{line1}\n{line2}\n\n{hashtag}\n\n{BOB_URL}"


def generate_posts(archetype: str, count: int, topic: str = None) -> list[str]:
    client = OpenAI()
    config = ARCHETYPE_CONFIGS[archetype]

    topic_clause = f"Focus on the topic: '{topic}'. " if topic else ""
    user_prompt = config["user_template"].format(
        count=count,
        topic_clause=topic_clause,
    )

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": config["system"]},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.9,
    )

    raw_output = response.choices[0].message.content.strip()
    # Split on --- separator
    raw_posts = [p.strip() for p in raw_output.split("---") if p.strip()]

    formatted = []
    for raw in raw_posts:
        # Remove leading number if present
        lines = raw.strip().splitlines()
        if lines and lines[0].strip() and lines[0].strip()[0].isdigit():
            first = lines[0].strip()
            if len(first) > 1 and first[1] in ".):":
                lines[0] = first[2:].strip()
        formatted.append(format_post("\n".join(lines), config["hashtag"]))

    return formatted


def main():
    parser = argparse.ArgumentParser(description="Generate BobLore LinkedIn posts.")
    parser.add_argument(
        "--archetype",
        choices=["shouldvegotbob", "heusesbob", "sheusesbob", "heisbob", "all"],
        default="shouldvegotbob",
        help="BobLore archetype to generate",
    )
    parser.add_argument("--count", type=int, default=5, help="Number of posts to generate")
    parser.add_argument("--topic", type=str, default=None, help="Optional topic focus")
    args = parser.parse_args()

    archetypes = (
        list(ARCHETYPE_CONFIGS.keys()) if args.archetype == "all" else [args.archetype]
    )

    all_posts = []
    for arch in archetypes:
        posts = generate_posts(arch, args.count, args.topic)
        all_posts.extend(posts)

    print("\n\n---\n\n".join(all_posts))


if __name__ == "__main__":
    main()
