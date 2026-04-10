# IBM Bob "WOW-First" Demo — Recording Checklist

Use this checklist before and after every demo recording session.

---

## Pre-Recording: Environment Setup

### Application
- [ ] The demo application is running locally on `localhost:3000` (or equivalent).
- [ ] The PostgreSQL database is populated with **realistic sample data** — real-looking names, addresses, dollar amounts, and dates. No "Test User 1" or "$0.00."
- [ ] All features demonstrated in the script have been tested end-to-end at least once.
- [ ] Any loading states or API calls complete within 2 seconds. If not, pre-load the data.

### IBM Project Bob Interface
- [ ] The IBM Project Bob interface is open in the IDE.
- [ ] The Master Prompt is pre-typed and ready to display (do not type it live — show it already written).
- [ ] The Bob output panel is visible and shows the generated artifacts.

### Code View
- [ ] VS Code (or preferred IDE) is open with `schema.sql` visible.
- [ ] `server.js` (or equivalent) is open in a second tab.
- [ ] Font size is increased to 16pt or higher for screen legibility.
- [ ] No unrelated files or tabs are visible.

### Screen and Audio
- [ ] Screen resolution is set to 1920x1080 or higher.
- [ ] Display scaling is set to 100% (not 125% or 150%).
- [ ] All browser notifications are disabled (Do Not Disturb mode is on).
- [ ] All desktop notifications are disabled.
- [ ] Microphone is tested — audio is clear, no background noise.
- [ ] Recording software (OBS, Loom, Camtasia, etc.) is open and tested.
- [ ] A countdown timer is visible to the presenter (not on screen).

### Slides
- [ ] Title slide is prepared: App name + one-line problem description.
- [ ] Final slide is prepared: App name + the Call to Action question.
- [ ] Both slides are open and ready to display.

---

## Recording: Segment Timing Targets

| Segment | Target Start | Target End | Hard Limit |
|---------|-------------|-----------|------------|
| The Hook | 0:00 | 0:30 | 0:35 |
| The WOW | 0:30 | 2:00 | 2:15 |
| The Reveal | 2:00 | 3:30 | 3:45 |
| The Enterprise Proof | 3:30 | 4:30 | 4:45 |
| The Call to Action | 4:30 | 5:00 | 5:15 |

If any segment runs over its hard limit, stop and re-record from that segment. Do not allow the total runtime to exceed 5:15.

---

## Post-Recording: Quality Review

### Timing
- [ ] Total runtime is between 4:45 and 5:15.
- [ ] No single segment exceeds its hard limit.

### Content
- [ ] The Reddit quote (or paraphrase) is audible and legible on screen.
- [ ] The WOW feature is demonstrated without technical errors or hesitation.
- [ ] The Master Prompt is on screen for at least 15 seconds (long enough to be readable).
- [ ] The PostgreSQL schema is visible and the presenter mentions "PostgreSQL" by name.
- [ ] The final Call to Action question is the last thing the viewer hears before the video ends.

### Production
- [ ] Audio is clear throughout with no background noise, pops, or clipping.
- [ ] Screen is sharp and all text is legible at 1080p.
- [ ] No personal information (email addresses, passwords, API keys) is visible on screen.
- [ ] The video ends with 3-5 seconds of the final slide visible before fading out.

---

## Distribution

After the video passes quality review:

- [ ] Export as MP4 at 1080p, H.264, 10-15 Mbps.
- [ ] Upload to the agreed distribution platform (IBM Box, Seismic, Vimeo, etc.).
- [ ] Attach the ODE document (`[app-name]-demo-ode.md`) as a companion resource.
- [ ] Send to the client contact with the subject line: *"[App Name] — Built with IBM Project Bob in [X] minutes"*
- [ ] Log the demo in the CRM with the client name, demo archetype, and send date.
