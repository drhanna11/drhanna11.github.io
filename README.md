# Indie Appliance Repair

A static directory of independent and locally owned appliance repair technicians, launching in the Phoenix, Arizona metro. Built as plain HTML, CSS, and JS for GitHub Pages. There is no required build for hosting once the HTML is generated; a small Python script regenerates pages from JSON.

This repository was prepared on the operator's computer. It has **not** been published, and no GitHub (or other) account was created from this work.

## Preview locally

From this folder:

```bash
python3 -m http.server 8080
```

Then open http://localhost:8080/. Clean URLs such as `/phoenix/` work because each section is a folder with `index.html`.

## Data and URL scheme

| Kind | Path | Source |
| --- | --- | --- |
| Homepage | `/` | generated |
| City | `/phoenix/` | `data/cities.json` + listings |
| City + appliance | `/phoenix/refrigerator-repair/` | `data/appliances.json` + listings that mention that appliance |
| Shop profile | `/phoenix/techs/{slug}/` | one object in `data/listings.json` |
| Guides / compare / best-for | `/guides/...`, `/compare/...`, `/best/...` | templates in `scripts/build.py` (later: optional `data/pages.json`) |
| Get listed / disclosure / about | `/get-listed/`, `/disclosure/`, `/about/` | templates in `scripts/build.py` |

Site-wide copy and the optional public origin live in `data/site.json`. Affiliate placement copy and tracking-URL placeholders live in `data/affiliates.json`; leave `enabled` false and `trackingUrl` empty until a program is approved, then rebuild.

## How to add a listing

1. Open a public source (usually the shop's own website). Do not invent ratings, reviews, prices, hours, or service areas.
2. Add an object to `data/listings.json`. Follow an existing listing: `id`/`slug`, `name`, `phone` (digits only) and `phoneDisplay`, `website`, optional `email` and `address`, `serviceAreas`, `appliances` (slugs from `data/appliances.json`), optional `brands` and `brandsNote`, `hours`, `flags`, `facts`, and a `sources` array with `url`, `accessed` (YYYY-MM-DD), and `facts`.
3. Regenerate the site (this also rewrites `sitemap.xml` and `robots.txt`):

```bash
python3 scripts/build.py
```

4. Spot-check the new profile and the city / appliance pages it should appear on.

To add a **new city**, add it to `data/cities.json` with `"status": "live"` and extend `scripts/build.py` so that city gets a page (Phoenix is the only live city in the first build). To add an **appliance category**, add it to `data/appliances.json` and rebuild; a city+appliance page is created when at least one listing mentions that slug.

Editorial pages (new guides, comparisons) are added as functions in `scripts/build.py` and registered in `main()`. See `PLAN.md` for the prioritized backlog of the next 30 pages.

## GitHub Pages (not done yet)

- The repo includes `.nojekyll` so Pages will not run Jekyll on the HTML.
- When a public origin is known, set `canonicalOrigin` in `data/site.json` (no trailing slash, for example `https://www.example.com`) and run the build again so canonical tags and the sitemap use absolute URLs.
- If the site is served from a project URL such as `https://user.github.io/repo/`, set `"baseUrl"` support is still TODO — prefer a custom domain or a user/organization site at the root, or add a base-prefix helper before launching on a subpath.
- Do not push or create a GitHub repository until the owner has signed in and approved publishing.

## Editorial rules

- Facts on listing pages must come from a recorded source URL.
- No invented ratings, reviews, or prices. Published service-call fees may be quoted with the access date and a note to confirm by phone.
- National franchises and lead-mill landing pages stay out of the independent directory.
