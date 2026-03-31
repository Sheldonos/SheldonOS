# RSPKT.co — Complete Design System Analysis

## Platform
- Built on **Squarespace** (identified via class names like `sqs-block`, `sqs-layout`, `yui3-js-enabled`, and Squarespace CDN URLs)

---

## Typography System

### Font Stack (3-Font Hierarchy — the signature move)
| Role | Font | Weight | Transform | Letter-Spacing |
|------|------|--------|-----------|----------------|
| **Display / Hero Headings** | `pragmatica-extended` | 700 (Bold) | UPPERCASE | Negative (tight: -2.5px to -1.28px) |
| **Body / Paragraph / Monospace** | `courier-std` | 400 (Regular) | none | Normal |
| **Navigation / UI / Utility** | `aktiv-grotesk` | 400–500 | none | Slight positive (+0.35px) |

### Typography Behavior
- Headings are **FULL UPPERCASE** with **negative letter-spacing** (condensed feel)
- Body text uses a **monospace/typewriter font** (Courier Std) — creates editorial, technical, authentic feel
- Navigation uses a clean grotesque — minimal, functional
- **Extreme scale contrast**: hero headings go viewport-width (e.g., "WHAT WE DO" fills the entire screen)
- Line height on headings: ~1.3x; on body: ~1.32x
- Mixed case within single phrases: "A FULL SERVICE creative agency FOCUSed ON premium CONTENT" — intentional case disruption

---

## Color Palette

### Core Colors
| Color | Hex/RGB | Usage |
|-------|---------|-------|
| **Off-White / Cream** | `rgb(250, 250, 250)` / `#FAFAFA` | Primary background |
| **Near-Black** | `rgb(40, 40, 42)` / `#28282A` | Primary text, nav |
| **Pure Black** | `rgb(0, 0, 0)` / `#000000` | Section backgrounds, manifesto |
| **Dark Charcoal** | `rgb(26, 26, 26)` / `#1A1A1A` | Footer background |
| **White** | `rgb(255, 255, 255)` | Text on dark backgrounds |

### Color Strategy
- **High contrast binary**: cream/white vs. black — no mid-tones
- **No brand accent color** on primary site — purity of black/white
- Section backgrounds alternate: cream → black → cream → black (creates rhythm)
- CTA buttons: black background, white text, bordered
- The only "color" is from **photography and video** — the media IS the color palette

---

## Layout Architecture

### Navigation
- **Transparent, floating nav** over hero media
- Logo centered, nav links left, social icons + cart right
- Nav links: ALL CAPS, spaced, no underline by default
- Sticky/fixed position on scroll
- Minimal — no mega-menus, no dropdowns

### Hero Section
- **Full-viewport video or image background** — no text overlay initially
- Tagline appears below the fold, not on the hero itself
- Creates a "cinematic reveal" effect

### Content Sections — Layout Patterns
1. **Full-bleed text** — headline spanning full width, centered
2. **3-column grid** — services displayed in equal-width columns
3. **Split layout** — text left (40%), media right (60%)
4. **Full-bleed dark section** — black background, white bold text (manifesto)
5. **Video gallery** — 3-column grid of embedded video players
6. **CTA band** — full-width dark band with headline left, button right

### Spacing Philosophy
- **Generous whitespace** — sections breathe
- Large padding between sections (60px–120px)
- Content width: ~1265px max-width
- No tight cramming — each section gets room

---

## Design Principles / Aesthetic DNA

### 1. Editorial Boldness
- Headlines are MASSIVE — sometimes 10–15vw font size
- Text is treated as a design element, not just content
- Mixed case disruption creates visual rhythm

### 2. Monochromatic Restraint
- The site is essentially black, white, and cream
- Color comes from photography/video only
- This makes the media POP against the neutral canvas

### 3. Media-First Storytelling
- Video is embedded directly in the page (not linked out)
- Work samples are shown immediately — "show don't tell"
- Full-bleed imagery used as section backgrounds

### 4. Typewriter + Extended Sans Contrast
- The pairing of `courier-std` (body) + `pragmatica-extended` (headings) creates:
  - Authentic / handcrafted feel (Courier)
  - Power / authority feel (Extended bold sans)
- This is the most distinctive design decision

### 5. Earned Minimalism
- No decorative elements, no icons, no gradients
- No drop shadows, no border-radius on most elements
- Borders are sharp/square
- The "decoration" IS the typography

### 6. Cultural Positioning Through Copy
- Brand manifesto is a full-page section
- Language is aspirational, street-authentic, motivational
- Copy has personality — not corporate-speak

### 7. Structural Rhythm
- Alternating section backgrounds (light/dark) create page rhythm
- Each section has ONE primary purpose
- No section tries to do too much

---

## Interactive / Motion Patterns
- Video autoplay (muted) in hero
- Video players in content sections (Plyr.js)
- Minimal JavaScript — no heavy animations
- Hover states: subtle underlines on nav
- Scroll-based reveals (Squarespace native)

---

## Logo / Brand Mark
- Custom logotype: "RSPKT" in a custom extended bold typeface
- The "R" has a modified/distressed character
- Monochromatic — black on light, white on dark
- No icon/symbol — wordmark only

---

## Section Anatomy (Page Structure)
1. Fixed Nav (transparent → opaque on scroll)
2. Full-viewport hero (video/image)
3. Tagline text section (cream bg)
4. Social proof / client logos section
5. Work portfolio (video grid, 3-col)
6. CTA band (dark bg)
7. Services section (3-col grid, cream bg)
8. Brand manifesto (full-bleed black)
9. Footer (dark charcoal, email subscribe)

---

## Key Differentiators vs. Generic Web Design
1. **Courier Std as body font** — almost no one uses monospace for body copy
2. **No hero text overlay** — the hero is pure media
3. **Manifesto as a full page section** — brand values given equal weight to services
4. **Negative letter-spacing on headings** — creates condensed, editorial feel
5. **3-font hierarchy with distinct personalities** — not just size variation
6. **Section background alternation** — creates rhythm without color
7. **Video as primary portfolio medium** — not static screenshots
