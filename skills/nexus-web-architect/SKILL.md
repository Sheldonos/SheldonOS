---
name: advanced-web-developer
description: A power-stacked web development workflow that combines Google Stitch (AI mockup generation), Nano Banana 2 (image-based slide presentations), 21st.dev Magic (3D and reactive React component library), and the UI/UX Pro Max design system engine. Use this skill when building any web application, landing page, dashboard, or product UI where you need to go from concept to production-ready code with maximum visual quality and speed. Triggers on tasks involving web design, UI mockups, component generation, design systems, frontend development, or client presentations.
---

# Advanced Web Developer

This skill encodes a complete, AI-powered web development pipeline. It fuses four distinct tools into a single, coherent workflow: the **UI/UX Pro Max** design system engine, **Google Stitch** for AI-generated mockups, **21st.dev Magic** for production-ready 3D and reactive components, and **Nano Banana 2** for image-based client presentations.

## Workflow Overview

```
PHASE 1: Design System  →  PHASE 2: Mockups  →  PHASE 3: Components  →  PHASE 4: Present
  (UI/UX Pro Max)           (Google Stitch)       (21st.dev Magic)       (Nano Banana 2)
```

Each phase feeds directly into the next. Complete them in order. Skip a phase only when explicitly not needed (e.g., skip Phase 4 if no presentation is required).

---

## Phase 1: Design System Generation (UI/UX Pro Max)

Always start here. The design system is the single source of truth for all subsequent phases.

**Run the design system generator:**

```bash
python3 /home/ubuntu/skills/advanced-web-developer/ui-ux-pro-max/src/ui-ux-pro-max/scripts/core.py \
  "<product_type> <industry> <style_keywords>" \
  --design-system \
  --persist \
  -p "Project Name"
```

This outputs a `design-system/MASTER.md` file containing:

| Output | Description |
|---|---|
| Color palette | Primary, secondary, CTA, background, text hex values |
| Typography | Heading and body font pairings with Google Fonts URLs |
| UI pattern | Recommended layout and component style |
| Effects | Animation, glassmorphism, gradients, shadows |
| Anti-patterns | What to avoid for this product type |

**Supplement with domain searches as needed:**

```bash
# Get UX best practices
python3 .../core.py "animation accessibility" --domain ux

# Get landing page structure
python3 .../core.py "hero social-proof CTA" --domain landing

# Get stack-specific guidelines (default: html-tailwind)
python3 .../core.py "layout responsive" --stack nextjs
```

Available stacks: `html-tailwind`, `react`, `nextjs`, `vue`, `svelte`, `shadcn`, `react-native`, `flutter`

---

## Phase 2: AI Mockup Generation (Google Stitch)

Use the design system output from Phase 1 to craft a precise prompt for Google Stitch.

**Navigate to:** [stitch.withgoogle.com](https://stitch.withgoogle.com/)

**Prompt construction formula:**

> "Design a [screen type] for a [product type]. Use a [light/dark] theme. Primary color: [hex]. Secondary: [hex]. Background: [hex]. Typography: [heading font] for headings, [body font] for body. Style: [style keywords from design system]. Include: [specific UI elements needed]."

**Example prompt:**

> "Design a SaaS dashboard for a fintech analytics platform. Use a dark theme. Primary: #6366F1. Background: #0F172A. Typography: Inter for both headings and body. Style: minimalist, glassmorphism cards with subtle borders. Include: KPI metric cards, a revenue trend chart, a recent transactions table, and a left sidebar with navigation."

**After generation:**

1. Use Stitch's **Direct Edits** feature to refine specific elements.
2. Export to **Figma** for team collaboration, or export as **React/JSX** or **Tailwind HTML** for direct use.
3. Save exported code or Figma link — it becomes the blueprint for Phase 3.

For full Stitch capabilities (prototyping, multi-screen flows, code export options), see [references/google-stitch.md](references/google-stitch.md).

---

## Phase 3: Component Generation (21st.dev Magic)

With the mockup as a visual spec, generate production-ready React components using 21st.dev Magic.

### Setup (one-time)

```bash
npx @21st-dev/cli@latest install <cursor|windsurf|cline|claude> --api-key <YOUR_API_KEY>
```

Get your API key at [21st.dev/magic](https://21st.dev/magic).

### Generating Components

In your IDE's AI chat, use the `/ui` command:

```
/ui [describe the component with style, behavior, and layout details]
```

**Example prompts:**

```
/ui create a glassmorphism pricing card with three tiers (Starter, Pro, Enterprise),
a monthly/yearly toggle, feature lists, and a gradient CTA button. Use Tailwind CSS.

/ui build an interactive 3D product showcase hero section with a rotating card
gallery, particle background, and a bold headline with gradient text.

/ui generate a responsive data table with sortable columns, row selection checkboxes,
pagination, and a search input. TypeScript with shadcn/ui components.
```

Magic generates multiple variations — browse them and select the best match. The component is automatically integrated into your project.

### Browsing the 21st.dev Library Directly

For specialized 3D and animated components, browse the community library:

| Category | URL | Best For |
|---|---|---|
| 3D Components | [21st.dev/community/components/s/3d](https://21st.dev/community/components/s/3d) | Hero sections, galleries, interactive showcases |
| Animated | [21st.dev/community/components/s/animated](https://21st.dev/community/components/s/animated) | Scroll effects, transitions, micro-interactions |
| Shaders/WebGL | [21st.dev/community/components/s/shaders](https://21st.dev/community/components/s/shaders) | Particle effects, glitter, fluid backgrounds |
| Heroes | [21st.dev/community/components/s/heroes](https://21st.dev/community/components/s/heroes) | Landing page hero sections |
| Backgrounds | [21st.dev/community/components/s/backgrounds](https://21st.dev/community/components/s/backgrounds) | Animated and static backgrounds |

For full setup and advanced usage, see [references/21st-dev.md](references/21st-dev.md).

---

## Phase 4: Client Presentation (Nano Banana 2)

When presenting designs, mockups, or the final product to clients or stakeholders, use the `slides` tool with `generate_mode="image"` to invoke Nano Banana 2. This renders each slide as a photorealistic, high-fidelity image — ideal for showcasing UI work.

**Step 1: Write the slide content file**

Create a Markdown file with the presentation structure. Include descriptions of what each slide should visually show (Nano Banana 2 will render them as images).

**Step 2: Generate the presentation**

```python
slides(
    brief="Client presentation for [Project Name] web application design",
    slide_content_file_path="/home/ubuntu/[project]/slide_content.md",
    slide_count=10,
    generate_mode="image"
)
```

**Recommended slide structure for design presentations:**

| Slide | Content |
|---|---|
| 1 | Title slide — project name, tagline, client logo |
| 2 | Problem statement and design goals |
| 3 | Design system overview (colors, typography, style) |
| 4–7 | Key screens / mockups (hero, dashboard, mobile, etc.) |
| 8 | Component library highlights (3D/animated components) |
| 9 | Technical stack and implementation approach |
| 10 | Next steps and call to action |

---

## Pre-Delivery Checklist

Before delivering any UI code or design, verify:

**Visual Quality**
- [ ] No emojis used as icons — use SVG (Heroicons, Lucide, Simple Icons)
- [ ] All icons from a consistent set with fixed 24x24 viewBox
- [ ] Brand logos verified from Simple Icons
- [ ] Hover states do not cause layout shift

**Interaction**
- [ ] All clickable elements have `cursor-pointer`
- [ ] Hover states provide clear visual feedback
- [ ] Transitions are smooth (150–300ms)
- [ ] Focus states visible for keyboard navigation

**Light/Dark Mode**
- [ ] Light mode text contrast meets 4.5:1 minimum
- [ ] Glass/transparent elements visible in light mode
- [ ] Borders visible in both modes

**Layout**
- [ ] Responsive at 375px, 768px, 1024px, 1440px
- [ ] No horizontal scroll on mobile
- [ ] No content hidden behind fixed navbars

**Accessibility**
- [ ] All images have descriptive alt text
- [ ] Form inputs have associated labels
- [ ] `prefers-reduced-motion` respected

---

## Bundled Resources

| Resource | Path | Purpose |
|---|---|---|
| UI/UX Pro Max Engine | `ui-ux-pro-max/src/ui-ux-pro-max/` | Design system generation scripts and data |
| Google Stitch Guide | `references/google-stitch.md` | Prompting, export, and iteration guide |
| 21st.dev Guide | `references/21st-dev.md` | MCP setup, component generation, library browsing |
