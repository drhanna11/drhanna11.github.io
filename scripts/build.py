#!/usr/bin/env python3
"""Generate static HTML, sitemap.xml, and robots.txt from data/*.json."""
from __future__ import annotations

import json
import shutil
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import quote

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


def live_metros() -> list[dict]:
    return [c for c in cities if c.get("status") == "live"]


def listings_for_metro(slug: str) -> list[dict]:
    return [l for l in LISTINGS if l.get("citySlug") == slug]


def listings_for_appliance(slug: str, metro_slug: str | None = None) -> list[dict]:
    rows = [l for l in LISTINGS if slug in l.get("appliances", [])]
    if metro_slug:
        rows = [l for l in rows if l.get("citySlug") == metro_slug]
    return rows


def listing_serves(listing: dict, names: list[str]) -> bool:
    names_l = {n.lower() for n in names}
    areas = [s.lower() for s in (listing.get("serviceAreas") or [])]
    addr = ((listing.get("address") or {}).get("city") or "").lower()
    if addr and addr in names_l:
        return True
    return any(a in names_l for a in areas)


def listings_for_subcity(metro_slug: str, subcity: dict) -> list[dict]:
    names = subcity.get("match") or [subcity["name"]]
    return [l for l in listings_for_metro(metro_slug) if listing_serves(l, names)]


def metro_nav_label(metro: dict) -> str:
    if metro["slug"] == "riverside-county":
        return "Riverside County"
    return metro["name"]


def registration_html(page_file: str, metro: dict) -> str:
    note = metro.get("registrationNote")
    if not note:
        return ""
    search = metro.get("registrationSearchUrl") or "https://search.dca.ca.gov/"
    guide = metro.get("registrationGuideUrl") or "https://www.bhgs.dca.ca.gov/consumers/ear.html"
    return (
        f'<p class="note"><strong>California registration.</strong> {e(note)} '
        f'<a href="{e(search)}" rel="noopener noreferrer">Search BHGS registrations</a>. '
        f'<a href="{e(guide)}" rel="noopener noreferrer">BHGS consumer guide</a>.</p>'
    )


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
    items = [("/", "Home", "home")]
    for metro in live_metros():
        items.append((f"/{metro['slug']}/", metro_nav_label(metro), metro["slug"]))
    items.extend([
        ("/guides/repair-vs-replace/", "Guides", "guides"),
        ("/compare/independent-vs-chains/", "Compare", "compare"),
        ("/get-listed/", "Get listed", "get-listed"),
    ])
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
    metro_links = "".join(
        '<li><a href="' + e(href(page_file, f"/{m['slug']}/")) + '">' + e(metro_nav_label(m)) + " directory</a></li>"
        for m in live_metros()
    )
    return f"""<footer class="site-footer">
  <div class="wrap footer-grid">
    <div>
      <h2>Indie Appliance Repair</h2>
      <p>A small directory of independent and locally owned appliance technicians. We publish only facts we can source, and we never invent ratings, reviews, or prices.</p>
    </div>
    <div>
      <h2>Explore</h2>
      <ul>
        {metro_links}
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
    metro = listing.get("citySlug") or "phoenix"
    return f"/{metro}/techs/{listing['slug']}/"


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
        "addressRegion": a.get("state") or (CITY_BY_SLUG.get(listing.get("citySlug") or "", {}) or {}).get("state") or "US",
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
        "areaServed": listing.get("serviceAreas") or [CITY_BY_SLUG.get(listing.get("citySlug") or "", {}).get("metroName") or "United States"],
    }
    if listing.get("email"):
        data["email"] = listing["email"]
    return data


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

PHOENIX_INTRO = {
    "refrigerator": "In the Phoenix metro, a refrigerator that stops cooling is an emergency. Valley summers put a heavy load on compressors, and food can be lost quickly once the box warms up. The shops below are ones whose own sites mention refrigerator or freezer repair. Call early, keep the doors closed, and ask about same-day availability — we do not track live schedules.",
    "washer": "Won't drain, spin, or fill, or water on the floor — a washer that stops can pile up laundry in a day. The shops below mention washer repair on a source we opened.",
    "dryer": "No heat, long dry times, or a drum that will not turn. Leave gas and electrical dryer repairs to a trained technician. The shops below mention dryer repair on a source we opened.",
    "dishwasher": "Leaks, standing water, and dishes that will not come clean are the usual reasons people look for dishwasher repair. This page lists Phoenix-metro shops that mention dishwashers on their own sites.",
    "oven-range": "Won't heat, a burner that will not light, or a cooktop fault on a gas or electric range. The shops below mention oven, range, stove, or cooktop repair on a source we opened.",
    "microwave": "No heat, a turntable that will not spin, or a built-in unit that has shut down. The shops below mention microwave repair on a source we opened.",
    "ice-maker": "Standalone ice machines and in-fridge ice makers are a frequent request in the Phoenix heat. This page lists shops that specifically mentioned ice maker or ice machine repair. Confirm residential vs. commercial coverage when you call.",
    "freezer": "Frost buildup, temperature swings, or a freezer that has stopped getting cold. The shops below mention freezer repair on a source we opened.",
}

RIVERSIDE_INTRO = {
    "refrigerator": "Inland Empire and Coachella Valley summers are hard on refrigerators. A box that stops cooling can lose food quickly, especially in Palm Springs, Indio, or a hot mid-county city like Hemet. The shops below are ones whose own sites mention refrigerator repair. Call early, keep the doors closed, and ask about same-day availability — we do not track live schedules.",
    "washer": "A washer that will not drain, spin, or fill can pile up laundry in a day. This page lists Riverside County shops that mention washer repair on a source we opened.",
    "dryer": "No heat, long dry times, or a drum that will not turn. Leave gas and electrical dryer repairs to a trained technician. Several county shops also mention dryer vent cleaning; confirm that service when you call. The shops below mention dryer repair on a source we opened.",
    "dishwasher": "Leaks, standing water, and dishes that will not come clean are the usual reasons people look for dishwasher repair. This page lists Riverside County shops that mention dishwashers on their own sites.",
    "oven-range": "Won't heat, a burner that will not light, or a cooktop fault on a gas or electric range. The Coachella Valley in particular has many built-in and professional-style ranges; confirm brand coverage when you call. The shops below mention oven, range, stove, or cooktop repair on a source we opened.",
    "microwave": "No heat, a turntable that will not spin, or a built-in unit that has shut down. The shops below mention microwave repair on a source we opened.",
    "ice-maker": "Standalone ice machines and in-fridge ice makers are a frequent request in Coachella Valley and Inland Empire heat. This page lists shops that specifically mentioned ice maker or ice machine repair. Confirm residential vs. commercial coverage when you call.",
    "freezer": "Frost buildup, temperature swings, or a freezer that has stopped getting cold — another high-urgency job in a desert or inland summer. The shops below mention freezer repair on a source we opened.",
}


def appliance_intro(metro: dict, app: dict) -> str:
    if metro["slug"] == "riverside-county":
        return RIVERSIDE_INTRO.get(app["slug"] or "", app.get("blurb") or "")
    if metro["slug"] == "phoenix":
        return PHOENIX_INTRO.get(app["slug"] or "", app.get("blurb") or "")
    return app.get("blurb") or ""


def page_home() -> None:
    page = "index.html"
    live = live_metros()

    metro_cta = []
    for m in live:
        n = len(listings_for_metro(m["slug"]))
        metro_cta.append(
            f'<a class="btn {"btn-primary" if not metro_cta else "btn-ghost"}" href="{e(href(page, f"/{m["slug"]}/"))}">'
            f'Browse {e(metro_nav_label(m))} techs ({n})</a>'
        )

    appliance_sections = []
    for m in live:
        cards = []
        for app in appliances:
            n = len(listings_for_appliance(app["slug"], m["slug"]))
            if not n:
                continue
            url = href(page, f"/{m['slug']}/{app['pathSegment']}/")
            cards.append(
                f"""<a class="card cat-card" href="{e(url)}">
            <h3>{e(app["name"])} repair</h3>
            <p>{e(app.get("blurb") and app["name"] + " repair in " + metro_nav_label(m) + "." or "")}</p>
            <p class="meta">{n} {e(metro_nav_label(m))} listing{"s" if n != 1 else ""} so far</p>
          </a>"""
            )
        if cards:
            appliance_sections.append(
                f'<h3 class="metro-cats">{e(metro_nav_label(m))}</h3><div class="grid grid-2">{"".join(cards)}</div>'
            )

    city_cards = []
    for c in cities:
        if c.get("status") == "live":
            n = len(listings_for_metro(c["slug"]))
            city_cards.append(
                f"""<a class="city-card" href="{e(href(page, f'/{c["slug"]}/'))}">
          <h3>{e(c.get("metroName") or c["name"])}</h3>
          <p>{e(c.get("summary") or "")}</p>
          <p class="meta">{n} listing{"s" if n != 1 else ""} · Live directory</p>
        </a>"""
            )
        else:
            city_cards.append(
                f"""<div class="city-card planned">
          <h3>{e(c.get("metroName") or c["name"])}</h3>
          <p>{e(c.get("summary") or "Planned expansion.")}</p>
          <p class="meta">Planned</p>
        </div>"""
            )

    body = f"""
    <header class="hero">
      <p class="kicker">Independent technician directory</p>
      <h1>Find an independent technician. Skip the lead mill.</h1>
      <p class="lede">A growing list of owner-operated and locally owned shops in Phoenix, Arizona, and Riverside County, California — the alternative to Angi, Sears, and Mr. Appliance. We list names, phones, service areas, and source URLs. We do not invent ratings or prices.</p>
      <div class="hero-actions">
        {"".join(metro_cta)}
      </div>
    </header>
    <section class="section">
      <h2>Repair categories</h2>
      <p class="lede">Each area has its own refrigerator, washer, dryer, and other category pages, built only from shops that mention that appliance on a source we opened.</p>
      {"".join(appliance_sections)}
    </section>
    <section class="section">
      <h2>Areas we cover</h2>
      <p class="lede">We go deep on one area at a time, then expand. Phoenix and Riverside County are live; other metros are planned.</p>
      <div class="grid grid-2">{"".join(city_cards)}</div>
    </section>
    <section class="section">
      <h2>Guides and comparisons</h2>
      <div class="grid grid-2">
        <a class="card cat-card" href="{e(href(page, "/guides/repair-vs-replace/"))}">
          <h3>Repair vs. replace</h3>
          <p>Get a diagnosis first, then compare the quoted repair with the cost and remaining life of a new machine.</p>
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
        "Find independent and locally owned appliance repair technicians in Phoenix, Arizona, "
        "and Riverside County, California. Call shops directly — not a lead mill."
    )
    schema = ld_json({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": site["name"],
        "description": site["description"],
        "about": "Independent appliance repair technician directory",
        "url": (site.get("canonicalOrigin") or "").rstrip("/") or None,
    })
    item_elements = []
    pos = 1
    for m in live:
        for app in appliances:
            if listings_for_appliance(app["slug"], m["slug"]):
                item_elements.append({
                    "@type": "ListItem",
                    "position": pos,
                    "name": f"{app['name']} repair in {metro_nav_label(m)}",
                    "url": f"/{m['slug']}/{app['pathSegment']}/",
                })
                pos += 1
    itemlist = ld_json({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Appliance repair categories",
        "itemListElement": item_elements,
    })
    # schema.org url: None would be invalid; strip if empty
    if schema and '"url": null' in schema:
        schema = schema.replace(', "url": null', "")
    write_page(page, layout(page, "Indie Appliance Repair — Independent techs in Phoenix and Riverside County", desc, body, "home", extra_head=schema + itemlist))


def page_metro(metro: dict) -> None:
    page = f"{metro['slug']}/index.html"
    shops = listings_for_metro(metro["slug"])
    label = metro_nav_label(metro)
    place = metro.get("metroName") or f"{metro['name']}, {metro.get('stateName') or metro.get('state', '')}"

    app_links = []
    for app in appliances:
        n = len(listings_for_appliance(app["slug"], metro["slug"]))
        if n:
            app_links.append(
                f'<a href="{e(href(page, f"/{metro["slug"]}/{app["pathSegment"]}/"))}">{e(app["name"])} ({n})</a>'
            )
    app_nav = (", ".join(app_links) + ".") if app_links else "Category pages appear when at least one shop mentions that appliance."

    city_cards = []
    for sub in metro.get("cities") or []:
        n = len(listings_for_subcity(metro["slug"], sub))
        city_cards.append(
            f"""<a class="city-card" href="{e(href(page, f'/{metro["slug"]}/{sub["slug"]}/'))}">
          <h3>{e(sub["name"])}</h3>
          <p>{e((sub.get("blurb") or "")[:180])}{"…" if len(sub.get("blurb") or "") > 180 else ""}</p>
          <p class="meta">{n} listing{"s" if n != 1 else ""} naming this area</p>
        </a>"""
        )
    cities_section = ""
    if city_cards:
        cities_section = f"""
    <section class="section">
      <h2>Cities and areas</h2>
      <p>These pages list only shops that published that city (or a named nearby community) on a source we opened.</p>
      <div class="grid grid-2">{"".join(city_cards)}</div>
    </section>"""

    lede_extra = metro.get("summary") or ""
    if metro["slug"] == "phoenix":
        heading = "Independent appliance repair in Phoenix, Arizona"
        lede = (
            f"A directory of {len(shops)} independent or locally based shops serving Phoenix and the Valley of the Sun. "
            "We gathered these from the businesses' own websites. Always call to confirm that they still serve your ZIP, and that the phone number is current."
        )
        why = (
            "Phoenix is our first metro because it is a large, year-round repair market — desert heat puts extra load on refrigerators, "
            "ice makers, and laundry equipment — and because we could document a deep bench of owner-operated and locally owned shops. "
            "Suburb pages (Mesa, Chandler, Scottsdale, and others) are planned next, and Riverside County, California, is now live as a second market."
        )
        faq_coverage = "Many Valley shops cover several cities. Each profile lists only the service areas named on a source we opened. If your city is not listed, still call — coverage can be broader than the website copy, or it may have changed."
        faq_only = "No. This is a researched starting set, not a complete census. If you run or know an independent shop that should be here, use the Get listed page."
        schema_name = "Independent appliance repair in Phoenix, AZ"
    else:
        heading = "Independent appliance repair in Riverside County, California"
        lede = (
            f"A directory of {len(shops)} independent or locally based shops serving Riverside County — from Corona and the city of Riverside "
            "through Temecula, Hemet, and the Coachella Valley. We gathered these from the businesses' own websites or other public pages we recorded. "
            "Always call to confirm that they still serve your ZIP, and that the phone number is current."
        )
        why = lede_extra or (
            "Riverside County is our second market: a large Inland Empire and desert-valley area where summer heat stresses refrigerators and ice makers, "
            "with a documented mix of owner-operated and long-running family shops."
        )
        faq_coverage = (
            "Many shops cover several cities, and some west-county businesses also drive into San Bernardino or Orange County. "
            "Each profile lists only the service areas named on a source we opened. If your city is not listed, still call — coverage can be broader than the website copy, or it may have changed."
        )
        faq_only = (
            "No. This is a researched starting set, not a complete census of every independent in the county. "
            "Some cities, especially San Jacinto, still have few shops that published that city by name. "
            "If you run or know an independent shop that should be here, use the Get listed page."
        )
        schema_name = "Independent appliance repair in Riverside County, CA"

    cards = "".join(listing_card(page, l) for l in shops)
    body = f"""
    <header class="hero">
      <p class="kicker">{e(place)}</p>
      <h1>{e(heading)}</h1>
      <p class="lede">{e(lede)}</p>
    </header>
    {registration_html(page, metro)}
    <p class="note">{e(why)}</p>
    <p>Browse by appliance: {app_nav}</p>
    {cities_section}
    <section class="section">
      <h2>{len(shops)} shops in this directory</h2>
      <div class="grid grid-2">{cards}</div>
    </section>
    <section class="section">
      <h2>{e(label)} appliance repair questions</h2>
      <details><summary>Do these shops cover my city?</summary>
      <p>{e(faq_coverage)}</p></details>
      <details><summary>Are these the only independent techs in {e(label)}?</summary>
      <p>{e(faq_only)}</p></details>
    </section>
    """
    desc = (
        f"Independent appliance repair technicians in {place}. "
        "Call shops directly — not a lead mill."
    )
    if metro["slug"] == "phoenix":
        desc = (
            "Independent appliance repair technicians serving Phoenix, Mesa, Scottsdale, Chandler, Gilbert, Tempe, and the rest of the Valley."
        )
    schema = ld_json({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": schema_name,
        "numberOfItems": len(shops),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": l["name"], "url": listing_url(l)}
            for i, l in enumerate(shops)
        ],
    })
    faq = ld_json({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": "Do these shops cover my city?",
             "acceptedAnswer": {"@type": "Answer", "text": faq_coverage}},
            {"@type": "Question", "name": f"Are these the only independent techs in {label}?",
             "acceptedAnswer": {"@type": "Answer", "text": faq_only}},
        ],
    })
    crumbs = [("/", "Home"), (f"/{metro['slug']}/", label)]
    write_page(page, layout(
        page,
        f"{schema_name} — Indie Appliance Repair",
        desc,
        body,
        metro["slug"],
        crumbs,
        extra_head=schema + faq,
    ))


def page_subcity(metro: dict, subcity: dict) -> None:
    page = f"{metro['slug']}/{subcity['slug']}/index.html"
    shops = listings_for_subcity(metro["slug"], subcity)
    label = metro_nav_label(metro)
    name = subcity["name"]
    is_region = bool(subcity.get("isRegion"))
    kind = "area" if is_region else "city"
    thin = ""
    if len(shops) <= 2:
        thin = (
            f'<p class="note"><strong>Thin on published names.</strong> Only {len(shops)} shop'
            f'{"s" if len(shops) != 1 else ""} in this directory published {e(name)} on a source we opened. '
            f"A nearby city page, or the <a href=\"{e(href(page, f'/{metro['slug']}/'))}\">{e(label)} directory</a>, "
            "may have shops that will still drive to you — call and ask.</p>"
        )
    cards = "".join(listing_card(page, l) for l in shops) or "<p>No shops in this directory have published this city yet.</p>"
    app_links = []
    for app in appliances:
        n = len([l for l in shops if app["slug"] in l.get("appliances", [])])
        if n:
            app_links.append(
                f'<a href="{e(href(page, f"/{metro["slug"]}/{app["pathSegment"]}/"))}">{e(app["name"])} ({n})</a>'
            )
    app_nav = ("Related county category pages: " + ", ".join(app_links) + ".") if app_links else ""
    body = f"""
    <header class="hero">
      <p class="kicker">{e(label)}</p>
      <h1>Independent appliance repair in {e(name)}</h1>
      <p class="lede">{e(subcity.get("blurb") or f"Shops in the {label} directory whose own sources name {name}.")}</p>
    </header>
    {registration_html(page, metro)}
    {thin}
    <p><a href="{e(href(page, f'/{metro["slug"]}/'))}">All {e(label)} shops</a></p>
    <p>{app_nav}</p>
    <section class="section">
      <h2>{len(shops)} shop{"s" if len(shops) != 1 else ""} that list{"s" if len(shops)==1 else ""} {e(name)}</h2>
      <div class="grid grid-2">{cards}</div>
    </section>
    """
    desc = (
        f"Independent appliance repair in {name}, Riverside County, California. "
        + (
            f"{len(shops)} shops in this directory published this {kind} on a source we opened."
            if len(shops) != 1
            else f"1 shop in this directory published this {kind} on a source we opened."
        )
    )
    schema = ld_json({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Independent appliance repair in {name}, CA",
        "numberOfItems": len(shops),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": l["name"], "url": listing_url(l)}
            for i, l in enumerate(shops)
        ],
    })
    crumbs = [("/", "Home"), (f"/{metro['slug']}/", label), (f"/{metro['slug']}/{subcity['slug']}/", name)]
    write_page(page, layout(
        page,
        f"Appliance repair in {name}, CA — independent techs",
        desc,
        body,
        metro["slug"],
        crumbs,
        extra_head=schema,
    ))


def page_appliance(metro: dict, app: dict) -> None:
    shops = listings_for_appliance(app["slug"], metro["slug"])
    page = f"{metro['slug']}/{app['pathSegment']}/index.html"
    label = metro_nav_label(metro)
    place = metro.get("metroName") or label
    cards = "".join(listing_card(page, l) for l in shops)
    intro = appliance_intro(metro, app)
    body = f"""
    <header class="hero">
      <p class="kicker">{e(place)}</p>
      <h1>{e(app["name"])} repair in {e(label)}</h1>
      <p class="lede">{e(intro)}</p>
    </header>
    {registration_html(page, metro)}
    <p>
      <a href="{e(href(page, f"/{metro["slug"]}/"))}">All shops</a>
    </p>
    <section class="section">
      <h2>{len(shops)} shop{"s" if len(shops) != 1 else ""} that mention {e(app["name"].lower())} repair</h2>
      <div class="grid grid-2">{cards}</div>
    </section>
    {aff_box(page, "parts-common")}
    """
    desc = (
        f"Independent {app['name'].lower()} repair in {place}. "
        "Shops whose own sites mention this appliance. Call directly — not a lead mill."
    )
    schema = ld_json({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{app['name']} repair in {label}",
        "numberOfItems": len(shops),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": l["name"], "url": listing_url(l)}
            for i, l in enumerate(shops)
        ],
    })
    crumbs = [("/", "Home"), (f"/{metro['slug']}/", label), (f"/{metro['slug']}/{app['pathSegment']}/", f"{app['name']} repair")]
    write_page(page, layout(
        page,
        f"{app['name']} repair in {label} — independent techs",
        desc,
        body,
        metro["slug"],
        crumbs,
        extra_head=schema,
    ))


def page_profile(listing: dict) -> None:
    metro = CITY_BY_SLUG.get(listing.get("citySlug") or "phoenix") or {
        "slug": listing.get("citySlug") or "phoenix",
        "name": "Directory",
        "metroName": "this area",
        "state": "",
    }
    page = f"{metro['slug']}/techs/{listing['slug']}/index.html"
    apps = appliances_for(listing)
    app_links = ", ".join(
        f'<a href="{e(href(page, f"/{metro["slug"]}/{a["pathSegment"]}/"))}">{e(a["name"])}</a>' for a in apps
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

    place = metro.get("metroName") or metro_nav_label(metro)
    body = f"""
    <header class="hero">
      <p class="kicker">{e(place)} listing</p>
      <h1>{e(listing["name"])}</h1>
      {flags_html(listing)}
      <p class="lede">An independent or locally based appliance repair business serving the {e(place)} area. Details below were taken from the sources listed at the bottom of this page. Confirm everything when you call — websites go out of date.</p>
      <div class="hero-actions">
        <a class="btn btn-call" href="{e(tel_href(listing['phone']))}">Call {e(listing['phoneDisplay'])}</a>
        <a class="btn btn-ghost" href="{e(listing['website'])}" rel="noopener noreferrer">Visit website</a>
      </div>
    </header>
    {registration_html(page, metro)}
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
    crumbs = [("/", "Home"), (f"/{metro['slug']}/", metro_nav_label(metro)), (listing_url(listing), listing["name"])]
    write_page(page, layout(
        page,
        f"{listing['name']} — {metro_nav_label(metro)} appliance repair",
        desc,
        body,
        metro["slug"],
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
          <tr><th scope="row">Accountability</th><td>A local reputation, plus the license or registration that applies where the work is done. In Arizona, that is often a Registrar of Contractors license. In California, appliance repair dealers must register with the Bureau of Household Goods and Services (BHGS). Some shops publish those numbers; you should still look them up in the official state search.</td><td>Brand policies plus whatever license the visiting company holds. A familiar logo is not the same thing as a local license check.</td></tr>
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
    for l in listings_for_metro("phoenix"):
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


def listing_request_mailto(email: str) -> str:
    subject = "Get listed: [business name]"
    body = (
        "Business name:\n"
        "Phone:\n"
        "Website:\n"
        "Cities served:\n"
        "Appliances repaired:\n"
        "Independently owned (yes/no):\n"
        "\n"
        "Anything else we should verify:\n"
    )
    return f"mailto:{email}?subject={quote(subject, safe='')}&body={quote(body, safe='')}"


def obfuscate_email_html(email: str) -> str:
    user, _, domain = email.partition("@")
    return f"{e(user)}&#64;{e(domain)}"


def page_get_listed() -> None:
    page = "get-listed/index.html"
    email = (site.get("contactEmail") or "").strip()
    if "@" not in email:
        raise SystemExit("Set contactEmail in data/site.json")
    user, _, domain = email.partition("@")
    mailto_href = e(listing_request_mailto(email)).replace("@", "&#64;")
    email_html = obfuscate_email_html(email)
    attrs = f'data-user="{e(user)}" data-domain="{e(domain)}"'
    body = f"""
    <header class="hero">
      <p class="kicker">For technicians and shop owners</p>
      <h1>Get listed, or ask about a featured listing</h1>
      <p class="lede">If you are an independent or locally owned appliance repair business serving a city we cover, we want accurate information on this site. Basic listings are free. Featured placements, if we offer them later, will be clearly labeled and will not bury or hide other shops.</p>
    </header>
    <section class="listing-request" aria-labelledby="email-to-list">
      <h2 id="email-to-list">Email us to get listed</h2>
      <p>Email us your shop details and we will verify them before publishing. We list independent and locally owned shops only — not national call centers or lead mills.</p>
      <p>Send your request to <a class="js-listing-email" {attrs} href="{mailto_href}">{email_html}</a>.</p>
      <p><a class="btn btn-primary js-listing-email" {attrs} href="{mailto_href}">Email us to get listed</a></p>
      <p class="fine-print">Your email app will open with the subject “Get listed: [business name]” and a short checklist in the body. Replace the bracketed text with your shop name, fill in the details, and send. A request is not a paid placement and does not guarantee a listing until we verify your information.</p>
      <h3>Please include</h3>
      <ul>
        <li>Business name</li>
        <li>Phone</li>
        <li>Website</li>
        <li>Cities served</li>
        <li>Appliances repaired</li>
        <li>Whether the shop is independently owned</li>
      </ul>
    </section>
    <section class="section prose">
      <h2>What we will and will not do</h2>
      <ul>
        <li>We will verify facts against a public page or a document you provide before publishing.</li>
        <li>We will not invent reviews, ratings, or prices for you.</li>
        <li>A featured listing, if offered, will be marked as paid or featured. It will not be the only way to appear in the directory.</li>
        <li>A brand-specialist sponsorship, if offered, will be labeled as a paid sponsorship and will not be presented as a ranked “best of.”</li>
      </ul>
      <h2>Featured placements</h2>
      <p>Paid featured options may come later. Nothing is for sale now, and no featured or sponsored placements have been sold. If we offer them, they will stay clearly labeled.</p>
    </section>
    """
    desc = "Request a free listing in the Indie Appliance Repair directory by email. Independent shops only. Featured placements, if offered, will be clearly labeled."
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
      <p class="lede">We are building a small, useful directory of independent appliance technicians — now in Phoenix, Arizona, and Riverside County, California — so homeowners can call a shop directly instead of entering a lead marketplace.</p>
      <h2>Where we cover</h2>
      <p>Phoenix is our first metro: a large, year-round repair market where heat stresses refrigerators and ice makers, with many documented owner-operated shops and no strong consumer directory that organizes independents by city, appliance, and brand. Riverside County is our second: the Inland Empire and Coachella Valley, where California requires appliance repair dealers to register with the Bureau of Household Goods and Services. We will keep adding verified shops and city pages in both areas, then expand to other metros one at a time.</p>
      <h2>How we research a listing</h2>
      <ul>
        <li>We open the business website (or another public page) and record the URL and the date.</li>
        <li>We include only facts stated there: name, phone, website, address, hours, service area, appliances, brands, and published fees or license numbers.</li>
        <li>We do not invent ratings, reviews, prices, or coverage areas. If a street address was not on the official site, we say so.</li>
        <li>National chains and lead-mill landing pages are out of scope for “independent” listings. Multi-office local companies can still appear if they are local businesses rather than a national franchise; the profile will say so.</li>
      </ul>
      <p>This directory currently includes {len(listings_for_metro("phoenix"))} Phoenix-metro businesses and {len(listings_for_metro("riverside-county"))} Riverside County businesses, researched on {e(site.get("accessedDate") or TODAY)}.</p>
      <h2>Get in touch</h2>
      <p>Use the <a href="{e(href(page, "/get-listed/"))}">Get listed</a> page to request an addition or a correction by email. Listings are free for independent and locally owned shops.</p>
    </article>
    """
    desc = "How Indie Appliance Repair researches listings, why Phoenix and Riverside County are the first markets, and what we will not invent."
    crumbs = [("/", "Home"), ("/about/", "About")]
    write_page(page, layout(page, "About Indie Appliance Repair", desc, body, "home", crumbs))


def page_404() -> None:
    page = "404.html"
    body = f"""
    <header class="hero">
      <p class="kicker">404</p>
      <h1>That page is not here</h1>
      <p class="lede">The link may be outdated, or the city page has not been built yet. Try a live directory or the homepage.</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="{e(href(page, "/phoenix/"))}">Phoenix directory</a>
        <a class="btn btn-ghost" href="{e(href(page, "/riverside-county/"))}">Riverside County directory</a>
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
    for metro in live_metros():
        page_metro(metro)
        remember(f"{metro['slug']}/index.html")
        for subcity in metro.get("cities") or []:
            page_subcity(metro, subcity)
            remember(f"{metro['slug']}/{subcity['slug']}/index.html")
        for app in appliances:
            if listings_for_appliance(app["slug"], metro["slug"]):
                page_appliance(metro, app)
                remember(f"{metro['slug']}/{app['pathSegment']}/index.html")
        for listing in listings_for_metro(metro["slug"]):
            page_profile(listing)
            remember(f"{metro['slug']}/techs/{listing['slug']}/index.html")
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
