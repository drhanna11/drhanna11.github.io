#!/usr/bin/env python3
"""Generate static HTML, sitemap.xml, and robots.txt from data/*.json."""
from __future__ import annotations

import json
import shutil
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TODAY = date.today().isoformat()

site = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
appliances = json.loads((DATA / "appliances.json").read_text(encoding="utf-8"))
cities = json.loads((DATA / "cities.json").read_text(encoding="utf-8"))
listings = json.loads((DATA / "listings.json").read_text(encoding="utf-8"))
affiliates_cfg = json.loads((DATA / "affiliates.json").read_text(encoding="utf-8"))
AFF_PROGRAMS = affiliates_cfg.get("programs", {})
AFF_PLACEMENTS = affiliates_cfg.get("placements", {})

APPLIANCE_BY_SLUG = {a["slug"]: a for a in appliances}
CITY_BY_SLUG = {c["slug"]: c for c in cities}
LISTINGS_BY_SLUG = {l["slug"]: l for l in listings}
LISTINGS = sorted(listings, key=lambda l: l["name"].lower())


def href(page_file: str, target: str) -> str:
    """Relative URL from a generated file (e.g. phoenix/index.html) to a site path."""
    depth = Path(page_file).as_posix().count("/")
    prefix = "../" * depth
    target = target.lstrip("/")
    if not target or target == "/":
        return prefix + "index.html" if prefix else "index.html"
    return prefix + target


def tel_href(phone: str) -> str:
    return f"tel:+1{phone}"


def e(text) -> str:
    return escape("" if text is None else str(text), quote=True)


def flag_label(flag: str) -> str:
    return {
        "owner-operated": "Owner-operated",
        "family-owned": "Family-owned",
        "locally-owned": "Locally owned",
        "independent-specialist": "Independent specialist",
    }.get(flag, flag.replace("-", " ").title())


def flags_html(listing: dict) -> str:
    if not listing.get("flags"):
        return ""
    pills = "".join(f'<span class="pill">{e(flag_label(f))}</span>' for f in listing["flags"])
    return f'<div class="flags">{pills}</div>'


def appliances_for(listing: dict) -> list[dict]:
    return [APPLIANCE_BY_SLUG[s] for s in listing.get("appliances", []) if s in APPLIANCE_BY_SLUG]


def listings_for_appliance(slug: str) -> list[dict]:
    return [l for l in LISTINGS if slug in l.get("appliances", [])]


def ld_json(obj: dict) -> str:
    payload = json.dumps(obj, ensure_ascii=False, indent=None)
    payload = payload.replace("<", "\\u003c")
    return f'<script type="application/ld+json">{payload}</script>'


def logo_svg() -> str:
    return """<span class="logo-mark" aria-hidden="true"><svg viewBox="0 0 24 24">
      <rect x="6" y="2.5" width="12" height="19" rx="1.2"/>
      <path d="M6 11.5h12"/><path d="M9 5.5v3"/><path d="M9 14v3"/>
    </svg></span>"""


def nav_html(page_file: str, current: str) -> str:
    items = [
        ("/", "Home", "home"),
        ("/phoenix/", "Phoenix", "phoenix"),
        ("/guides/repair-vs-replace/", "Guides", "guides"),
        ("/compare/independent-vs-chains/", "Compare", "compare"),
        ("/get-listed/", "Get listed", "get-listed"),
    ]
    links = []
    for path, label, key in items:
        cur = ' aria-current="page"' if current == key else ""
        cls = ' class="nav-cta"' if key == "get-listed" else ""
        links.append(f'<li><a href="{e(href(page_file, path))}"{cls}{cur}>{e(label)}</a></li>')
    return f'<ul>{"".join(links)}</ul>'


def crumbs_html(page_file: str, crumbs: list[tuple[str, str]]) -> str:
    parts = []
    items = []
    for i, (path, label) in enumerate(crumbs):
        last = i == len(crumbs) - 1
        if last:
            parts.append(f"<li aria-current='page'>{e(label)}</li>")
        else:
            parts.append(f'<li><a href="{e(href(page_file, path))}">{e(label)}</a></li>')
        item = {"@type": "ListItem", "position": i + 1, "name": label}
        if not last:
            # Breadcrumb URLs stay path-only until a public origin is set
            item["item"] = path if path != "/" else "/"
        items.append(item)
    schema = ld_json({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    })
    return f'<nav class="crumbs" aria-label="Breadcrumb"><ol>{"".join(parts)}</ol></nav>\n{schema}'


def footer_html(page_file: str) -> str:
    return f"""<footer class="site-footer">
  <div class="wrap footer-grid">
    <div>
      <h2>Indie Appliance Repair</h2>
      <p>A small directory of independent and locally owned appliance technicians. We publish only facts we can source, and we never invent ratings, reviews, or prices.</p>
    </div>
    <div>
      <h2>Explore</h2>
      <ul>
        <li><a href="{e(href(page_file, "/phoenix/"))}">Phoenix directory</a></li>
        <li><a href="{e(href(page_file, "/guides/repair-vs-replace/"))}">Repair vs. replace</a></li>
        <li><a href="{e(href(page_file, "/compare/independent-vs-chains/"))}">Independent vs. chains</a></li>
        <li><a href="{e(href(page_file, "/best/sub-zero/"))}">Techs who list Sub-Zero</a></li>
      </ul>
    </div>
    <div>
      <h2>This site</h2>
      <ul>
        <li><a href="{e(href(page_file, "/about/"))}">About &amp; method</a></li>
        <li><a href="{e(href(page_file, "/get-listed/"))}">Get listed / featured</a></li>
        <li><a href="{e(href(page_file, "/disclosure/"))}">Affiliate disclosure</a></li>
      </ul>
    </div>
  </div>
  <div class="wrap footer-legal">
    <p><strong>Affiliate disclosure:</strong> {e(site["disclosureSummary"])}</p>
    <p>© {date.today().year} Indie Appliance Repair. Listings are provided for information only; always confirm details directly with the business. Not affiliated with Angi, Sears, Mr. Appliance, or any manufacturer unless a listing page says a shop made that claim itself.</p>
  </div>
</footer>"""



def aff_is_live(program: dict) -> bool:
    return bool(program.get("enabled") and str(program.get("trackingUrl") or "").strip())


def aff_href(page_file: str, program_id: str) -> tuple[str, bool]:
    """Return (href, is_live). Pending programs point at the disclosure page."""
    program = AFF_PROGRAMS.get(program_id) or {}
    if aff_is_live(program):
        return str(program["trackingUrl"]).strip(), True
    return href(page_file, "/disclosure/#affiliate-placeholders"), False


def aff_link(page_file: str, program_id: str, label: str | None = None) -> str:
    program = AFF_PROGRAMS.get(program_id)
    if not program:
        return ""
    url, live = aff_href(page_file, program_id)
    text_label = label or program.get("label") or program.get("name") or program_id
    cls = "aff-link" + ("" if live else " is-pending")
    pending = "" if live else ' data-aff-pending="true"'
    target = ' target="_blank"' if live else ""
    extra_rel = " noopener noreferrer" if live else ""
    return (
        f'<a class="{cls}" href="{e(url)}" data-aff="{e(program_id)}"{pending}'
        f' rel="sponsored nofollow{extra_rel}"{target}>{e(text_label)}</a>'
    )


def aff_box(page_file: str, placement_id: str, extra_intro: str | None = None) -> str:
    """Labeled affiliate slot. Harmless until trackingUrl is filled in."""
    placement = AFF_PLACEMENTS.get(placement_id)
    if not placement:
        return ""
    links = []
    for pid in placement.get("programs") or []:
        if pid not in AFF_PROGRAMS:
            continue
        links.append(f"<li>{aff_link(page_file, pid)}</li>")
    if not links:
        return ""
    intro = extra_intro or placement.get("intro") or ""
    disclosure = href(page_file, "/disclosure/#affiliate-placeholders")
    any_live = any(
        aff_is_live(AFF_PROGRAMS[pid]) for pid in placement.get("programs") or [] if pid in AFF_PROGRAMS
    )
    status = "some links in this box may earn a commission" if any_live else "links are not active yet"
    pending_note = ""
    if not any_live:
        pending_note = (
            " <strong>These are placeholders.</strong> They go to our disclosure page, not to a retailer, "
            "and we do not earn a commission from them until a program is approved and a tracking link is installed."
        )
    title = e(placement.get("title") or "Related products")
    return (
        f'<aside class="aff-box" data-aff-placement="{e(placement_id)}" aria-label="Affiliate placement">'
        f'<p class="aff-box-kicker">Affiliate placement &middot; {e(status)}</p>'
        f"<h2>{title}</h2>"
        f"<p>{e(intro)}{pending_note}</p>"
        f'<ul class="aff-actions">{"".join(links)}</ul>'
        f'<p class="aff-box-foot"><a href="{e(disclosure)}">Affiliate disclosure</a></p>'
        "</aside>\n"
    )


def sponsorship_box(page_file: str, brand: str) -> str:
    """Direct-revenue slot for a labeled brand-specialist sponsorship. Not an affiliate unit."""
    listed = href(page_file, "/get-listed/")
    return (
        f'<aside class="sponsor-box" data-spot="brand-specialist" aria-label="Sponsorship placement">'
        f'<p class="aff-box-kicker">Sponsorship placement &middot; not sold yet</p>'
        f"<h2>Featured {e(brand)} specialist</h2>"
        f"<p>This reserved slot is for a clearly labeled, paid sponsorship by a shop that services {e(brand)} "
        "appliances. It will not be presented as a ranked &ldquo;best of,&rdquo; and it will not replace the unpaid "
        "list above. No sponsorships have been sold.</p>"
        f'<p class="aff-box-foot"><a href="{e(listed)}">Shops: ask about a featured or specialist listing</a></p>'
        "</aside>\n"
    )


def layout(
    page_file: str,
    title: str,
    description: str,
    body: str,
    current: str,
    crumbs: list[tuple[str, str]] | None = None,
    extra_head: str = "",
    extra_after: str = "",
) -> str:
    css = href(page_file, "/css/styles.css")
    js = href(page_file, "/js/main.js")
    home = href(page_file, "/")
    crumb_block = crumbs_html(page_file, crumbs) if crumbs else ""
    origin = (site.get("canonicalOrigin") or "").rstrip("/")
    path = "/" if page_file == "index.html" else "/" + str(Path(page_file).parent).replace("\\", "/") + "/"
    if page_file.endswith("404.html"):
        path = "/404.html"
    canonical = f'<link rel="canonical" href="{e(origin + path)}">' if origin else ""
    return f"""<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(description)}">
  <meta name="robots" content="index,follow">
  {canonical}
  <link rel="stylesheet" href="{e(css)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Source+Sans+3:wght@400;550;650;700&display=swap" rel="stylesheet">
  {extra_head}
</head>
<body>
  <a class="skip" href="#content">Skip to content</a>
  <header class="site-header">
    <div class="wrap">
      <div class="header-inner">
        <a class="logo" href="{e(home)}">{logo_svg()}<span class="logo-text"><strong>Indie Appliance Repair</strong><span>Independent techs, not a lead mill</span></span></a>
        <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>
      </div>
      <nav class="site-nav" id="site-nav" aria-label="Primary">{nav_html(page_file, current)}</nav>
    </div>
  </header>
  <main id="content">
    <div class="wrap">{crumb_block}{body}</div>
  </main>
  {footer_html(page_file)}
  {extra_after}
  <script src="{e(js)}" defer></script>
</body>
</html>
"""


def write_page(page_file: str, html: str) -> None:
    path = ROOT / page_file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def listing_url(listing: dict) -> str:
    return f"/phoenix/techs/{listing['slug']}/"


def listing_card(page_file: str, listing: dict) -> str:
    apps = ", ".join(a["name"] for a in appliances_for(listing)) or "See profile"
    areas = ", ".join(listing.get("serviceAreas", [])[:6])
    if len(listing.get("serviceAreas", [])) > 6:
        areas += ", and more"
    more = href(page_file, listing_url(listing))
    call = tel_href(listing["phone"])
    return f"""<article class="listing-card">
  {flags_html(listing)}
  <h3><a href="{e(more)}">{e(listing["name"])}</a></h3>
  <p class="meta">{e(areas)}</p>
  <p class="meta">Lists: {e(apps)}</p>
  <a class="phone" href="{e(call)}">Call {e(listing["phoneDisplay"])}</a>
  <p class="meta"><a href="{e(more)}">View profile and sources</a></p>
</article>"""


def address_line(listing: dict) -> str | None:
    a = listing.get("address") or {}
    if a.get("street") and a.get("city") and a.get("state"):
        zip_part = f" {a['zip']}" if a.get("zip") else ""
        return f"{a['street']}, {a['city']}, {a['state']}{zip_part}"
    if a.get("city") and a.get("state"):
        zip_part = f" {a['zip']}" if a.get("zip") else ""
        return f"{a['city']}, {a['state']}{zip_part}"
    return None


def local_business_schema(listing: dict) -> dict:
    a = listing.get("address") or {}
    addr = {
        "@type": "PostalAddress",
        "addressRegion": a.get("state") or "AZ",
        "addressCountry": "US",
    }
    if a.get("city"):
        addr["addressLocality"] = a["city"]
    if a.get("street"):
        addr["streetAddress"] = a["street"]
    if a.get("zip"):
        addr["postalCode"] = a["zip"]
    data = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": listing["name"],
        "telephone": f"+1{listing['phone']}",
        "url": listing.get("website"),
        "address": addr,
        "areaServed": listing.get("serviceAreas") or ["Phoenix, AZ"],
    }
    if listing.get("email"):
        data["email"] = listing["email"]
    return data


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def page_home() -> None:
    page = "index.html"
    phoenix = href(page, "/phoenix/")
    cats = []
    for app in appliances:
        n = len(listings_for_appliance(app["slug"]))
        url = href(page, f"/phoenix/{app['pathSegment']}/")
        cats.append(
            f"""<a class="cat-card" href="{e(url)}">
              <h3>{e(app["name"])} repair</h3>
              <p>{e(app["blurb"])}</p>
              <p class="meta">{n} Phoenix-metro listing{"s" if n != 1 else ""} so far</p>
            </a>"""
        )
    city_cards = []
    for c in cities:
        if c["status"] == "live":
            city_cards.append(
                f"""<a class="city-card" href="{e(href(page, f'/{c["slug"]}/'))}">
                  <h3>{e(c["name"])}, {e(c["state"])}</h3>
                  <p>{e(c["summary"])}</p>
                  <p class="meta"><span class="pill">Live · {len(LISTINGS)} listings</span></p>
                </a>"""
            )
        else:
            city_cards.append(
                f"""<div class="city-card planned">
                  <h3>{e(c["name"])}, {e(c["state"])}</h3>
                  <p>{e(c["summary"])}</p>
                  <p class="meta"><span class="pill">Coming next</span></p>
                </div>"""
            )
    body = f"""
    <header class="hero">
      <p class="kicker">Phoenix launch directory</p>
      <h1>Independent appliance repair techs you can actually call</h1>
      <p class="lede">A growing list of owner-operated and locally owned shops in the Phoenix metro — the alternative to Angi, Sears, and Mr. Appliance. We list names, phones, service areas, and source URLs. We do not invent ratings or prices.</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="{e(phoenix)}">Browse Phoenix techs</a>
        <a class="btn btn-ghost" href="{e(href(page, "/get-listed/"))}">Get listed</a>
      </div>
    </header>
    <section class="section">
      <h2>Repair by appliance</h2>
      <p class="lede">Start with the machine that quit. Every category page lists only shops that mention that appliance on a source we opened.</p>
      <div class="grid grid-2 grid-4">{"".join(cats)}</div>
    </section>
    <section class="section">
      <h2>Cities</h2>
      <p class="lede">We are going deep on one metro first, then expanding city by city.</p>
      <div class="grid grid-2">{"".join(city_cards)}</div>
    </section>
    <section class="section">
      <h2>Useful guides</h2>
      <div class="grid grid-2 grid-3">
        <a class="card cat-card" href="{e(href(page, "/guides/repair-vs-replace/"))}">
          <h3>Repair or replace?</h3>
          <p>A practical way to decide after you have a diagnosis — without made-up average prices.</p>
        </a>
        <a class="card cat-card" href="{e(href(page, "/compare/independent-vs-chains/"))}">
          <h3>Independent vs. chains</h3>
          <p>How calling a local shop differs from a national dispatch line or a lead marketplace.</p>
        </a>
        <a class="card cat-card" href="{e(href(page, "/best/sub-zero/"))}">
          <h3>Shops that list Sub-Zero</h3>
          <p>Phoenix-metro listings whose own sites mention Sub-Zero service — not a ranked “best of.”</p>
        </a>
      </div>
    </section>
    <section class="section">
      <h2>How this directory works</h2>
      <div class="grid grid-2">
        <div class="card">
          <h3>Facts, not scores</h3>
          <p>Each profile records the business website (or other public page) we used, and only includes phones, addresses, hours, brands, and fees if those pages stated them. If we could not verify a detail, we left it out.</p>
        </div>
        <div class="card">
          <h3>Call the shop directly</h3>
          <p>There is no lead auction and no “we will have three companies call you” form. Click-to-call goes to the number the business published. Confirm coverage, price, and availability when you reach them.</p>
        </div>
      </div>
    </section>
    """
    desc = (
        "Find independent and locally owned appliance repair technicians in the Phoenix metro. "
        "Call shops directly — not a lead mill. Refrigerator, washer, dryer, and more."
    )
    schema = ld_json({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": site["name"],
        "description": site["description"],
        "about": "Independent appliance repair technician directory",
    })
    itemlist = ld_json({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Appliance repair categories in Phoenix",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": f"{a['name']} repair", "url": f"/phoenix/{a['pathSegment']}/"}
            for i, a in enumerate(appliances)
        ],
    })
    write_page(page, layout(page, "Indie Appliance Repair — Independent techs in Phoenix", desc, body, "home", extra_head=schema + itemlist))


def page_phoenix() -> None:
    page = "phoenix/index.html"
    cards = "".join(listing_card(page, l) for l in LISTINGS)
    filters = ['<a href="#listings" class="is-active" aria-current="page">All shops</a>']
    for app in appliances:
        n = len(listings_for_appliance(app["slug"]))
        if n:
            filters.append(
                f'<a href="{e(href(page, f"/phoenix/{app["pathSegment"]}/"))}">{e(app["name"])} ({n})</a>'
            )
    body = f"""
    <header class="hero">
      <p class="kicker">Launch metro</p>
      <h1>Independent appliance repair in Phoenix, Arizona</h1>
      <p class="lede">A directory of {len(LISTINGS)} independent or locally based shops serving Phoenix and the Valley of the Sun. We gathered these from the businesses' own websites. Always call to confirm that they still serve your ZIP, and that the phone number is current.</p>
    </header>
    <p class="note">Phoenix is our first metro because it is a large, year-round repair market — desert heat puts extra load on refrigerators, ice makers, and laundry equipment — and because we could document a deep bench of owner-operated and locally owned shops. Next we will add suburb pages (Mesa, Chandler, Scottsdale, and others) and then Tucson.</p>
    <div class="filter-bar" aria-label="Filter by appliance">{"".join(filters)}</div>
    <section class="section" id="listings">
      <h2>{len(LISTINGS)} shops in the Phoenix metro</h2>
      <div class="grid grid-2">{cards}</div>
    </section>
    <section class="section faq">
      <h2>Phoenix appliance repair questions</h2>
      <details><summary>Do these companies cover my suburb?</summary>
      <p>Many Valley shops cover several cities. Each profile lists only the service areas named on a source we opened. If your city is not listed, still call — coverage can be broader than the website copy, or it may have changed.</p></details>
      <details><summary>Why are there no star ratings?</summary>
      <p>We do not copy or invent review scores. Ratings go stale, can be incomplete, and are easy to misuse. Use the profile to reach the shop, then check recent reviews on a platform you trust, or ask a neighbor.</p></details>
      <details><summary>Are these the only independent techs in Phoenix?</summary>
      <p>No. This is a first batch of businesses we could verify from public websites in November 2026. Licensed shops we have not yet sourced will be added over time, and shops can <a href="{e(href(page, "/get-listed/"))}">request a listing</a>.</p></details>
    </section>
    """
    desc = (
        f"Directory of {len(LISTINGS)} independent and locally owned appliance repair businesses "
        "serving Phoenix, Mesa, Scottsdale, Chandler, Gilbert, Tempe, and the rest of the Valley."
    )
    schema = ld_json({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Independent appliance repair in Phoenix, AZ",
        "numberOfItems": len(LISTINGS),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": l["name"], "url": listing_url(l)}
            for i, l in enumerate(LISTINGS)
        ],
    })
    faq = ld_json({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": "Do these companies cover my suburb?",
             "acceptedAnswer": {"@type": "Answer", "text": "Many Valley shops cover several cities. Each profile lists only the service areas named on a source we opened. Call to confirm coverage for your ZIP."}},
            {"@type": "Question", "name": "Why are there no star ratings?",
             "acceptedAnswer": {"@type": "Answer", "text": "We do not copy or invent review scores. Use the profile to reach the shop, then check recent reviews on a platform you trust."}},
            {"@type": "Question", "name": "Are these the only independent techs in Phoenix?",
             "acceptedAnswer": {"@type": "Answer", "text": "No. This is a first batch of businesses verified from public websites in November 2026. More listings will be added over time."}},
        ],
    })
    crumbs = [("/", "Home"), ("/phoenix/", "Phoenix")]
    write_page(page, layout(
        page,
        "Independent appliance repair in Phoenix, AZ — Indie Appliance Repair",
        desc,
        body,
        "phoenix",
        crumbs,
        extra_head=schema + faq,
    ))


APPLIANCE_INTRO = {
    "refrigerator": "In the Phoenix metro, a refrigerator that stops cooling is an emergency. Valley summers put a heavy load on compressors, and food can be lost quickly once the box warms up. The shops below are ones whose own sites mention refrigerator or freezer repair. Call early, keep the doors closed, and ask about same-day availability — we do not track live schedules.",
    "washer": "A washer that will not drain, spin, or fill can shut a household down in a day. The listings on this page mentioned washer or washing-machine repair on a source we opened. Confirm whether they service your brand and type (top-load, front-load, or stacked) when you call.",
    "dryer": "Dryers that run without heat, take too long, or make new noises should be diagnosed by someone who works on gas and electric machines. Lint and vent issues can also be a fire hazard; several Valley shops mention dryer or vent work. We only include shops that listed dryer repair on a page we opened.",
    "dishwasher": "Leaks, standing water, and dishes that will not come clean are the usual reasons people look for dishwasher repair. This page lists Phoenix-metro shops that mention dishwashers on their own sites.",
    "oven-range": "Ovens, ranges, and cooktops — gas or electric — show up often in Valley service areas, including high-end brands. This page includes shops that mentioned oven, range, stove, or cooktop repair on a source we opened.",
    "microwave": "Built-in and over-the-range microwaves are a different job than a countertop unit you can carry in. We only list shops that mentioned microwave repair on a page we opened; some independents do not take microwave work, so read the profile.",
    "ice-maker": "Standalone ice machines and in-fridge ice makers are a frequent request in the Phoenix heat. This page lists shops that specifically mentioned ice maker or ice machine repair. Confirm residential vs. commercial coverage when you call.",
    "freezer": "A chest, upright, or built-in freezer that warms up can cost a lot in lost food. These shops mentioned freezer repair on a source we opened. Keep the door closed until a technician arrives, and ask whether they also handle related refrigerator work.",
}


def page_appliance(app: dict) -> None:
    rows = listings_for_appliance(app["slug"])
    if not rows:
        return
    page = f"phoenix/{app['pathSegment']}/index.html"
    cards = "".join(listing_card(page, l) for l in rows)
    intro = APPLIANCE_INTRO.get(app["slug"], app["blurb"])
    body = f"""
    <header class="hero">
      <p class="kicker">Phoenix metro</p>
      <h1>{e(app["name"])} repair in Phoenix</h1>
      <p class="lede">{e(intro)}</p>
    </header>
    <p class="fine-print">{len(rows)} listing{"s" if len(rows) != 1 else ""} on this page mentioned {e(app["name"].lower())} repair on a source we recorded. That is not a ranking, and it is not every shop in the Valley.</p>
    <div class="filter-bar">
      <a href="{e(href(page, "/phoenix/"))}">All shops</a>
      <span class="is-active">{e(app["name"])}</span>
    </div>
    <section class="section">
      <h2>Independent shops that list {e(app["name"].lower())} repair</h2>
      <div class="grid grid-2">{cards}</div>
    </section>
    <section class="section">
      <h2>Before you book</h2>
      <ul>
        <li>Have the brand and model number ready if you can find it.</li>
        <li>Ask whether the visit is a diagnosis first, what the service call costs, and whether that fee is waived if you approve the repair.</li>
        <li>If you are comparing this repair with buying new, read our <a href="{e(href(page, "/guides/repair-vs-replace/"))}">repair vs. replace guide</a>.</li>
      </ul>
    </section>
    {aff_box(page, "parts-common", extra_intro=(
        f"If you already know the model and want to look up a {app['name'].lower()} part or diagram yourself, "
        "these are the catalogs we plan to link once a program is approved. A local technician can also source the part."
    ))}
    """
    desc = (
        f"Independent {app['name'].lower()} repair in Phoenix, Arizona. "
        f"{len(rows)} locally based shops that mention {app['name'].lower()} service on their own sites."
    )
    schema = ld_json({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{app['name']} repair in Phoenix, AZ",
        "numberOfItems": len(rows),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": l["name"], "url": listing_url(l)}
            for i, l in enumerate(rows)
        ],
    })
    crumbs = [("/", "Home"), ("/phoenix/", "Phoenix"), (f"/phoenix/{app['pathSegment']}/", f"{app['name']} repair")]
    write_page(page, layout(
        page,
        f"{app['name']} repair in Phoenix, AZ — independent techs",
        desc,
        body,
        "phoenix",
        crumbs,
        extra_head=schema,
    ))


def page_profile(listing: dict) -> None:
    page = f"phoenix/techs/{listing['slug']}/index.html"
    apps = appliances_for(listing)
    app_links = ", ".join(
        f'<a href="{e(href(page, f"/phoenix/{a["pathSegment"]}/"))}">{e(a["name"])}</a>' for a in apps
    ) or "See the company website"
    areas = ", ".join(listing.get("serviceAreas") or []) or "Confirm when you call"
    addr = address_line(listing)
    sources = "".join(
        f"<li><a class='source-url' href='{e(s['url'])}' rel='noopener noreferrer'>{e(s['url'])}</a>"
        f" — {e(s['facts'])} (accessed {e(s['accessed'])})</li>"
        for s in listing.get("sources", [])
    )
    facts = "".join(f"<li>{e(f)}</li>" for f in listing.get("facts", []))
    brands = ", ".join(listing.get("brands") or [])
    rows = []
    if addr:
        rows.append(f"<div><dt>Address</dt><dd>{e(addr)}</dd></div>")
    if listing.get("addressNotes"):
        rows.append(f"<div><dt>Address note</dt><dd>{e(listing['addressNotes'])}</dd></div>")
    rows.append(f"<div><dt>Phone</dt><dd><a href='{e(tel_href(listing['phone']))}'>{e(listing['phoneDisplay'])}</a></dd></div>")
    if listing.get("email"):
        rows.append(f"<div><dt>Email</dt><dd><a href='mailto:{e(listing['email'])}'>{e(listing['email'])}</a></dd></div>")
    if listing.get("website"):
        rows.append(f"<div><dt>Website</dt><dd><a href='{e(listing['website'])}' rel='noopener noreferrer'>{e(listing['website'])}</a></dd></div>")
    if listing.get("hours"):
        rows.append(f"<div><dt>Hours</dt><dd>{e(listing['hours'])}</dd></div>")
    rows.append(f"<div><dt>Service area</dt><dd>{e(areas)}</dd></div>")
    rows.append(f"<div><dt>Appliances listed</dt><dd>{app_links}</dd></div>")
    if brands or listing.get("brandsNote"):
        brand_dd = e(brands) if brands else ""
        if listing.get("brandsNote"):
            brand_dd = (brand_dd + ". " if brand_dd else "") + e(listing["brandsNote"])
        rows.append(f"<div><dt>Brands</dt><dd>{brand_dd}</dd></div>")
    if listing.get("license"):
        rows.append(f"<div><dt>License</dt><dd>{e(listing['license'])}</dd></div>")

    sticky = f"""<div class="sticky-call" role="region" aria-label="Call this shop">
      <a class="btn btn-call" href="{e(tel_href(listing['phone']))}">Call {e(listing['phoneDisplay'])}</a>
      <a class="btn btn-ghost" href="{e(listing['website'])}" rel="noopener noreferrer">Website</a>
    </div>"""

    body = f"""
    <header class="hero">
      <p class="kicker">Phoenix metro listing</p>
      <h1>{e(listing["name"])}</h1>
      {flags_html(listing)}
      <p class="lede">An independent or locally based appliance repair business serving the Phoenix area. Details below were taken from the sources listed at the bottom of this page. Confirm everything when you call — websites go out of date.</p>
      <div class="hero-actions">
        <a class="btn btn-call" href="{e(tel_href(listing['phone']))}">Call {e(listing['phoneDisplay'])}</a>
        <a class="btn btn-ghost" href="{e(listing['website'])}" rel="noopener noreferrer">Visit website</a>
      </div>
    </header>
    <div class="profile-grid">
      <div>
        <section class="section">
          <h2>What we verified</h2>
          <dl class="dl">{"".join(rows)}</dl>
        </section>
        <section class="section">
          <h2>From the business</h2>
          <ul class="fact-list">{facts}</ul>
          <p class="fine-print">These are claims or details published by the business, not reviews or ratings from this directory.</p>
        </section>
        <section class="section sources">
          <h2>Sources</h2>
          <ul>{sources}</ul>
        </section>
      </div>
      <aside class="profile-side">
        <div class="card">
          <h2>Call this shop</h2>
          <p>We do not book appointments and we do not sell this lead. You are calling the number the business published.</p>
          <p><a class="btn btn-call" href="{e(tel_href(listing['phone']))}">Call {e(listing['phoneDisplay'])}</a></p>
          <p class="fine-print">Ask about today’s availability, the service-call fee, and whether your brand and ZIP are covered.</p>
        </div>
      </aside>
    </div>
    """
    desc = f"{listing['name']} — independent appliance repair serving {areas}. Call {listing['phoneDisplay']}."
    crumbs = [("/", "Home"), ("/phoenix/", "Phoenix"), (listing_url(listing), listing["name"])]
    write_page(page, layout(
        page,
        f"{listing['name']} — Phoenix appliance repair",
        desc,
        body,
        "phoenix",
        crumbs,
        extra_head=ld_json(local_business_schema(listing)),
        extra_after=sticky,
    ))


def page_guide() -> None:
    page = "guides/repair-vs-replace/index.html"
    body = """
    <article class="prose hero">
      <p class="kicker">Guide</p>
      <h1>Repair or replace that appliance?</h1>
      <p class="lede">Get a diagnosis first, then compare the quoted repair with the cost and remaining life of a new machine. This page does not invent average Phoenix repair prices.</p>
      <h2>Start with a diagnosis, not a guess</h2>
      <p>A “click” from a dryer or a warm refrigerator can have more than one cause. An independent technician can often tell you whether the job is a modest part and labor bill or a major sealed-system or control-board repair. Several shops in our Phoenix directory publish a service-call fee that is waived or applied if you approve the work — ask about the current policy when you book.</p>
      <h2>Questions worth asking</h2>
      <ol>
        <li>What failed, and is the part still available?</li>
        <li>What will the repair cost, including labor, and what is warranted after the visit?</li>
        <li>How old is the appliance, and has it needed other repairs recently?</li>
        <li>If you replaced it, what would a comparable new unit cost, installed?</li>
        <li>Would a newer model use meaningfully less energy in your home?</li>
      </ol>
      <h2>A common rule of thumb — and its limits</h2>
      <p>Consumer writers often suggest repairing when the quote is well under half the price of a comparable new appliance, and replacing when the machine is near the end of a typical life and the repair is a large share of that replacement cost. Treat this as a starting point, not a law. A $400 repair on a well-maintained refrigerator can be sensible; the same bill on a washer that has already failed twice this year may not be.</p>
      <p>We are not publishing made-up “average repair costs in Phoenix.” Those figures vary by brand, part, and travel, and they go stale. Use the quote in your hand.</p>
      <h2>When replacement is often the better path</h2>
      <ul>
        <li>The technician cannot get a part, or the appliance uses a refrigerant or control system that is no longer practical to service.</li>
        <li>The box, tub, or cabinet itself is rusted or damaged.</li>
        <li>You already have a written diagnosis, and stacking another major repair on a short remaining life does not make sense to you.</li>
      </ul>
      <h2>If the refrigerator already failed</h2>
      <p>Keep the doors closed. Food-safety time limits depend on the appliance, how full it is, and the room temperature — which in a Phoenix summer can be unforgiving. Use a thermometer if you have one, and follow current food-safety guidance from a public-health source such as FoodSafety.gov or USDA, not a memory of a rule of thumb.</p>
      <h2>Talk to a local tech</h2>
      <p>If you are in the Valley, browse the <a href="PHOENIX_HREF">Phoenix directory</a> and call a shop that lists your appliance. Ask for a diagnosis and a written or on-site price before you decide.</p>
    </article>
    """
    body = body.replace("PHOENIX_HREF", href(page, "/phoenix/"))
    insert = (
        aff_box(page, "parts-common")
        + aff_box(page, "replace-appliance")
        + aff_box(page, "warranty-protect")
        + aff_box(page, "tools")
    )
    body = body.replace("    </article>", insert + "    </article>", 1)
    desc = "How to decide whether to repair or replace a refrigerator, washer, dryer, or other home appliance — starting with a real diagnosis."
    faq = ld_json({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": "Should I repair or replace a broken appliance?",
             "acceptedAnswer": {"@type": "Answer", "text": "Get a diagnosis first. Compare the quoted repair with the cost of a comparable new machine, the appliance's age, and how often it has already failed. A common rule of thumb is to repair when the quote is well under half the replacement cost, but that is only a starting point."}},
            {"@type": "Question", "name": "Why doesn't this guide list average repair prices?",
             "acceptedAnswer": {"@type": "Answer", "text": "Average prices vary by brand, part, and travel and go stale quickly. This directory does not invent prices. Use the quote a technician gives you."}},
        ],
    })
    crumbs = [("/", "Home"), ("/guides/repair-vs-replace/", "Repair vs. replace")]
    write_page(page, layout(page, "Repair or replace an appliance? — Indie Appliance Repair", desc, body, "guides", crumbs, extra_head=faq))


def page_compare() -> None:
    page = "compare/independent-vs-chains/index.html"
    body = f"""
    <article class="prose hero">
      <p class="kicker">Comparison</p>
      <h1>Independent appliance techs vs. Sears, Mr. Appliance, and lead marketplaces</h1>
      <p class="lede">This is a comparison of how you hire someone, not a claim that every independent is better than every national brand. Quality varies in both groups. Confirm licensing, insurance, and price with the company you call.</p>
      <h2>What is different</h2>
      <table>
        <thead><tr><th></th><th>Independent / local shop</th><th>National chain or lead marketplace</th></tr></thead>
        <tbody>
          <tr><th scope="row">Who you call</th><td>The shop or owner, using the number they publish.</td><td>A national or regional dispatch line, or a form that may be sold as a lead to one or more providers.</td></tr>
          <tr><th scope="row">Who shows up</th><td>Often the owner or a technician employed by that local business. Ask if you want to be sure.</td><td>May be an employee, a franchisee, or a subcontractor, depending on the brand and market.</td></tr>
          <tr><th scope="row">Price and warranty</th><td>Set by that shop. Several Phoenix listings publish a service-call fee and whether it is waived with a repair.</td><td>Set by the chain, franchise, or the individual provider who buys the lead. Terms vary; read them for the company that actually visits.</td></tr>
          <tr><th scope="row">Accountability</th><td>A local reputation and, in Arizona, a Registrar of Contractors license when the work requires one. Some shops publish their ROC number.</td><td>Brand policies plus whatever license the visiting company holds. A familiar logo is not the same thing as a local license check.</td></tr>
        </tbody>
      </table>
      <h2>About Angi, Thumbtack, and similar platforms</h2>
      <p>These can be a way to find names, but they are usually paid lead or advertising products. The technician may have paid to be introduced to you. That does not make them unqualified; it does mean you should still interview the shop as if you had found them yourself — ask who is coming, what the visit costs, and how warranty work is handled.</p>
      <h2>Factory service and luxury brands</h2>
      <p>Some independents in our Phoenix list say they are factory-authorized or preferred providers for brands such as Viking, Sub-Zero, or U-Line. That is the shop's claim, sourced from its website. Manufacturer factory service is a different path and can be the right one if the appliance is in warranty. We are not a manufacturer directory.</p>
      <h2>Find a Phoenix independent</h2>
      <p><a href="{e(href(page, "/phoenix/"))}">Browse the Phoenix directory</a> and call a shop that lists your appliance. Or read how we decide <a href="{e(href(page, "/guides/repair-vs-replace/"))}">whether to repair or replace</a>.</p>
      {aff_box(page, "parts-common")}
      {aff_box(page, "tools")}
    </article>
    """
    desc = "How hiring an independent appliance technician differs from calling a national chain or submitting a form on a lead marketplace."
    crumbs = [("/", "Home"), ("/compare/independent-vs-chains/", "Independent vs. chains")]
    write_page(page, layout(page, "Independent appliance techs vs. Sears, Mr. Appliance, and Angi", desc, body, "compare", crumbs))


def page_subzero() -> None:
    page = "best/sub-zero/index.html"
    mentioned = []
    for l in LISTINGS:
        brands = [b.lower() for b in (l.get("brands") or [])]
        note = (l.get("brandsNote") or "").lower()
        facts = " ".join(l.get("facts") or []).lower()
        if "sub-zero" in brands or "sub zero" in note or "sub-zero" in note or "sub-zero" in facts:
            mentioned.append(l)
    cards = "".join(listing_card(page, l) for l in mentioned)
    body = f"""
    <header class="hero">
      <p class="kicker">Brand page · not a ranked “best of”</p>
      <h1>Phoenix shops that list Sub-Zero service</h1>
      <p class="lede">These {len(mentioned)} listings mentioned Sub-Zero on a website we opened. That is not a ranking, an endorsement, or proof of factory authorization. Some shops specialize in luxury brands; others list Sub-Zero among many major brands. Confirm authorization and parts access when you call.</p>
    </header>
    <p class="note">We titled this section carefully on purpose. “Best for Sub-Zero” searchers often want a specialist, but we will not invent a winner. If a shop claims factory authorization or exclusive specialty, that claim is quoted on its profile and sourced.</p>
    <section class="section">
      <h2>Listings that mention Sub-Zero</h2>
      <div class="grid grid-2">{cards}</div>
    </section>
    {sponsorship_box(page, "Sub-Zero")}
    {aff_box(page, "parts-common", extra_intro=(
        "Specialty brands sometimes need OEM or specialty parts. These general parts catalogs are reserved "
        "affiliate slots — not a claim that they stock every Sub-Zero part."
    ))}
    """
    desc = (
        f"{len(mentioned)} independent or locally based Phoenix-metro appliance shops whose own websites "
        "mention Sub-Zero service. Not a ranked list."
    )
    schema = ld_json({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Phoenix appliance shops that list Sub-Zero service",
        "numberOfItems": len(mentioned),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": l["name"], "url": listing_url(l)}
            for i, l in enumerate(mentioned)
        ],
    })
    crumbs = [("/", "Home"), ("/best/sub-zero/", "Shops that list Sub-Zero")]
    write_page(page, layout(page, "Phoenix shops that list Sub-Zero service — Indie Appliance Repair", desc, body, "guides", crumbs, extra_head=schema))


def page_get_listed() -> None:
    page = "get-listed/index.html"
    body = """
    <header class="hero">
      <p class="kicker">For technicians and shop owners</p>
      <h1>Get listed, or ask about a featured listing</h1>
      <p class="lede">If you are an independent or locally owned appliance repair business serving a city we cover, we want accurate information on this site. Featured placements, if we offer them, will be clearly labeled and will not bury or hide other shops.</p>
    </header>
    <div class="todo">
      <strong>TODO — no form backend yet.</strong> Submitting this form does not send a message and does not create a listing. We still need a form endpoint (and a public contact email once a domain is live). Until then, treat this page as a preview of what we will collect.
    </div>
    <form id="get-listed-form" action="#" method="post" novalidate>
      <label>Your name <input type="text" name="name" autocomplete="name" required></label>
      <label>Business name <input type="text" name="business" required></label>
      <label>City or metro you serve <input type="text" name="city" required></label>
      <label>Phone <input type="tel" name="phone" autocomplete="tel" required></label>
      <label>Email <input type="email" name="email" autocomplete="email" required></label>
      <label>Website <input type="url" name="website" placeholder="https://"></label>
      <label>Appliances and brands you service, and anything we should verify
        <textarea name="message" required></textarea>
      </label>
      <label class="check"><input type="checkbox" name="featured" value="yes"> I would also like to hear about a clearly labeled featured listing when that program is ready.</label>
      <label class="check"><input type="checkbox" name="specialist" value="yes"> I would also like to hear about a labeled brand-specialist sponsorship (for example Sub-Zero, Wolf, or another brand I service).</label>
      <button class="btn btn-primary" type="submit">Submit request (preview only)</button>
    </form>
    <p id="form-status" class="form-status" tabindex="-1">This form is a placeholder and was not sent. TODO: connect a form backend before the site is public. Nothing in this preview is a paid placement or a commitment to list a business.</p>
    <section class="section prose">
      <h2>What we will and will not do</h2>
      <ul>
        <li>We will verify facts against a public page or a document you provide before publishing.</li>
        <li>We will not invent reviews, ratings, or prices for you.</li>
        <li>A featured listing, if offered, will be marked as paid or featured. It will not be the only way to appear in the directory.</li>
        <li>A brand-specialist sponsorship, if offered, will be labeled as a paid sponsorship and will not be presented as a ranked “best of.”</li>
      </ul>
      <h2>Proposed products (not a live offer)</h2>
      <p>These prices are a proposal for when the site is public and the form works. Nothing on this preview is a contract, and no placements have been sold.</p>
      <ul>
        <li>Free basic listing.</li>
        <li>Founding featured listing on a city or category page: $39 per month or $349 per year, rate locked for 12 months, limited spots per city.</li>
        <li>Brand-specialist sponsorship (for example a labeled Sub-Zero specialist slot): $59–$79 per month or $499–$699 per year, one or two spots per brand page.</li>
        <li>Exclusive pay-per-call or pay-per-lead would come later, only after call tracking or a lead form is in place.</li>
      </ul>
    </section>
    """
    desc = "Request a listing in the Indie Appliance Repair directory, or ask about a clearly labeled featured placement. Form backend not connected yet."
    crumbs = [("/", "Home"), ("/get-listed/", "Get listed")]
    write_page(page, layout(page, "Get listed or request a featured listing — Indie Appliance Repair", desc, body, "get-listed", crumbs))


def page_disclosure() -> None:
    page = "disclosure/index.html"
    body = f"""
    <article class="prose hero">
      <p class="kicker">Legal</p>
      <h1>Affiliate and advertising disclosure</h1>
      <p id="affiliate-placeholders"><strong>As of {e(site.get("accessedDate") or TODAY)}, this site has no active affiliate tracking links, no paid featured listings, and no sponsored posts.</strong> We do not currently earn commissions from any retailer or warranty company.</p>
      <h2>Placeholder slots</h2>
      <p>Some guide, comparison, “best for,” and city-and-appliance pages include clearly labeled “Affiliate placement” boxes. Those boxes reserve space for parts, tools, replacement-appliance, or warranty links. Until a program is approved and a tracking URL is added to our link configuration, those buttons point here — not to a merchant — and use <code>rel="sponsored nofollow"</code>. They are not live affiliate links.</p>
      <p>When a program is approved, we will turn on the tracking URL, keep the sponsored label, and update this page so it lists the programs actually in use.</p>
      <h2>What we may do later</h2>
      <p>Priority placements, if approved, are for higher-commission parts catalogs (for example AppliancePartsPros, RepairClinic, or Sears PartsDirect), then tools, then replacement-appliance retailers, then warranty or product-protection plans. Warranty links, if used, will stay clearly separated from the advice to call a local technician, because a warranty company may dispatch its own network.</p>
      <h2>Featured listings and sponsorships</h2>
      <p>We may later offer shops a paid, clearly labeled featured placement on a city or category page, or a labeled brand-specialist sponsorship (for example on a Sub-Zero page). Featured and sponsored listings will not be the only way to appear in the directory, and we will not invent ratings to justify a paid slot. No such placements have been sold.</p>
      <h2>Editorial standard</h2>
      <p>Listing facts come from sources recorded on each profile. We do not sell the right to hide a competitor or to publish a fake review. See <a href="{e(href(page, "/about/"))}">About &amp; method</a>.</p>
    </article>
    """
    desc = "Affiliate and advertising disclosure for Indie Appliance Repair. Placeholder slots exist; no live tracking links or paid listings as of this build."
    crumbs = [("/", "Home"), ("/disclosure/", "Affiliate disclosure")]
    write_page(page, layout(page, "Affiliate and advertising disclosure — Indie Appliance Repair", desc, body, "home", crumbs))


def page_about() -> None:
    page = "about/index.html"
    body = f"""
    <article class="prose hero">
      <p class="kicker">About</p>
      <h1>About Indie Appliance Repair</h1>
      <p class="lede">We are building a small, useful directory of independent appliance technicians — starting in Phoenix, Arizona — so homeowners can call a shop directly instead of entering a lead marketplace.</p>
      <h2>Launch metro</h2>
      <p>Phoenix is first: a large, year-round repair market where heat stresses refrigerators and ice makers, with many documented owner-operated shops and no strong consumer directory that organizes independents by city, appliance, and brand. We plan to finish Phoenix depth, then add cities one at a time.</p>
      <h2>How we research a listing</h2>
      <ul>
        <li>We open the business website (or another public page) and record the URL and the date.</li>
        <li>We include only facts stated there: name, phone, website, address, hours, service area, appliances, brands, and published fees or license numbers.</li>
        <li>We do not invent ratings, reviews, prices, or coverage areas. If a street address was not on the official site, we say so.</li>
        <li>National chains and lead-mill landing pages are out of scope for “independent” listings. Multi-office Arizona companies can still appear if they are local businesses rather than a national franchise; the profile will say so.</li>
      </ul>
      <p>This first batch includes {len(LISTINGS)} Phoenix-metro businesses, researched on {e(site.get("accessedDate") or TODAY)}.</p>
      <h2>Get in touch</h2>
      <p>Use the <a href="{e(href(page, "/get-listed/"))}">Get listed</a> page to request an addition or a correction. The form is a placeholder until a backend and public email are connected (TODO).</p>
    </article>
    """
    desc = "How Indie Appliance Repair researches listings, why Phoenix is the launch metro, and what we will not invent."
    crumbs = [("/", "Home"), ("/about/", "About")]
    write_page(page, layout(page, "About Indie Appliance Repair", desc, body, "home", crumbs))


def page_404() -> None:
    page = "404.html"
    body = f"""
    <header class="hero">
      <p class="kicker">404</p>
      <h1>That page is not here</h1>
      <p class="lede">The link may be outdated, or the city page has not been built yet. Try the Phoenix directory or the homepage.</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="{e(href(page, "/phoenix/"))}">Phoenix directory</a>
        <a class="btn btn-ghost" href="{e(href(page, "/"))}">Home</a>
      </div>
    </header>
    """
    write_page(page, layout(page, "Page not found — Indie Appliance Repair", "That page does not exist on Indie Appliance Repair.", body, "home"))


SITEMAP_PATHS = []


def remember(page_file: str) -> None:
    if page_file == "index.html":
        SITEMAP_PATHS.append("/")
    elif page_file == "404.html":
        return
    else:
        SITEMAP_PATHS.append("/" + str(Path(page_file).parent).replace("\\", "/") + "/")


def write_robots_and_sitemap() -> None:
    origin = (site.get("canonicalOrigin") or "").rstrip("/")
    sitemap_ref = f"{origin}/sitemap.xml" if origin else "/sitemap.xml"
    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        "# TODO: set canonicalOrigin in data/site.json so Sitemap can be an absolute URL.\n"
        f"Sitemap: {sitemap_ref}\n",
        encoding="utf-8",
    )
    urls = []
    for path in SITEMAP_PATHS:
        loc = f"{origin}{path}" if origin else path
        urls.append(f"  <url><loc>{escape(loc)}</loc><lastmod>{TODAY}</lastmod></url>")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")


def write_cname() -> None:
    """Write a GitHub Pages CNAME file when canonicalOrigin is a custom domain."""
    origin = (site.get("canonicalOrigin") or "").rstrip("/")
    if "://" not in origin:
        return
    host = origin.split("://", 1)[1].split("/")[0]
    if not host or host.endswith(".github.io"):
        return
    (ROOT / "CNAME").write_text(host + "\n", encoding="utf-8")


def main() -> None:
    # Keep research/planning files; regenerate HTML output dirs as needed.
    page_home(); remember("index.html")
    page_phoenix(); remember("phoenix/index.html")
    for app in appliances:
        if listings_for_appliance(app["slug"]):
            page_appliance(app)
            remember(f"phoenix/{app['pathSegment']}/index.html")
    for listing in LISTINGS:
        page_profile(listing)
        remember(f"phoenix/techs/{listing['slug']}/index.html")
    page_guide(); remember("guides/repair-vs-replace/index.html")
    page_compare(); remember("compare/independent-vs-chains/index.html")
    page_subzero(); remember("best/sub-zero/index.html")
    page_get_listed(); remember("get-listed/index.html")
    page_disclosure(); remember("disclosure/index.html")
    page_about(); remember("about/index.html")
    page_404()
    write_robots_and_sitemap()
    write_cname()
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {len(SITEMAP_PATHS)} indexable pages + 404. Listings: {len(LISTINGS)}")


if __name__ == "__main__":
    main()
