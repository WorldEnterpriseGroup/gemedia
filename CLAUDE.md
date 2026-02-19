# World Enterprise Group — Site Standards

This is a static GitHub Pages website. You are responsible for making it look exceptional.

## Skills

Use these skills when working on any site:

- **`/frontend-design`** — For all HTML, CSS, and JS work. Creates distinctive, production-grade interfaces.
- **`/comfyui`** — For generating images. Produces photorealistic images in ~6 seconds via the Z-Image Turbo 6B model.

## ComfyUI Image Generation

The ComfyUI API is available at `https://api.studio.hardmagic.com`. You can use either the `/comfyui` skill or call the API directly.

**Using the skill:**
```
/comfyui a professional hero image of a modern office space --profile hero-home --seed 42
```

**Using the API directly:**
```bash
# Step 1: Build the workflow payload
python3 scripts/skills/comfyui/workflow_builder.py \
  --template scripts/skills/comfyui/templates/text-to-image-zimage-turbo.api.json \
  --prompt "a professional hero image of a modern office space" \
  --width 1024 --height 576 --seed 42 \
  --output /tmp/comfyui-payload.json

# Step 2: Submit to API and download
python3 scripts/skills/comfyui/comfyui_client.py \
  --url https://api.studio.hardmagic.com \
  --payload /tmp/comfyui-payload.json \
  --output-dir ./assets/images \
  --format avif --timeout 120
```

**Model**: Z-Image Turbo 6B (4 steps, ~6s/image on RTX 3090). Default output format is AVIF.

After generating, commit the `.avif` file directly into the repo's image directory.

## Image Standards

### Format: AVIF only

All images MUST be `.avif`. No PNG, no JPG, no unoptimized formats.

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

## CSS & JavaScript — Upgrade Aggressively

These sites use old templates (2016-2019 era). **Your job is to modernize them to 2026 standards.**

### Framework upgrades

When you encounter outdated frameworks, upgrade them:

| If you find... | Upgrade to... |
|----------------|---------------|
| Bootstrap 3.x | Bootstrap 5.3 (latest) via CDN |
| Bootstrap 4.x | Bootstrap 5.3 (latest) via CDN |
| jQuery 1.x / 2.x | Remove if only used for Bootstrap; keep jQuery 3.x slim if needed |
| Font Awesome 4.x | Font Awesome 6 via CDN |
| Old Google Fonts `<link>` | `<link rel="preconnect">` + `display=swap` |

If the site uses Tailwind, use the latest Tailwind via CDN Play. If it uses Material Design, use the latest Material Web Components. **Match and upgrade what's already there — don't switch frameworks.**

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

### Navigation consistency

Navigation is copy-pasted across every HTML file. When updating navigation:
- Update ALL `.html` files in the repo
- Use grep/glob to find every file with the nav markup
- Verify consistency across all pages

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

### SEO & social

Every page should have:
```html
<meta name="description" content="Concise page description under 160 chars">
<meta property="og:title" content="Page Title">
<meta property="og:description" content="Same as meta description">
<meta property="og:image" content="https://domain.com/assets/images/og-image.avif">
<meta property="og:type" content="website">
<link rel="canonical" href="https://domain.com/page">
```

Add JSON-LD structured data for rich search results:
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Company Name",
  "url": "https://domain.com",
  "logo": "https://domain.com/assets/images/logo.avif",
  "description": "What this company does"
}
</script>
```

### Accessibility

- All interactive elements must be keyboard-accessible
- Color contrast ratio of at least 4.5:1 for body text, 3:1 for large text
- Form inputs must have associated `<label>` elements
- Skip-to-content link for keyboard users
- `aria-label` on icon-only buttons and links

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

## Deployment

- **Hosting**: GitHub Pages (static files only — no server-side code)
- **Deploy trigger**: Push to the default branch
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
