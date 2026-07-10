# LP Widget — Landing Page for Return Stacking Visualizer

## Project Overview

This is a self-contained, embeddable landing page component that promotes the **Return Stacking Visualizer** and captures leads through a HubSpot form. It explains the concept of return stacking and drives users to launch the interactive tool.

---

## Key Files

| File | Purpose |
|------|---------|
| `lp-embed.html` | **Primary deliverable** — embeddable HTML fragment (no `<html>`/`<body>` tags), designed to paste into existing site templates |
| `lp-preview.html` | Standalone full-page preview for testing and client review |
| `deploy/index.html` | Deployed production version |
| `deploy/Screen recording5.webm` | Demo video asset (WebM, looping) |
| `form embed code.txt` | HubSpot form embed snippet reference |
| `Landing Page content.txt` | Content reference document |

## Two Delivery Models

- **Embeddable fragment** (`lp-embed.html`): Drop-in HTML fragment with `rs-lp-` prefixed classes to prevent CSS conflicts with host sites. CSS custom properties allow theming overrides.
- **Standalone preview** (`lp-preview.html`): Full HTML page for testing. Uses `rs-` class prefix.

---

## Brand Assets

Shared brand assets are at `../../../references/brand-assets/return-stacked/` (see root `CLAUDE.md` for full reference).

**Colors** — uses the standard Return Stacked palette via CSS custom properties:

```css
--rs-navy: #172c3a       /* Cover Dark — hero & proof sections */
--rs-text-primary: #2c3641
--rs-text-secondary: #625c6d
--rs-teal: #14cfa6        /* Buttons, highlights, accents */
--rs-teal-hover: #11b893  /* Derived hover state */
--rs-gray-bg: #f0f1f1     /* Section Gray */
--rs-border: #bfbfbf
```

**Font**: DM Sans loaded from Google Fonts CDN (weights 300–800). Not loaded from local `../../../references/brand-assets/return-stacked/Font_Family/` files.

**Background**: Inline SVG wave pattern (blue, 25% opacity). Could be replaced with `../../../references/brand-assets/return-stacked/Background_images/RS-Background-Blue.svg`.

**Logos**: Not used in this landing page.

---

## Page Structure (5 Sections)

1. **Hero** — Navy background, animated SVG, headline with teal highlight, CTA button
2. **Features** — Light gray background, demo video, 3 feature cards in a grid
3. **Social Proof** — Navy background, teal accent bar, testimonial quote
4. **Final CTA** — White background, headline, video, HubSpot form
5. **HubSpot Form** — Portal 46343589, Form 48364b2b-12c7-4df4-87a8-bca02fc09b54

---

## Implementation Notes

- **Video path**: In `lp-embed.html`, the `<source src>` is a placeholder (`YOUR_VIDEO_PATH_HERE.webm`). Must be updated to the actual hosted URL before embedding.
- **HubSpot script**: If the host site already loads `embed/v2.js`, remove the first `<script>` tag and keep only the `hbspt.forms.create()` call.
- **CSS scoping**: The `rs-lp-` class prefix prevents conflicts. Host site styles should not leak in.
- **Responsive breakpoints**: 900px (2-col grid), 640px (single-col mobile).

## Build / Deploy

No build process. Pure HTML/CSS — edit directly and serve. The `deploy/` folder contains the production-ready version with the video file co-located.
