# APEX PERFORMANCE — personal trainer website

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
├── contact.html       Short enquiry form, direct details, booking link
├── apply.html         6-step client application (the main conversion path)
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

### Fonts

Currently Archivo (display), Inter (body), IBM Plex Mono (labels), loaded
from Google Fonts. To change: edit the `<link>` tags in **every** `.html`
`<head>`, then the `--font-*` tokens in `css/styles.css`.

To self-host instead (faster, and avoids the Google Fonts GDPR question that
affects EU/UK businesses): download from <https://gwfh.mranftl.com>, put the
`.woff2` files in `/fonts`, replace the `<link>` tags with `@font-face` rules
using `font-display: swap`.

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

## 2. The two forms

There are deliberately two, doing different jobs:

**`apply.html` — the client application.** Six steps: about you, your goal,
training background, health, program fit, then a review screen before
sending. This is where the nav "Apply" button and every primary CTA point.
It validates per step (you can't skip a required answer), autosaves to
`localStorage` so a half-finished application survives a closed tab, and
shows a confirmation panel rather than a page reload. Without JavaScript it
degrades to one long form that posts normally.

To add, remove or reorder a step: each step is a `<section class="wizard__step"
data-step="N" data-name="Label">`. The progress bar reads its segment count
from `.wizard__bar` — add or remove a `<span class="wizard__seg">` to match.
Mark a field required with `data-validate="required|email|min20"`, and a radio
group with `data-required-group="Field name"` on the `.choices` wrapper.

Field `name` attributes are written in plain English ("Full name", "Injuries")
because they become the column headings in whatever inbox or spreadsheet your
form provider delivers to. Rename them freely — the review screen reads them
automatically.

**`contact.html` — the low-friction alternative.** Name, email, message. For
people who don't want to fill in an application, and a fallback if the
application feels like too much for a quick question.

## 3. Connecting the forms

Both forms take the same endpoint. Set it on each one separately —
`#apply-form` in `apply.html` and `#enquiry-form` in `contact.html`.

The enquiry form is at `contact.html` and posts via `fetch`, so the visitor
never leaves the page. Until you connect it, it stays in demo mode and says
so. Pick one:

**Formspree** (easiest) — sign up, create a form, then:
```html
<form ... action="https://formspree.io/f/YOUR_FORM_ID" ...>
```

**Netlify Forms** (free if you host there) — add two attributes:
```html
<form id="enquiry-form" method="POST" action="/" netlify netlify-honeypot="_gotcha" ...>
```

**Basin / Getform / FormSubmit** — paste their endpoint into `action`.

Any endpoint accepting a `POST` of `FormData` and returning 2xx works. The
form already sends `name`, `email`, `sport`, `program`, `message`, plus
`_subject` and `_source` fields, and carries a `_gotcha` honeypot — leave
that hidden field in, it stops most spam.

One more edit: `js/main.js` has a fallback message containing `[YOUR EMAIL]`
shown if the request fails. Put your real address there.

### Booking tool


`contact.html` has a button with `href="[YOUR CALENDLY OR CAL.COM LINK]"` —
paste your scheduling URL in. For a full inline widget instead, replace the
button with:

```html
<div class="calendly-inline-widget" data-url="https://calendly.com/YOUR-LINK"
     style="min-width:320px;height:660px"></div>
<script src="https://assets.calendly.com/assets/external/widget.js" async></script>
```

---

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
11. form validation + submit · 12. footer year
13. application wizard — steps, validation, autosave, review, submit

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
