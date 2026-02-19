# World Enterprise Group — Site Standards

This is a static GitHub Pages website. You are responsible for making it look exceptional.

## Before You Start: Get Business Context

**Every site belongs to a real business.** Before making ANY changes, fetch the business profile from the ORBITAL registry.

**Repository:** `Om-Labs/registry` → `orbital/` directory on the `main` branch.

```bash
# Fetch business entities (company names, descriptions, NAICS/SIC codes)
gh api repos/Om-Labs/registry/contents/orbital/worlds.yaml --jq '.content' | base64 -d

# Fetch website plans (planned nav structure, priority rankings)
gh api repos/Om-Labs/registry/contents/orbital/websites.yaml --jq '.content' | base64 -d
```

**`Om-Labs/registry/orbital/worlds.yaml`** — 75 business entities:
- Company name, type (LLC, Corp, etc.), location
- Business category and description (what the company actually does)
- NAICS/SIC/PSC industry codes

**`Om-Labs/registry/orbital/websites.yaml`** — planned website structure:
- Company name and URL
- Planned navigation structure (`nav` field)
- Priority ranking

### Step 1: Match the business

Find the entry matching this repo's name or domain. Read the `description` field — it is the **source of truth** for what the business does. Do not invent or contradict it.

### Step 2: Align brand to industry codes

If NAICS/SIC codes are provided, the site's visual brand, tone, and content MUST reflect those industries:
- **Consulting (NAICS 5416xx)** — clean, authoritative, premium feel (think McKinsey, Deloitte)
- **Education (NAICS 6116xx)** — warm, inviting, structured curriculum layout
- **Technology (NAICS 5415xx)** — modern, innovative, technical credibility
- **Healthcare (NAICS 621xxx)** — trustworthy, calming, HIPAA-aware language
- **Fitness/Wellness (NAICS 7139xx)** — energetic, aspirational, action-oriented
- **Legal (NAICS 5411xx)** — professional, conservative, trust-building
- **Agriculture (NAICS 01xxxx)** — earthy, organic, sustainability-focused
- **Finance (NAICS 5242xx)** — secure, precise, data-driven

Use the NAICS/SIC codes to research what visual standards and UX patterns are expected in that industry. The brand should feel native to the industry, not generic.

### Step 3: Align navigation

If `websites.yaml` has a `nav` field for this site, the site's navigation MUST match it. Compare the current nav against the planned nav and update it. When updating navigation, update ALL `.html` files in the repo for consistency.

### Step 4: GAP Analysis

Before making changes, perform a GAP analysis — compare the current state of the site against what it should be:

1. **Content gaps** — Is the site content aligned with the business description? Are there placeholder pages, missing sections, or content that contradicts the ORBITAL entry?
2. **Navigation gaps** — Does the current nav match `websites.yaml`? Are there missing or extra pages?
3. **Brand gaps** — Does the visual design match the industry and company positioning? Colors, typography, imagery appropriate?
4. **Technical gaps** — Outdated frameworks? Missing accessibility? Poor performance? Non-AVIF images?
5. **SEO gaps** — Missing meta tags, structured data, canonical URLs, sitemap?

Document the gaps you find, then prioritize: content accuracy > accessibility > SEO > performance > visual polish.

### Step 5: SEO Audit

Check and fix these SEO fundamentals for every page:

- [ ] Unique, descriptive `<title>` tag (under 60 chars, includes company name)
- [ ] `<meta name="description">` (under 160 chars, matches page content)
- [ ] One `<h1>` per page matching the page's primary topic
- [ ] Proper heading hierarchy (`h1` > `h2` > `h3`, no skipped levels)
- [ ] `<link rel="canonical">` pointing to the correct URL
- [ ] Open Graph tags (`og:title`, `og:description`, `og:image`, `og:type`)
- [ ] JSON-LD structured data (Organization, LocalBusiness, or appropriate schema)
- [ ] All images have meaningful `alt` text (descriptive, not "image" or "photo")
- [ ] Internal links use descriptive anchor text (not "click here")
- [ ] No broken links (404s)
- [ ] `robots.txt` exists and doesn't block important pages
- [ ] `sitemap.xml` exists and lists all pages

For the JSON-LD, use data from `worlds.yaml` — company name, description, category map to Schema.org types:
- Consulting/Professional → `ProfessionalService`
- Education → `EducationalOrganization`
- Restaurant/Food → `Restaurant` or `FoodService`
- Legal → `LegalService`
- Healthcare → `MedicalOrganization`
- General → `Organization`

Example: `taomgt.com` → TAO MGT LTD → Consulting firm positioned like BCG/McKinsey → site should reflect premium business consulting with `ProfessionalService` schema.

## Skills

Use these skills when working on any site:

- **`/frontend-design`** — For all HTML, CSS, and JS work. Creates distinctive, production-grade interfaces.
- **`/comfyui`** — For generating images. Produces photorealistic images in ~6 seconds via the Z-Image Turbo 6B model.

## ComfyUI Image Generation

The ComfyUI API is available at `https://api.studio.hardmagic.com` running the **Z-Image Turbo 6B** model (4 steps, ~6s/image). Default output format is AVIF.

**Use the `/comfyui` skill** to generate images:
```
/comfyui a professional hero image of a modern office space --profile hero-home --seed 42
```

Available profiles: `hero-home` (16:9, 1024x576), `card-4x3` (4:3, 1024x768), `social-square` (1:1, 1024x1024).

After generating, commit the `.avif` file directly into the repo's image directory.

## Image Standards

### Format: AVIF only

All images MUST be `.avif`. No PNG, no JPG, no unoptimized formats.

**Convert all existing images to AVIF.** When working on any site, convert every existing JPG/PNG to AVIF, update all HTML/CSS references, and delete the old files. Use Pillow to batch-convert:

```python
from PIL import Image
import pillow_avif
img = Image.open("old-image.jpg")
img.save("old-image.avif", quality=85)
```

### Size: optimize for exact largest display size

**Images must be generated and saved at the exact largest size they will ever display, not larger.** Serving oversized images wastes bandwidth.

Before generating or adding any image, determine its maximum CSS display size:
1. Check the layout — what is the widest this image will ever render on any breakpoint?
2. Generate at that size (or the nearest supported size), not at an arbitrary large resolution
3. For retina/HiDPI: generate at 2x the CSS display size (e.g., a 600px-wide card image should be generated at 1200px wide)

| Use Case | Max CSS Display | Generate at (2x) | Aspect |
|----------|----------------|-------------------|--------|
| Full-width hero | 1600x900 | 1024x576 (model max) | 16:9 |
| Card / thumbnail | 600x450 | 1024x768 | 4:3 |
| Square (avatar, social) | 400x400 | 1024x1024 | 1:1 |
| Portrait | 400x700 | 768x1344 | ~9:16 |
| Small icon/logo | exact size | exact size | varies |

### Responsive images

For images that display at different sizes across breakpoints, use `srcset` with multiple sizes:

```html
<img src="assets/images/hero-1024w.avif"
     srcset="assets/images/hero-480w.avif 480w,
             assets/images/hero-768w.avif 768w,
             assets/images/hero-1024w.avif 1024w"
     sizes="(max-width: 480px) 100vw,
            (max-width: 768px) 100vw,
            1024px"
     alt="Descriptive alt text"
     width="1024" height="576"
     loading="lazy" decoding="async">
```

For hero images that need multiple breakpoints, generate the image once at the largest size and resize down using Pillow for smaller variants.

### Lazy loading

- `loading="lazy"` on every `<img>` that is NOT in the initial viewport (below the fold)
- `decoding="async"` on ALL images
- `fetchpriority="high"` on the hero/LCP image (do NOT also add `loading="lazy"` to it)
- Always include `width` and `height` attributes to prevent layout shift (CLS)
- Preload the hero image: `<link rel="preload" as="image" href="hero.avif" type="image/avif">`

## CSS & JavaScript — Always Upgrade

These sites use old templates (2016-2019 era). **Always upgrade frameworks and modernize code, even for small changes.** Every touch is an opportunity to improve.

### Framework upgrades (mandatory)

Every time you work on a site, upgrade its frameworks:

| If you find... | Upgrade to... |
|----------------|---------------|
| Bootstrap 3.x | Bootstrap 5.3 (latest) via CDN |
| Bootstrap 4.x | Bootstrap 5.3 (latest) via CDN |
| jQuery 1.x / 2.x | Remove if only used for Bootstrap; keep jQuery 3.x slim if needed |
| Font Awesome 4.x | Font Awesome 6 via CDN |
| Old Google Fonts `<link>` | `<link rel="preconnect">` + `display=swap` |

If the site uses Tailwind, use the latest Tailwind via CDN Play. If it uses Material Design, use the latest Material Web Components. **Match and upgrade what's already there — don't switch frameworks.**

When upgrading Bootstrap 3→5, fix the breaking changes: `col-xs-*` → `col-*`, `panel` → `card`, `btn-default` → `btn-outline-secondary`, `pull-right` → `float-end`, jQuery plugins → Bootstrap 5 vanilla JS, etc.

### Modern CSS (2026)

Use these native CSS features — they are fully supported in all browsers and replace old JS hacks:

- **Container queries** (`@container`) — make components responsive to their parent, not the viewport. Use instead of viewport media queries when styling cards, sidebars, widgets.
- **CSS nesting** — nest selectors natively (no SASS needed): `.card { &:hover { transform: scale(1.02); } }`
- **`:has()` selector** — style parents based on children: `.card:has(img) { padding: 0; }`
- **`aspect-ratio`** — replace padding-bottom hacks: `aspect-ratio: 16/9;`
- **`content-visibility: auto`** — on long pages, add this to below-fold sections for massive render performance gains
- **`color-mix()` and `oklch()`** — modern color manipulation: `color-mix(in oklch, var(--primary) 80%, white)`
- **Scroll-driven animations** (`animation-timeline: scroll()`) — replace WOW.js, AOS.js, and other scroll animation libraries with pure CSS
- **View Transitions** (`@view-transition`) — smooth page transitions for multi-page sites without JS
- **`@layer`** — cascade layers for clean specificity management when mixing template CSS with custom styles
- **Popover API** (`popover` attribute) — native popovers/tooltips without JS libraries
- **`<dialog>` element** — native modals, replace jQuery modal plugins
- **`accent-color`** — style checkboxes, radios, range inputs: `accent-color: var(--primary);`

### When CSS/JS is weak or minimal

If a site has thin CSS (just a template with minimal customization), improve it:

- Add smooth transitions and hover effects to interactive elements
- Use `scroll-behavior: smooth` and `scroll-margin-top` for anchor links
- Replace floats with flexbox/grid, margin hacks with `gap`
- Add `prefers-reduced-motion` media query to disable animations for users who request it
- Add `prefers-color-scheme` dark mode support if the design allows it
- Use CSS custom properties for the site's color palette, extracted from the existing theme
- Use native CSS nesting to keep styles organized and readable

### Script optimization

- Add `defer` to all `<script>` tags
- Remove unused JS plugins (check if carousels, scrollers, etc. are actually used)
- Remove dead code: commented-out PHP forms, expired countdown timers, broken integrations
- Replace jQuery UI interactions with CSS-only equivalents where possible
- Replace JS scroll animations (WOW.js, AOS) with CSS `animation-timeline: scroll()`
- Replace JS modals with native `<dialog>` element
- Replace JS tooltips/popovers with native `popover` attribute

## HTML Standards

### Structure

- These are static HTML sites — NO build tools, NO npm, NO bundlers, NO package.json
- Preserve the existing directory structure and naming conventions
- Use semantic HTML: `<header>`, `<main>`, `<footer>`, `<section>`, `<nav>`, `<article>`
- One `<h1>` per page, proper heading hierarchy (`h1` > `h2` > `h3`)
- Every `<img>` must have a meaningful `alt` attribute (never empty, never "image", never "photo")

### Navigation — must match ORBITAL

Navigation MUST match the `nav` field from `Om-Labs/registry/orbital/websites.yaml`. If the current site nav differs from the planned nav, update it.

When updating navigation:
- Fetch `websites.yaml`: `gh api repos/Om-Labs/registry/contents/orbital/websites.yaml --jq '.content' | base64 -d`
- Compare current nav against the `nav` field for this company
- Add missing pages, remove pages not in the plan, reorder to match
- Update ALL `.html` files in the repo — nav is copy-pasted across every file
- Use grep/glob to find every file with the nav markup and verify consistency
- Add `aria-current="page"` to the active nav link on each page

### Instant navigation

For multi-page sites, add the Speculation Rules API in `<head>` for instant page loads:

```html
<script type="speculationrules">
{
  "prerender": [{ "where": { "href_matches": "/*" }, "eagerness": "moderate" }]
}
</script>
```

This prerenders pages when the user hovers over links, making navigation feel instant. Browsers that don't support it simply ignore the tag.

### SEO & Social

Every page MUST have these meta tags (populated from ORBITAL `worlds.yaml` data):

```html
<title>Page Title — Company Name</title>
<meta name="description" content="Concise page description under 160 chars">
<meta property="og:title" content="Page Title — Company Name">
<meta property="og:description" content="Same as meta description">
<meta property="og:image" content="https://domain.com/assets/images/og-image.avif">
<meta property="og:type" content="website">
<meta property="og:url" content="https://domain.com/page">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="https://domain.com/page">
```

Add JSON-LD structured data using the appropriate Schema.org type for the business. Pull the company name, description, and NAICS from `Om-Labs/registry/orbital/worlds.yaml`:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ProfessionalService",
  "name": "Company Name from worlds.yaml",
  "url": "https://domain.com",
  "logo": "https://domain.com/assets/images/logo.avif",
  "description": "Description from worlds.yaml",
  "address": { "@type": "PostalAddress", "addressLocality": "Location from worlds.yaml" },
  "naics": "NAICS code from worlds.yaml"
}
</script>
```

Use the correct `@type`: `ProfessionalService`, `EducationalOrganization`, `Restaurant`, `LegalService`, `MedicalOrganization`, `SportsActivityLocation`, or `Organization` (see GAP analysis step for mapping).

Every site should also have:
- `robots.txt` allowing crawling of all public pages
- `sitemap.xml` listing all HTML pages with `<lastmod>` dates

### Accessibility — WCAG 2.2 AA & Section 508

All sites MUST meet **WCAG 2.2 Level AA** and **Section 508** compliance. This is not optional.

**Perceivable:**
- Color contrast: 4.5:1 minimum for body text, 3:1 for large text (18px+ or 14px+ bold)
- Non-text contrast: 3:1 for UI components and graphical objects (borders, icons, focus indicators)
- All images have meaningful `alt` text. Decorative images use `alt=""`
- Video/audio has captions or transcripts (if applicable)
- Content is readable and functional at 200% zoom without horizontal scrolling
- No information conveyed by color alone — use icons, text, or patterns alongside color

**Operable:**
- All interactive elements keyboard-accessible (Tab, Enter, Space, Escape, Arrow keys)
- Visible focus indicator on all focusable elements (minimum 2px outline, 3:1 contrast)
- Skip-to-content link as the first focusable element: `<a href="#main" class="skip-link">Skip to content</a>`
- No keyboard traps — users can always Tab away from any element
- Focus order follows visual/logical reading order
- Touch targets: minimum 24x24px (WCAG 2.2 new requirement)
- No content that flashes more than 3 times per second

**Understandable:**
- Page language declared: `<html lang="en">`
- Form inputs have associated `<label>` elements (use `for`/`id`, not just placeholder text)
- Error messages are descriptive and associated with the input via `aria-describedby`
- Consistent navigation across all pages
- No unexpected context changes on focus or input

**Robust:**
- Valid HTML (no duplicate IDs, proper nesting, closed tags)
- ARIA used correctly: `aria-label` on icon-only buttons, `aria-expanded` on toggles, `aria-current="page"` on active nav
- Landmark roles: `<header>`, `<nav>`, `<main>`, `<footer>`, `<aside>` (semantic HTML preferred over ARIA roles)
- Status messages use `aria-live="polite"` or `role="status"`

**Section 508 specific:**
- All the above WCAG 2.2 AA requirements (508 references WCAG 2.0 AA, but we exceed with 2.2)
- No CAPTCHA without accessible alternative
- Timed content has controls to pause, stop, or extend

**CSS for accessibility:**
```css
/* Skip link */
.skip-link { position: absolute; left: -9999px; top: auto; }
.skip-link:focus { left: 1rem; top: 1rem; z-index: 9999; background: var(--primary); color: white; padding: 0.5rem 1rem; }

/* Visible focus */
:focus-visible { outline: 3px solid var(--primary); outline-offset: 2px; }

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; scroll-behavior: auto !important; }
}

/* Minimum touch target */
button, a, input, select, textarea { min-height: 24px; min-width: 24px; }
```

## Fonts & Favicon

### Font loading

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

Always use `display=swap` and `preconnect`. Prefer variable fonts (single file, all weights). If the site uses a Google Font, keep it — just modernize the loading pattern.

### Favicon

Use an SVG favicon with dark mode support:
```html
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
```

SVG favicons can adapt to dark mode via `prefers-color-scheme` inside the SVG.

## Performance Targets

Aim for these Core Web Vitals on every page:
- **LCP** (Largest Contentful Paint): under 2.5 seconds
- **CLS** (Cumulative Layout Shift): under 0.1
- **INP** (Interaction to Next Paint): under 200ms

Key levers: preload hero image, set `width`/`height` on all images, `defer` scripts, `content-visibility: auto` on below-fold sections, remove unused CSS/JS.

## Git Workflow

Push directly to `gh-pages`. No branches, no PRs. Changes go live immediately.

```bash
git add -A && git commit -m "description of changes" && git push origin gh-pages
```

## Deployment

- **Hosting**: GitHub Pages (static files only — no server-side code)
- **Deploy trigger**: Push to `gh-pages` branch
- **Custom domains**: Configured via `CNAME` file — **NEVER delete or modify it**

## What NOT To Do

- NEVER delete the `CNAME` file
- NEVER add build tools, bundlers, or package managers
- NEVER add React, Vue, Angular, or any SPA framework to these sites
- NEVER commit node_modules or dependency directories
- NEVER use placeholder text (Lorem ipsum) — always write real content
- NEVER leave dead code (commented-out sections, unused CSS/JS, broken PHP forms)
- NEVER reference external images by URL — commit all images to the repo
- NEVER serve oversized images — match the image file size to its display size
- NEVER use PHP, Python, or server-side code (GitHub Pages is static only)
- NEVER leave old JPG/PNG images — convert everything to AVIF
- NEVER leave outdated frameworks — always upgrade to latest
