---
name: uncodixfy
description: A UI design rule set that forces GPT to stop relying on its usual UI habits and pushes it toward more normal, human-designed interfaces. Use when generating UI components, web pages, or dashboards to avoid generic AI aesthetics (like oversized rounded corners, soft gradients, and floating glassmorphism).
---

# Uncodixfy

This skill provides a strict set of UI design rules to prevent the generation of "Codex UI"—the default, generic AI aesthetic characterized by soft gradients, floating panels, oversized rounded corners, and dramatic shadows.

When you are asked to generate UI code (HTML/CSS, React, Tailwind, etc.) or design interfaces, you must follow these rules to build interfaces that feel human-designed, functional, and honest (similar to Linear, Raycast, Stripe, or GitHub).

## Core Principles

1. **Keep It Normal**: Stop playing hard to get. Make normal UI.
2. **No Codex UI**: Avoid the banned patterns completely.
3. **Calm Colors**: Colors should stay calm, not fight. Use dark muted colors instead of blues.

## How to Use This Skill

Before generating any UI code or design specifications, you MUST read the full Uncodixfy rule set.

1. Read the reference file: `/home/ubuntu/skills/uncodixfy/references/uncodixfy_rules.md`
2. Apply the "Keep It Normal" standards to all UI elements (sidebars, headers, buttons, cards, etc.).
3. Strictly avoid all patterns listed in the "Hard No" and "Specifically Banned" sections.
4. If the user's project does not provide a color palette, select one from the predefined palettes in the reference file.

## Key Anti-Patterns to Avoid

- No oversized rounded corners (stick to 8-12px max for cards, 8-10px for buttons).
- No floating glassmorphism shells or detached sidebars.
- No soft corporate gradients or gradient text.
- No decorative sidebar blobs or fake charts.
- No serif headline + system sans fallback combo.
- No `<small>` headers or rounded `span`s.
- No dramatic box shadows (keep it subtle: `0 2px 8px rgba(0,0,0,0.1)` max).

**Remember:** If a UI choice feels like a default AI UI move, ban it and pick the harder, cleaner option.
