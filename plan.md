# Website Modernization Plan

> **Audience:** Claude Code agent (autonomous execution)
> **Authority:** All standards, rules, and constraints are defined in `CLAUDE.md` at the repo root. Read it fully before starting.
> **Skill dependencies:** `/frontend-design`, `/comfyui`

---

## Phase 1: Context & Discovery

### 1.1 Read project instructions
- Read `CLAUDE.md` in this repo. It is the binding specification for all work.
- Note the constraints: static HTML only, AVIF images, push to `gh-pages`, never delete `CNAME`.

### 1.2 Fetch ORBITAL business data
- Fetch `Om-Labs/registry/orbital/worlds.yaml` and `Om-Labs/registry/orbital/websites.yaml` via `gh api`.
- Match this repo's name or domain to the business entry in `worlds.yaml`.
- Extract: company name, description, category, NAICS/SIC codes, location.
- Extract planned navigation from `websites.yaml` (`nav` field).
- This data is the source of truth. All content, branding, and structure decisions flow from it.

### 1.3 Audit current site state
- Read every `.html` file in the repo. Understand the current page structure, navigation, content, and styling.
- Identify the CSS/JS framework in use (Bootstrap version, Tailwind, jQuery, etc.).
- Inventory all images: formats, sizes, filenames, where they are referenced.
- Check for `robots.txt`, `sitemap.xml`, JSON-LD structured data.

---

## Phase 2: GAP Analysis

### 2.1 Content gaps
- Compare site content against the ORBITAL `description` field. Flag any content that contradicts or is unrelated to the business purpose.
- Identify placeholder text (Lorem ipsum), empty pages, broken links, dead code (commented-out PHP, expired countdowns).

### 2.2 Navigation gaps
- Compare the current nav against the `nav` field in `websites.yaml`.
- List pages that need to be added, removed, or renamed.
- Verify nav is consistent across all HTML files.

### 2.3 Brand gaps
- Does the visual design match the industry indicated by the NAICS/SIC codes?
- Are colors, typography, and imagery appropriate for the company's positioning?
- Reference the NAICS-to-brand mapping in `CLAUDE.md` Step 2.

### 2.4 Technical gaps
- What framework version is in use? Does it need upgrading per `CLAUDE.md`?
- Are images in AVIF format? Any JPG/PNG that need conversion?
- Are images sized correctly for their display size (not oversized)?
- Is there a skip-to-content link? Are focus indicators visible? WCAG 2.2 AA compliance?

### 2.5 SEO gaps
- Run through the SEO audit checklist in `CLAUDE.md` Step 5.
- Check every page for: `<title>`, `<meta description>`, `<link rel="canonical">`, OG tags, heading hierarchy, alt text.
- Is there JSON-LD structured data with the correct Schema.org `@type` for this business?

### 2.6 Prioritize
Order of priority: **content accuracy > accessibility (WCAG/508) > navigation > SEO > performance > visual polish**.

---

## Phase 3: Framework & Infrastructure

### 3.1 Upgrade CSS/JS frameworks
- Follow the mandatory upgrade table in `CLAUDE.md`: Bootstrap 3/4 → 5.3, jQuery removal, Font Awesome 4 → 6.
- Fix all breaking changes from the upgrade (class renames, removed jQuery plugins, etc.).
- Do NOT switch frameworks — upgrade what is already in use.

### 3.2 Modernize CSS
- Replace old patterns: floats → flexbox/grid, padding-bottom aspect ratio hacks → `aspect-ratio`, JS scroll animations → `animation-timeline: scroll()`.
- Add CSS custom properties for the site's color palette.
- Use native CSS nesting, `:has()`, `@layer`, container queries where beneficial.
- Add `prefers-reduced-motion` and `prefers-color-scheme` media queries.

### 3.3 Optimize scripts
- Add `defer` to all `<script>` tags.
- Remove unused JS plugins, dead code, commented-out blocks.
- Replace JS modals → `<dialog>`, JS tooltips → `popover` attribute.

### 3.4 Add infrastructure files
- `robots.txt` — allow all public pages.
- `sitemap.xml` — list all HTML pages with `<lastmod>`.
- SVG favicon with dark mode support.
- Speculation Rules API in `<head>` for instant navigation.

---

## Phase 4: Accessibility (WCAG 2.2 AA & Section 508)

### 4.1 Perceivable
- Verify color contrast: 4.5:1 body text, 3:1 large text and UI components.
- All images: meaningful `alt` text (decorative images use `alt=""`).
- Content readable at 200% zoom without horizontal scroll.

### 4.2 Operable
- Add skip-to-content link as first focusable element.
- Verify all interactive elements are keyboard-accessible.
- Add visible `:focus-visible` styles (minimum 2px, 3:1 contrast).
- Ensure touch targets are minimum 24x24px.
- Add `aria-current="page"` to active nav link.

### 4.3 Understandable
- Set `<html lang="en">`.
- All form inputs have `<label>` elements.
- Error messages use `aria-describedby`.
- Navigation consistent across all pages.

### 4.4 Robust
- Valid HTML: no duplicate IDs, proper nesting.
- ARIA used correctly: `aria-label`, `aria-expanded`, `aria-live`.
- Semantic landmarks: `<header>`, `<nav>`, `<main>`, `<footer>`.

---

## Phase 5: Content & SEO

### 5.1 Update page content
- Rewrite content to align with the ORBITAL business description.
- Remove placeholder text — write real, specific content.
- Use the company's actual positioning and industry language.

### 5.2 Update navigation
- Match navigation to `websites.yaml` `nav` field.
- Update ALL `.html` files for consistency.
- Add `aria-current="page"` on each page's active nav item.

### 5.3 SEO implementation
- Add unique `<title>` and `<meta description>` to every page.
- Add `<link rel="canonical">` to every page.
- Add Open Graph and Twitter Card meta tags.
- Add JSON-LD structured data using the correct `@type` from `CLAUDE.md` (mapped from NAICS/business category). Populate from `worlds.yaml` data.

### 5.4 Heading structure
- One `<h1>` per page, matching the page's primary topic.
- Proper hierarchy: `h1` > `h2` > `h3`, no skipped levels.
- Headings should be descriptive, not generic.

---

## Phase 6: Images

### 6.1 Convert existing images to AVIF
- Find all JPG/PNG images in the repo.
- Convert each to AVIF using Pillow (`quality=85`).
- Update all HTML/CSS references to point to the new `.avif` files.
- Delete the original JPG/PNG files.

### 6.2 Generate new images where needed
- Use the `/comfyui` skill to generate images.
- Select the appropriate `--profile` for the use case (see `CLAUDE.md` image size table).
- Select a `--style` matching the brand aesthetic (e.g., `editorial` for consulting, `product` for e-commerce).
- Apply a `--filter` if the site has a specific color mood.
- Commit generated `.avif` files directly to the repo.

### 6.3 Optimize image delivery
- Set `width` and `height` attributes on every `<img>` to prevent layout shift.
- Add `loading="lazy"` and `decoding="async"` to below-fold images.
- Add `fetchpriority="high"` to the hero/LCP image (no `loading="lazy"` on it).
- Preload the hero image: `<link rel="preload" as="image" href="hero.avif" type="image/avif">`.
- Use `srcset` for images that display at multiple sizes across breakpoints.

---

## Phase 7: Performance

### 7.1 Core Web Vitals targets
- **LCP** < 2.5s — preload hero image, optimize largest element.
- **CLS** < 0.1 — `width`/`height` on all images, no layout-shifting ads or embeds.
- **INP** < 200ms — `defer` scripts, minimize main thread work.

### 7.2 Loading optimizations
- `<link rel="preconnect">` for Google Fonts and other external origins.
- `content-visibility: auto` on below-fold `<section>` elements.
- Font loading with `display=swap`.
- Remove unused CSS/JS files.

---

## Phase 8: Final Validation

### 8.1 Cross-page consistency
- Navigation identical across all HTML files.
- Footer identical across all HTML files.
- CSS/JS references consistent (same CDN versions, same local files).

### 8.2 Functional checks
- No broken internal links.
- All images load (no 404s).
- Forms work (if any exist — these are static sites, so forms likely use external services).
- CNAME file exists and is untouched.

### 8.3 Compliance checklist
- [ ] Content matches ORBITAL business description
- [ ] Navigation matches `websites.yaml` `nav` field
- [ ] Brand aligns with NAICS/SIC industry codes
- [ ] WCAG 2.2 AA: skip link, focus indicators, contrast, touch targets, alt text, lang, landmarks
- [ ] Section 508 compliance
- [ ] All images are AVIF, sized correctly, have `width`/`height`/`alt`
- [ ] SEO: title, meta description, canonical, OG tags, JSON-LD, sitemap, robots.txt
- [ ] Frameworks upgraded to latest versions
- [ ] No dead code, no placeholder text, no unused files
- [ ] Core Web Vitals within targets

---

## Execution

### Commit and deploy
```bash
git add -A && git commit -m "modernize: [brief description of changes]" && git push origin gh-pages
```

Changes deploy immediately via GitHub Pages. Verify the live site after pushing.

### Rules
- Push directly to `gh-pages`. No branches, no PRs.
- NEVER delete the `CNAME` file.
- NEVER add build tools, npm, bundlers, or SPA frameworks.
- NEVER use placeholder text — write real content from the ORBITAL data.
- NEVER serve oversized images or non-AVIF formats.
- Refer to `CLAUDE.md` for the complete rules and "What NOT To Do" list.
