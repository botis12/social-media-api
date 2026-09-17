# APEX PERFORMANCE — personal trainer website

**Γλώσσα: Ελληνικά** (`<html lang="el">`, `og:locale: el_GR`).

Static, dependency-free site for an athletic-performance coaching business.
Plain HTML, CSS and vanilla JS — no build step, no framework, no npm install.
Drop the folder on any host and it works.

```
website/
├── index.html         Home
├── about.html         Bio, credentials, philosophy
├── services.html      4 programs + pricing
├── results.html       Stats, before/after slider, testimonials
├── faq.html           8-question accordion (+ FAQ schema)
├── contact.html       Contact details + booking link (no duplicate form)
├── apply.html         The client form — one short page, 10 fields
├── privacy.html       Template policy (NOT legal advice)
├── terms.html         Template terms (NOT legal advice)
├── 404.html
├── css/styles.css     All styling. Tokens at the very top.
├── js/main.js         All behaviour. One file, commented per feature.
├── images/            SVG placeholders + generated OG image
├── robots.txt · sitemap.xml · site.webmanifest
└── netlify.toml · vercel.json · .nojekyll
```

Preview locally — double-click `start.command` (Mac/Linux) or `start.bat` (Windows),
which finds a free port, starts a server and opens your browser. Or manually:

```bash
npx http-server -p 8080 .     # then open http://localhost:8080
# or: python3 -m http.server 8080
```

---

## 1. Make it yours

Everything you must change is marked in the source with `CUSTOMIZE` comments
or `[SQUARE BRACKETS]`. Find them all:

```bash
grep -rn "CUSTOMIZE" .          # every editable decision
grep -rno "\[[A-Z ][A-Z0-9 /.,'&-]*\]" . | sort -u   # every placeholder
```

### Brand name

`APEX PERFORMANCE` appears in the nav, menu, footer, OG tags and JSON-LD.
One pass replaces it everywhere:

```bash
# Long form, then the short wordmark + tagline halves
grep -rl "APEX PERFORMANCE" . | xargs sed -i 's/APEX PERFORMANCE/YOUR BRAND/g'
grep -rl ">APEX<"           . | xargs sed -i 's/>APEX</>YOUR</g'
grep -rl "brand__mark\">"   . | xargs sed -i 's/brand__mark">PERFORMANCE</brand__mark">BRAND</g'
```

(On macOS use `sed -i ''`.) Then swap `images/favicon.svg` — it's a two-line
SVG, change the `<path>` or drop in your own mark.

### Your details

Replace these placeholders across all pages:

| Placeholder | Where it shows |
|---|---|
| `[YOUR NAME]` | About page, meta author, Person schema |
| `[CITY]`, `[COUNTRY]` | Nav menu, footer, hero kicker, schema, titles |
| `[YOUR EMAIL]`, `[YOUR PHONE]` | Footer, contact page, schema, JS error message |
| `[YOUR PHONE E164]` | `tel:` links — use `+441234567890` format |
| `[GYM NAME]` | About, services, contact |
| `[INSTAGRAM URL]` etc. | Footer + contact social links |
| `[YOUR CERTIFICATION 1]` … | Home marquee, About credentials list, home credentials chips |
| `$[XXX]` | Services pricing |
| `https://www.your-domain.com` | **Canonical URLs, OG tags, sitemap, robots, all JSON-LD** |

The domain matters most — do it in one pass:

```bash
grep -rl "your-domain.com" . | xargs sed -i 's|www\.your-domain\.com|www.yourrealdomain.com|g'
```

### Colours

All in `css/styles.css` → `:root`. It's a strict three-value monochrome
palette; change these and the whole site follows, including the inverted
sections, which derive from the same tokens.

```css
--ink:       #0B0B0B;   /* text, dark sections, buttons */
--paper:     #F7F7F5;   /* page background, text on dark */
--grey:      #6B6B6B;   /* secondary text only */
--radius:    2px;       /* 14px for a softer, less editorial feel */
```

Want an accent colour? Add `--accent: #C8FF00;` to `:root`, then use it on
`.btn { --btn-bg: var(--accent); --btn-fg: var(--ink); }`. Check contrast
first at <https://webaim.org/resources/contrastchecker/> — 4.5:1 minimum.

> Dark sections (`.hero`, `.cta`, `.invert`, `.pagehead`, `.footer`) redeclare
> the token set, not just `color`. If you build a new dark section, copy that
> token block or components reading `var(--fg)` will render ink-on-ink.

### Fonts — read this before changing them

The site uses **Noto Sans Display** (headlines), **Inter** (body) and
**JetBrains Mono** (labels), loaded from Google Fonts.

These three were chosen because **they all ship Greek glyphs**. Many popular
display faces do not — Archivo, Anton, Oswald, Montserrat and Barlow all
lack a Greek subset, and Greek text in them silently falls back to a system
font, which looks broken next to the rest of the page.

Before swapping a family, check it covers Greek:

```bash
curl -s "https://fonts.googleapis.com/css2?family=YOUR+FONT&display=swap" \
  -A "Mozilla/5.0 (Windows NT 10.0) Chrome/120.0" | grep -c "0370"
```

A result above `0` means the Greek range (U+0370–03FF) is served. Verified
Greek-capable alternatives: Roboto Condensed, Fira Sans Condensed, Manrope,
Noto Sans Mono, Roboto Mono, Source Code Pro.

Change the families in **every** `.html` `<head>` and in the `--font-*`
tokens in `css/styles.css`. Note that Noto Sans Display's width axis stops
at 100 (some faces go to 125), so `font-variation-settings: "wdth"` values
above 100 clamp silently.

### Images

Replace the SVGs in `/images` with real photos, keeping the filenames — then
nothing else needs editing. Keep the aspect ratios so nothing reflows:

| File | Ratio | Suggested export |
|---|---|---|
| `hero-athlete` | 3:2 | 1920×1280 |
| `portrait-trainer` | 3:4 | 900×1200 |
| `training-strength` | 4:5 | 900×1125 |
| `training-speed` | 1:1 | 900×900 |
| `training-testing`, `training-gym` | 8:5 | 1200×750 |
| `result-01-before` / `-after` | 4:3 | 1200×900, **same crop and framing** |
| `og-image` | 1200×630 | see below |

Using `.jpg`? Update the `src` **and** the `width`/`height` attributes, which
are there to prevent layout shift.

The site greyscales every photo (`filter: grayscale(100%)`) to hold the
monochrome direction. To show colour, delete that line from `.figure img`,
`.compare img` and `.hero__media img`.

`images/og-image.png` is a generated placeholder. Replace it with a real
1200×630 export — it's what shows in WhatsApp, iMessage, LinkedIn and X.

---

## 2. The form

`apply.html` is the single form on the site. Ten fields, one page:
name, email, phone, city, sport, goal (option cards), experience, program,
injuries, message — plus a consent checkbox.

It validates inline (nothing sends until the required fields and the goal
are answered), autosaves to `localStorage` so a half-filled form survives a
closed tab, and swaps in a confirmation panel instead of reloading.

Field `name` attributes are **in Greek** ("Ονοματεπώνυμο", "Τραυματισμοί")
because they become the column headings in whatever inbox or spreadsheet
your form provider delivers to. The error-message ids follow the field name,
so if you rename `Στόχος` you must rename `id="Στόχος-error"` to match.

To add a field, copy an existing `.field` block. Mark it required with
`data-validate="required"` (or `email`), give it a unique `id`, and add a
matching `<p class="field__error" id="<id>-error" role="alert"></p>`.

`contact.html` deliberately has **no second form** — it holds your direct
details and the booking link, and points at this one. One form, one place
enquiries land.

## 3. Connecting the form

Set the endpoint on `#apply-form` in `apply.html`:

**Formspree** — `action="https://formspree.io/f/YOUR_FORM_ID"`

**Netlify Forms** — `action="/"` plus `netlify netlify-honeypot="_gotcha"`
on the `<form>` tag.

**Basin / Getform / FormSubmit** — paste their endpoint into `action`.

Anything that accepts a `POST` of `FormData` and returns 2xx works. Until
you connect one, the form stays in demo mode and says so in Greek rather
than failing silently. Leave the hidden `_gotcha` field in — it stops most
spam bots.

### Booking tool

`contact.html` has a button with `href="[LINK CALENDLY Ή CAL.COM]"` — paste
your scheduling URL in.

## 4. Deploying

**Netlify** — drag the `website/` folder onto <https://app.netlify.com/drop>.
Done. For git deploys set base directory `website`, publish directory `.`,
leave the build command empty. `netlify.toml` handles headers and the 404.

**Vercel** — `vercel --cwd website`, or import the repo and set the root
directory to `website` with framework preset "Other". `vercel.json` is set up.

**GitHub Pages** — Pages serves from the repo root or `/docs`, not an
arbitrary folder, so either move these files to the repo root, rename
`website/` to `docs/` and pick "main /docs" in Settings → Pages, or use a
workflow that publishes the subfolder. `.nojekyll` is already here, which
stops Jekyll from dropping files.

**Custom domain** — after DNS, do the `your-domain.com` find-and-replace
above, then submit `sitemap.xml` in Google Search Console.

---

## 5. Analytics (optional)

Add before `</head>` on every page. Plausible is cookieless, so in most
jurisdictions it needs no consent banner:

```html
<script defer data-domain="yourdomain.com" src="https://plausible.io/js/script.js"></script>
```

Google Analytics 4 does set cookies — you'll need a consent banner in the
UK/EU, and to describe it in `privacy.html`:

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXX"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}
gtag('js',new Date());gtag('config','G-XXXXXXX');</script>
```

To track enquiries, add a `gtag('event','generate_lead')` call inside the
success branch of the fetch in `js/main.js`.

---

## 6. How the code is organised

**CSS** (`css/styles.css`) is one file in 25 numbered sections — tokens,
reset, a11y, layout, type, buttons, nav, hero, marquee, stats, cards,
process, testimonials, compare slider, FAQ, form, media, CTA, footer,
texture, reveal, utilities, motion prefs, print. Scan the section headers.

**JS** (`js/main.js`) is twelve independent IIFEs; delete any one and the
rest keeps working:

1. sticky/hide-on-scroll nav · 2. mobile menu (focus trap, Escape)
3. split-text line masking · 4. IntersectionObserver reveals
5. scroll progress bar · 6. hero parallax · 7. custom cursor + magnetic buttons
8. animated counters · 9. FAQ accordion · 10. before/after slider
11. form validation, autosave and submit · 12. footer year

**Turning off effects**: delete the `data-reveal` / `data-split` attributes to
stop animations; set `--grain` opacity to `0` in `:root` to remove the film
grain; delete IIFE 7 to remove the custom cursor.

`prefers-reduced-motion` is honoured throughout — all of it degrades to a
static page for visitors who ask for that.

## 7. Accessibility notes

Semantic landmarks, one `<h1>` per page, no skipped heading levels, skip
link, visible focus rings, labelled form fields with `role="alert"` errors,
`aria-expanded`/`aria-controls` on the accordion and menu, keyboard-operable
before/after slider (it's a real `<input type="range">`), alt text on every
image. If you edit, keep those intact — and write real alt text describing
your photos.

## 8. Before you go live

See the checklist in the pull request / handover notes, or re-read the
`CUSTOMIZE` comments. The short version: **replace every statistic and
testimonial with something true.** The numbers in here are placeholders, and
publishing invented results is both dishonest and, in most countries,
unlawful advertising.
