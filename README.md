# Indie Appliance Repair

A static directory of independent and locally owned appliance repair technicians, live in the Phoenix, Arizona metro and Riverside County, California. Built as plain HTML, CSS, and JS for GitHub Pages at [indieappliancerepair.com](https://indieappliancerepair.com). There is no required build for hosting once the HTML is generated; a small Python script regenerates pages from JSON.

## Preview locally

From this folder:

```bash
python3 -m http.server 8080
```

Then open http://localhost:8080/. Clean URLs such as `/phoenix/` and `/riverside-county/temecula/` work because each section is a folder with `index.html`.

## Data and URL scheme

| Kind | Path | Source |
| --- | --- | --- |
| Homepage | `/` | generated |
| Metro / county hub | `/phoenix/`, `/riverside-county/` | `data/cities.json` + listings with that `citySlug` |
| City or area page | `/riverside-county/temecula/`, `/riverside-county/coachella-valley/` | `cities[].cities` in `data/cities.json`; shops whose `serviceAreas` match |
| Metro + appliance | `/phoenix/refrigerator-repair/`, `/riverside-county/refrigerator-repair/` | `data/appliances.json` + listings in that metro that mention the appliance |
| Shop profile | `/phoenix/techs/{slug}/`, `/riverside-county/techs/{slug}/` | one object in `data/listings.json` |
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

To add a **new metro or county**, add it to `data/cities.json` with `"status": "live"`, give listings that `citySlug`, and rebuild. Optional `cities` entries under a metro generate city or area pages (Riverside County uses these). To add an **appliance category**, add it to `data/appliances.json` and rebuild; a metro+appliance page is created when at least one listing in that metro mentions that slug. California pages include a short BHGS registration note and a link to the official license search.

Editorial pages (new guides, comparisons) are added as functions in `scripts/build.py` and registered in `main()`. See `PLAN.md` for the prioritized backlog of the next 30 pages.

## GitHub Pages

- The site is published at `https://indieappliancerepair.com` (`canonicalOrigin` in `data/site.json`). Rebuild after changing that value so canonical tags, the sitemap, and the `CNAME` file stay in sync.
- The repo includes `.nojekyll` so Pages will not run Jekyll on the HTML.
- Never push the `private-history` branch. Planning notes and `outreach/` are gitignored.

## Editorial rules

- Facts on listing pages must come from a recorded source URL.
- No invented ratings, reviews, or prices. Published service-call fees may be quoted with the access date and a note to confirm by phone.
- National franchises and lead-mill landing pages stay out of the independent directory.
