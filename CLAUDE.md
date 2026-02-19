# World Enterprise Group — Site Standards

This is a static GitHub Pages website. All changes deploy automatically when pushed to the default branch.

## Deployment

- **Hosting**: GitHub Pages (static files only — no server-side code)
- **Deploy trigger**: Push to default branch (`main`, `master`, or `gh-pages`)
- **Custom domains**: Configured via `CNAME` file — never delete or modify it

## Image Standards

### Format: AVIF (mandatory)

All images MUST be saved as `.avif`. Use the `<picture>` element with fallback for maximum compatibility:

```html
<picture>
  <source srcset="assets/images/hero.avif" type="image/avif">
  <img src="assets/images/hero.avif" alt="Descriptive alt text"
       width="1024" height="768" loading="lazy" decoding="async">
</picture>
```

For hero/above-the-fold images, do NOT use `loading="lazy"` — instead use `fetchpriority="high"`:

```html
<img src="assets/images/hero.avif" alt="Hero description"
     width="1600" height="900" fetchpriority="high" decoding="async">
```

### Lazy loading (mandatory for below-fold images)

- Add `loading="lazy"` to every `<img>` that is NOT in the initial viewport
- Add `decoding="async"` to all images
- Always include `width` and `height` attributes to prevent layout shift

### Image generation

Use the `/comfyui` skill to generate images. The default model (Z-Image Turbo) produces photorealistic 1024x1024 images in ~6 seconds. Output format is AVIF by default.

Common dimensions for site images:

| Use Case | Generate Size | Display Size | Aspect |
|----------|--------------|--------------|--------|
| Hero banner | 1024x576 | 1600x900 | 16:9 |
| Card / thumbnail | 1024x768 | 600x450 | 4:3 |
| Square (social, avatar) | 1024x1024 | 400x400 | 1:1 |
| Portrait | 768x1344 | 400x700 | ~9:16 |

After generating, place images in the repo's existing image directory (typically `assets/images/`, `images/`, or `assets/img/`).

## HTML Standards

### Structure

- These are static HTML sites — no build tools, no npm, no bundlers
- Do NOT add package.json, webpack, vite, or any build system
- Keep the existing CSS framework (Bootstrap 3, 4, or 5 — whichever the site uses)
- Preserve the existing directory structure and naming conventions

### Navigation consistency

Many sites have navigation copy-pasted across every HTML file. When updating navigation:
- Update ALL HTML files in the repo, not just one
- Use grep/glob to find every file containing the nav markup
- Verify the update is consistent across all pages

### Semantic HTML

- Use `<header>`, `<main>`, `<footer>`, `<section>`, `<nav>`, `<article>` elements
- Every `<img>` must have a descriptive `alt` attribute (never empty, never "image")
- Use heading hierarchy (`h1` > `h2` > `h3`) — one `h1` per page

### Performance

- Add `defer` to all `<script>` tags (except inline scripts that must run immediately)
- Preload the hero/LCP image: `<link rel="preload" as="image" href="hero.avif" type="image/avif">`
- Do NOT add new JavaScript libraries unless absolutely necessary
- Prefer CSS animations over JavaScript animations

## CSS Standards

- Follow the existing site's class naming convention (BEM, utility, or template-specific like `ct-`)
- Add new styles to the existing custom stylesheet — do NOT create new CSS files
- Use CSS custom properties (`var(--color-primary)`) for colors when the site already uses them
- Mobile-first responsive design: start with mobile styles, add `min-width` media queries for larger screens

## What NOT To Do

- Do NOT delete the `CNAME` file
- Do NOT add build tools, bundlers, or package managers
- Do NOT replace the existing CSS framework with a different one
- Do NOT add React, Vue, Angular, or any SPA framework
- Do NOT commit node_modules or any dependency directories
- Do NOT use placeholder text (Lorem ipsum) — always write real content
- Do NOT leave dead code (commented-out sections, unused CSS/JS)
- Do NOT reference external images by URL — always commit images to the repo
- Do NOT use PHP, Python, or any server-side code (GitHub Pages is static only)
