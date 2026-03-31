---
name: cultural-website-rebuilder
description: Rebuild or redesign an existing website with an authentic cultural theme rooted in a specific heritage, tradition, or geographic identity. Produces a visually immersive, hand-crafted result by combining AI-generated cultural imagery, culturally-specific typography, a thematically coherent color palette, and section content that reflects genuine cultural knowledge. Use when a user asks to redesign, rebuild, or retheme a website with cultural authenticity — e.g., Cuban dance school, West African textile brand, Japanese tea ceremony studio, Mexican folk art gallery, or any culturally-rooted organization.
---

# Cultural Website Rebuilder

Rebuild a website so it feels like it was made *inside* the culture it represents — not a tourist-brochure approximation of it.

## Workflow Overview

1. **Analyze** the existing site (screenshot, URL, or description)
2. **Define** the cultural identity and design philosophy
3. **Generate** 4–5 custom cultural images with AI
4. **Build** the site section by section
5. **Polish** with motion, marquee, and micro-details
6. **Checkpoint** and deliver

---

## Step 1 — Analyze the Existing Site

Extract from the source material:
- Organization name, tagline, founding year
- Core offerings (classes, events, products, services)
- Key people (founders, instructors, team)
- Contact details, location, social links
- Existing sections and navigation structure

If a URL is available, browse it. If only a screenshot, extract all visible text and structure.

---

## Step 2 — Define the Cultural Identity

Before writing a single line of code, commit to a **specific cultural design philosophy**. Avoid generic "ethnic" aesthetics. Research the actual visual culture:

| Culture | Authentic Visual References |
|---|---|
| Afro-Cuban | Havana street murals, Santería color symbolism, vintage Son album art |
| West African | Kente cloth geometry, Adinkra symbols, indigo-dyed textile patterns |
| Japanese | Wabi-sabi imperfection, sumi-e ink brushwork, Edo woodblock composition |
| Mexican Folk | Oaxacan alebrijes, Talavera tile patterns, papel picado geometry |
| Indian Classical | Mughal miniature borders, rangoli symmetry, temple gopuram layering |

**Write an `ideas.md`** with three distinct design directions (each `<0.10` probability), then commit to one. Document:

- **Design Movement**: Name a specific aesthetic (e.g., "Contemporary Afro-Cuban Muralism")
- **Color Philosophy**: 4–5 OKLCH values with cultural reasoning (e.g., coral = Santería Changó, cobalt = Caribbean sea)
- **Typography System**: One display font (bold, condensed, or calligraphic) + one body font. Avoid Inter as the sole font.
- **Layout Paradigm**: Asymmetric, masonry, or diagonal — not centered-grid-only
- **Signature Elements**: 2–3 recurring motifs (e.g., tile pattern as section divider, dance silhouette as icon)
- **Interaction Philosophy**: How hover states and animations reflect cultural energy

---

## Step 3 — Generate Cultural Images

Generate **4–5 images** before writing any component code. Use highly specific prompts referencing the actual art style.

### Image Roles (generate all at once to save time)

| Slot | Purpose | Placement |
|---|---|---|
| Hero | Full-bleed scene, people + architecture | Hero section background |
| Activity | Core offering in action (dance, craft, ceremony) | Featured event or about section |
| Community | Group scene, celebration, or ritual | Events or about section |
| Pattern/Texture | Repeating decorative motif | Section dividers, card backgrounds |
| Cityscape/Place | Local geography fused with cultural elements | Banner or footer illustration |

### Prompt Formula

```
[Art style] illustration of [scene]. [Color palette]. [Specific cultural details].
[Mood/lighting]. [Composition notes]. No text overlays.
```

**Example (Afro-Cuban):**
> "Vibrant Afro-Cuban street mural style illustration of a couple dancing Casino Salsa on a Havana street. Electric coral, cobalt blue, saffron yellow. Colorful colonial buildings, palm trees, tropical flowers. Warm golden hour light. Bold outlines, flat color fills with texture. No text overlays."

Use the returned CDN URLs directly in component code — never copy images into the project directory.

---

## Step 4 — Build the Site

### CSS & Typography Setup

In `client/src/index.css`, define OKLCH color variables for the cultural palette:

```css
/* Example: Afro-Cuban palette */
--color-primary: oklch(0.65 0.22 28);    /* Electric coral */
--color-secondary: oklch(0.42 0.22 258); /* Cobalt blue */
--color-accent: oklch(0.78 0.18 68);     /* Saffron gold */
--color-dark: oklch(0.22 0.04 55);       /* Warm black */
--color-light: oklch(0.97 0.02 80);      /* Warm cream */
```

Add Google Fonts in `client/index.html`. Recommended pairings by culture:

| Culture | Display Font | Body Font | Accent Font |
|---|---|---|---|
| Latin/Caribbean | Bebas Neue | Source Sans 3 | Dancing Script |
| West African | Playfair Display | Lato | — |
| Japanese | Noto Serif JP | Noto Sans JP | — |
| Mexican Folk | Lobster Two | Nunito | — |
| South Asian | Yatra One | Hind | — |

Define `.font-display`, `.font-accent`, and `.card-lift` utilities in the `@layer components` block.

### Standard Section Architecture

Build these sections in order. Alternate dark (`oklch(0.22 0.04 55)`) and light (`oklch(0.97 0.02 80)`) backgrounds to create visual rhythm:

1. **Navbar** — Top bar with contact info strip, logo, nav links, CTA button. Sticky on scroll with background transition.
2. **Hero** — Full-bleed generated image, diagonal `clip-path` bottom edge, animated headline (staggered `translateY` entrance), two CTAs.
3. **Cultural Marquee** — Scrolling ticker of culturally-specific terms (dance styles, ingredients, techniques, place names). Use CSS `@keyframes marquee` animation. Background: primary color.
4. **Featured Activity/Events** — Dark background. One large featured card (image + details) + 2–3 secondary cards.
5. **About/History** — Light background with pattern texture overlay (`opacity: 0.03–0.05`). Mission quote block, founding story, stats row, activity illustration.
6. **Offerings/Classes/Products** — Dark background. Grid of offering cards with level/category badges, schedule/price details, CTA banner.
7. **Team** — Light background. Tabbed view (e.g., Instructors / Performance Team). Portrait cards with role, styles, bio, tenure badge.
8. **Media/Videos** — Dark background. Thumbnail grid with play overlay, platform channel CTA banner.
9. **Contact** — Dark background. Info cards (address, phone, email, social) + contact form with toast confirmation.
10. **Footer** — Deepest dark. Pattern strip divider, brand column, nav columns, social icons, copyright.

### Key Implementation Details

**Hero clip-path** — Use diagonal bottom to create visual flow into the next section:
```css
clip-path: polygon(0 0, 100% 0, 100% 96%, 0 100%);
margin-bottom: -2rem;
padding-bottom: 3rem;
```
Add `margin-top: -5rem; padding-top: 8rem` to the following section to close the gap.

**Text on image backgrounds** — Always add `textShadow` for legibility:
```jsx
style={{ textShadow: "0 2px 20px rgba(0,0,0,0.8), 0 4px 40px rgba(0,0,0,0.6)" }}
```

**Pattern texture overlay** — Use the generated pattern image at low opacity as a repeating background:
```jsx
<div className="absolute inset-0 opacity-[0.04] bg-repeat"
  style={{ backgroundImage: `url(${PATTERN_IMG})`, backgroundSize: "300px 300px" }} />
```

**Card lift hover** — Define in CSS, apply as className:
```css
.card-lift { transition: transform 0.25s ease, box-shadow 0.25s ease; }
.card-lift:hover { transform: translateY(-4px) scale(1.01);
  box-shadow: 0 16px 40px -8px oklch(0.65 0.22 28 / 0.25); }
```

**Scroll reveal** — Use `IntersectionObserver` in a `useScrollReveal` hook on the Home page. Add `.scroll-reveal` class to section wrappers.

---

## Step 5 — Polish Details

- **Section eyebrow labels**: Every section header should have a small italic/script-font label in the cultural language (e.g., Spanish, Yoruba, Japanese) above the main heading.
- **Decorative badges**: Float a small badge over key images (e.g., "RUEDA / de Casino", "EST. 1999").
- **Stat counters**: 3-column row of large display-font numbers (years, students, locations).
- **Mission quote block**: Primary-color background card with large italic quote and attribution.
- **Tag pills**: Color-coded category badges on cards (Beginner = green, Featured = coral, Social = blue).

---

## Step 6 — Pre-Checkpoint Checklist

Before saving the checkpoint:
- [ ] All image `src` values use CDN URLs (no local paths)
- [ ] No images copied into the project directory
- [ ] Text is legible on all image backgrounds (check dark/light contrast)
- [ ] Marquee animation runs smoothly
- [ ] Contact form shows toast on submit
- [ ] All nav links scroll to correct section IDs
- [ ] TypeScript reports no errors

---

## Anti-Patterns to Avoid

- **Tourist-brochure aesthetics**: Generic stock photos of "ethnic" people, clip-art flags, or stereotyped imagery. Use AI-generated illustrations in the specific art style instead.
- **Centered-grid-only layout**: Every section should have some asymmetric element — offset images, diagonal dividers, or split columns.
- **Purple gradients + Inter font**: The default "AI slop" look. Always choose a culturally-specific font pairing.
- **Uniform rounded corners everywhere**: Mix sharp, slightly-rounded, and fully-rounded elements based on the cultural aesthetic.
- **Same image reused in multiple sections**: Each of the 4–5 generated images should appear in exactly one prominent location.
