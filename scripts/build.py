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
DO_NOT_LIST_PATH = DATA / "do-not-list.json"
do_not_list = json.loads(DO_NOT_LIST_PATH.read_text(encoding="utf-8")) if DO_NOT_LIST_PATH.exists() else []


def _norm_url(value: str | None) -> str:
    return (value or "").strip().rstrip("/").lower()


def _norm_phone(value: str | None) -> str:
    return "".join(ch for ch in (value or "") if ch.isdigit())


def listing_is_blocked(listing: dict) -> bool:
    """True if a shop is on data/do-not-list.json (id, slug, site, phone, email, or name)."""
    listing_id = (listing.get("id") or "").strip()
    slug = (listing.get("slug") or "").strip()
    website = _norm_url(listing.get("website"))
    phone = _norm_phone(listing.get("phone"))
    email = (listing.get("email") or "").strip().lower()
    name = (listing.get("name") or "").strip().lower()
    for entry in do_not_list:
        if listing_id and listing_id == (entry.get("id") or "").strip():
            return True
        if slug and slug == (entry.get("slug") or "").strip():
            return True
        if website and website == _norm_url(entry.get("website")):
            return True
        if phone and phone == _norm_phone(entry.get("phone")):
            return True
        if email and email == (entry.get("email") or "").strip().lower():
            return True
        if name and name == (entry.get("name") or "").strip().lower():
            return True
    return False


_skipped = [l for l in listings if listing_is_blocked(l)]
if _skipped:
    print("Skipping do-not-list shop(s): " + ", ".join(l.get("slug") or l.get("id") or "?" for l in _skipped))
listings = [l for l in listings if not listing_is_blocked(l)]
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
        f'<a href="{e(guide)}" rel="noopener noreferrer">BHGS consumer guide</a>. '
        f'<a href="{e(href(page_file, "/guides/check-california-bhgs-registration/"))}">How to check a registration, step by step</a>. '
        f'<a href="{e(href(page_file, "/riverside-county/service-call-fees/"))}">Service-call fees local shops publish</a>.</p>'
    )


def ld_json(obj: dict) -> str:
    payload = json.dumps(obj, ensure_ascii=False, indent=None)
    payload = payload.replace("<", "\\u003c")
    return f'<script type="application/ld+json">{payload}</script>'


def logo_html(page_file: str) -> str:
    src = href(page_file, "/img/logo.png")
    return f'<img class="logo-img" src="{e(src)}" alt="" width="32" height="32">'


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


def absolute_url(path: str) -> str:
    """Absolute https canonical URL for a site path."""
    origin = (site.get("canonicalOrigin") or "https://indieappliancerepair.com").rstrip("/")
    path = (path or "/").strip() or "/"
    if not path.startswith("/"):
        path = "/" + path
    if path != "/" and not path.endswith("/") and not path.rsplit("/", 1)[-1].count("."):
        path += "/"
    return origin + path


def crumbs_html(page_file: str, crumbs: list[tuple[str, str]]) -> str:
    parts = []
    items = []
    for i, (path, label) in enumerate(crumbs):
        last = i == len(crumbs) - 1
        if last:
            parts.append(f"<li aria-current='page'>{e(label)}</li>")
        else:
            parts.append(f'<li><a href="{e(href(page_file, path))}">{e(label)}</a></li>')
        items.append({
            "@type": "ListItem",
            "position": i + 1,
            "name": label,
            "item": absolute_url(path),
        })
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
        <li><a href="{e(href(page_file, "/guides/check-california-bhgs-registration/"))}">Check a CA BHGS registration</a></li>
        <li><a href="{e(href(page_file, "/riverside-county/service-call-fees/"))}">Riverside County service-call fees</a></li>
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
    favicon = href(page_file, "/favicon.ico")
    favicon_32 = href(page_file, "/img/favicon-32.png")
    favicon_16 = href(page_file, "/img/favicon-16.png")
    apple_icon = href(page_file, "/img/apple-touch-icon.png")
    logo_abs = f"{origin}/img/logo.png" if origin else ""
    og_image = (
        f'<meta property="og:image" content="{e(logo_abs)}">\n'
        f'  <meta property="og:image:type" content="image/png">\n'
        f'  <meta property="og:image:width" content="512">\n'
        f'  <meta property="og:image:height" content="512">'
        if logo_abs else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(description)}">
  <meta name="robots" content="index,follow">
  {canonical}
  <link rel="icon" href="{e(favicon)}" sizes="any">
  <link rel="icon" type="image/png" sizes="32x32" href="{e(favicon_32)}">
  <link rel="icon" type="image/png" sizes="16x16" href="{e(favicon_16)}">
  <link rel="apple-touch-icon" href="{e(apple_icon)}">
  {og_image}
  <link rel="stylesheet" href="{e(css)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&amp;family=Source+Sans+3:wght@400;550;650;700&amp;display=swap" rel="stylesheet">
  {extra_head}
</head>
<body>
  <a class="skip" href="#content">Skip to content</a>
  <header class="site-header">
    <div class="wrap">
      <div class="header-inner">
        <a class="logo" href="{e(home)}">{logo_html(page_file)}<span class="logo-text"><strong>Indie Appliance Repair</strong><span>Independent techs, not a lead mill</span></span></a>
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
        **({"url": listing["website"]} if listing.get("website") else {}),
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

    city_link_rows = []
    for m in live:
        subs = m.get("cities") or []
        if not subs:
            continue
        links = ", ".join(
            f'<a href="{e(href(page, f"/{m["slug"]}/{sub["slug"]}/"))}">{e(sub["name"])}</a>' for sub in subs
        )
        city_link_rows.append(f"<p><strong>{e(metro_nav_label(m))}:</strong> {links}</p>")
    city_pages_html = "".join(city_link_rows)

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
      <h3>City pages</h3>
      {city_pages_html}
    </section>
    <section class="section">
      <h2>Guides and comparisons</h2>
      <div class="grid grid-2">
        <a class="card cat-card" href="{e(href(page, "/guides/repair-vs-replace/"))}">
          <h3>Repair vs. replace</h3>
          <p>Get a diagnosis first, then compare the quoted repair with the cost and remaining life of a new machine.</p>
        </a>
        <a class="card cat-card" href="{e(href(page, "/guides/check-california-bhgs-registration/"))}">
          <h3>Check a California BHGS registration</h3>
          <p>Step-by-step lookup of an appliance repair dealer in the state license search, what the results mean, and how to file a complaint.</p>
        </a>
        <a class="card cat-card" href="{e(href(page, "/riverside-county/service-call-fees/"))}">
          <h3>Riverside County service-call fees</h3>
          <p>What local shops publish for a service call or diagnostic visit, what “waived with repair” means, and California’s rules on trip charges.</p>
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
            "City pages are rolling out one at a time: Mesa and Chandler are live; Scottsdale, Gilbert, and others are next. Riverside County, California, is live as a second market."
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
    names = subcity.get("match") or [subcity["name"]]
    names_l = {n.lower() for n in names}
    shops_all = listings_for_subcity(metro["slug"], subcity)
    label = metro_nav_label(metro)
    name = subcity["name"]
    state = metro.get("state") or ""
    state_name = metro.get("stateName") or state
    is_region = bool(subcity.get("isRegion"))
    kind = "area" if is_region else "city"

    def based_here(l: dict) -> bool:
        return ((l.get("address") or {}).get("city") or "").lower() in names_l

    based = [l for l in shops_all if based_here(l)]
    others = [l for l in shops_all if not based_here(l)]
    # Split into "based here" and "also lists" only when a page has some of each
    # and opts in (Riverside County pages keep their original single list).
    split = bool(subcity.get("splitBased")) and based and others
    shops = based + others if split else shops_all

    thin = ""
    if len(shops) <= 2:
        thin = (
            f'<p class="note"><strong>Thin on published names.</strong> Only {len(shops)} shop'
            f'{"s" if len(shops) != 1 else ""} in this directory published {e(name)} on a source we opened. '
            f"A nearby city page, or the <a href=\"{e(href(page, f'/{metro['slug']}/'))}\">{e(label)} directory</a>, "
            "may have shops that will still drive to you — call and ask.</p>"
        )
    app_links = []
    for app in appliances:
        n = len([l for l in shops if app["slug"] in l.get("appliances", [])])
        if n:
            app_links.append(
                f'<a href="{e(href(page, f"/{metro["slug"]}/{app["pathSegment"]}/"))}">{e(app["name"])} ({n})</a>'
            )
    scope_word = "county" if metro.get("hubKind") == "county" else "metro"
    app_nav = (f"Related {scope_word} category pages: " + ", ".join(app_links) + ".") if app_links else ""

    if split:
        listing_sections = f"""
    <section class="section">
      <h2>{len(based)} shop{"s" if len(based) != 1 else ""} based in {e(name)}</h2>
      <p>The address on the shop's own website (or the public business listing we recorded) is in {e(name)}.</p>
      <div class="grid grid-2">{"".join(listing_card(page, l) for l in based)}</div>
    </section>
    <section class="section">
      <h2>{len(others)} more shop{"s" if len(others) != 1 else ""} that list {e(name)}</h2>
      <p>Based elsewhere in the {e(label)} area, but {e(name)} is named in their published service area.</p>
      <div class="grid grid-2">{"".join(listing_card(page, l) for l in others)}</div>
    </section>"""
    else:
        cards = "".join(listing_card(page, l) for l in shops) or "<p>No shops in this directory have published this city yet.</p>"
        listing_sections = f"""
    <section class="section">
      <h2>{len(shops)} shop{"s" if len(shops) != 1 else ""} that list{"s" if len(shops)==1 else ""} {e(name)}</h2>
      <div class="grid grid-2">{cards}</div>
    </section>"""

    tips_html = ""
    tips = subcity.get("tips") or []
    if tips:
        items = "".join(f"<li>{e(t)}</li>" for t in tips)
        lic = ""
        if metro.get("licenseSearchUrl"):
            lic = (
                f'<p><a href="{e(metro["licenseSearchUrl"])}" rel="noopener noreferrer">Arizona ROC contractor search</a>'
                + (f' · <a href="{e(metro["licenseGuideUrl"])}" rel="noopener noreferrer">ROC: before you hire a contractor</a>' if metro.get("licenseGuideUrl") else "")
                + "</p>"
            )
        tip_sources = subcity.get("tipSources") or []
        if tip_sources:
            lic += "<p>Sources for the tips above: " + " · ".join(
                f'<a href="{e(t["url"])}" rel="noopener noreferrer">{e(t["label"])}</a>' for t in tip_sources
            ) + "</p>"
        tips_html = f"""
    <section class="section">
      <h2>Before you call a {e(name)} repair shop</h2>
      <ul>{items}</ul>
      {lic}
    </section>"""

    faq_items = []
    if split:
        faq_items.append((
            f"How many independent appliance repair shops in this directory serve {name}?",
            f"{len(shops)} shops in this directory publish {name} on a source we opened: {len(based)} based in {name} and {len(others)} based elsewhere that list it in their service area. This is a researched starting set, not a complete census.",
        ))
        faq_items.append((
            f"Is a shop based in {name} faster to get?",
            "Not necessarily. Many shops route technicians across several cities, and some out-of-town shops say they have techs who live near their customers. Ask about the next available window and any trip fee when you call.",
        ))
    faq_html = ""
    faq_ld = ""
    if faq_items:
        faq_html = '<section class="section"><h2>' + e(name) + " appliance repair questions</h2>" + "".join(
            f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq_items
        ) + "</section>"
        faq_ld = ld_json({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in faq_items
            ],
        })

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
    {listing_sections}
    {tips_html}
    {faq_html}
    """
    region = f"{label}, {state_name}" if metro.get("hubKind") == "county" else state_name
    desc = (
        f"Independent appliance repair in {name}, {region}. "
        + (
            f"{len(shops)} shops in this directory published this {kind} on a source we opened"
            + (f", {len(based)} of them based in {name}." if split else ".")
            if len(shops) != 1
            else f"1 shop in this directory published this {kind} on a source we opened."
        )
    )
    schema = ld_json({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Independent appliance repair in {name}, {state}",
        "numberOfItems": len(shops),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": l["name"], "url": listing_url(l)}
            for i, l in enumerate(shops)
        ],
    })
    crumbs = [("/", "Home"), (f"/{metro['slug']}/", label), (f"/{metro['slug']}/{subcity['slug']}/", name)]
    write_page(page, layout(
        page,
        f"Appliance repair in {name}, {state} — independent techs",
        desc,
        body,
        metro["slug"],
        crumbs,
        extra_head=schema + faq_ld,
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
    ) or ("See the company website" if listing.get("website") else "Not published on the sources we opened — confirm when you call")
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

    website_btn = (
        f'<a class="btn btn-ghost" href="{e(listing["website"])}" rel="noopener noreferrer">Website</a>'
        if listing.get("website") else ""
    )
    website_btn_hero = (
        f'<a class="btn btn-ghost" href="{e(listing["website"])}" rel="noopener noreferrer">Visit website</a>'
        if listing.get("website") else ""
    )
    sticky = f"""<div class="sticky-call" role="region" aria-label="Call this shop">
      <a class="btn btn-call" href="{e(tel_href(listing['phone']))}">Call {e(listing['phoneDisplay'])}</a>
      {website_btn}
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
        {website_btn_hero}
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


BHGS_GUIDE_PATH = "/guides/check-california-bhgs-registration/"


def page_bhgs_guide() -> None:
    page = "guides/check-california-bhgs-registration/index.html"
    src = {
        "ear": "https://www.bhgs.dca.ca.gov/consumers/ear.html",
        "law": "https://www.bhgs.dca.ca.gov/laws/ear_law_book-effective_1-1-24_with_links.pdf",
        "search": "https://search.dca.ca.gov/",
        "faq": "https://search.dca.ca.gov/FAQ",
        "lookup": "https://www.bhgs.dca.ca.gov/enforcement/lookup.html",
        "complaint": "https://www.bhgs.dca.ca.gov/consumers/complaint.html",
        "online": "https://connect.dca.ca.gov/bhgs/public/submitcomplaint/bhgs",
        "form": "https://www.bhgs.dca.ca.gov/forms_pubs/complaint_form.pdf",
        "cslb": "https://www.cslb.ca.gov/OnlineServices/CheckLicenseII/CheckLicense.aspx",
    }
    def a(key: str, label: str) -> str:
        return f'<a href="{e(src[key])}" rel="noopener noreferrer">{label}</a>'
    riverside = href(page, "/riverside-county/")
    body = f"""
    <article class="prose hero">
      <p class="kicker">Guide · California · Riverside County</p>
      <h1>How to check an appliance repair shop’s California BHGS registration</h1>
      <p class="lede">In California, a business that repairs major home appliances for pay has to be registered with the Bureau of Household Goods and Services (BHGS) as a service dealer. Here is what that registration is, how to look a shop up in the state’s free license search, and where to file a complaint. Every rule below links to the official source.</p>
      <p class="note">This is a plain-language summary, not legal advice. Laws and state websites change. If anything here differs from the official pages linked below, the official pages win. Last checked: November 19, 2026.</p>

      <h2>What a “service dealer” registration is</h2>
      <p>California’s Electronic and Appliance Repair Dealer Registration Law (Business and Professions Code, starting at section 9800) defines a <strong>service dealer</strong> as a person or business that, for compensation, repairs, services, or maintains major appliances or home electronics, or advertises that it does (section 9801(f)). The law defines “major home appliance” to include refrigerators, freezers, ranges, microwave ovens, washers, dryers, dishwashers, trash compactors, ice makers, dehumidifiers, residential portable furnaces, and room air conditioners used in the home or home office (section 9801(i)). {a("law", "Source: BHGS law book, 2024 edition (PDF)")}.</p>
      <p>The bureau that enforces this law is BHGS, part of the California Department of Consumer Affairs (DCA). BHGS says it regulates “service dealers and the repair of major home appliances and electronic equipment used for personal or home office use,” and handles complaints about the repair or installation — not the sale — of those items. {a("ear", "Source: BHGS consumer guide to electronic and appliance repair")}.</p>

      <h2>Who has to register</h2>
      <ul>
        <li><strong>Any business acting as a service dealer.</strong> Section 9840 makes it unlawful to act as a service dealer without first registering and without a registration that is currently valid.</li>
        <li><strong>Each location.</strong> Section 9830 requires the registration fee for each place of business and each drop-off location the dealer operates in California.</li>
        <li><strong>Out-of-state businesses, too.</strong> Under section 9830, a service dealer with no place of business in California that still does appliance or electronic repair work in the state must hold a valid BHGS registration.</li>
        <li><strong>Renewal is not optional.</strong> Section 9832 says registrations expire no more than 12 months after issue and must be renewed.</li>
      </ul>
      <p>{a("law", "Source: sections 9830, 9832, and 9840 in the BHGS law book (PDF)")}.</p>

      <h2>Where the registration number should show up</h2>
      <p>You often do not have to ask for the number. The BHGS regulations require it on paperwork you will see:</p>
      <ul>
        <li><strong>Receipts or claim checks</strong> when a shop takes an appliance away for repair must show the dealer’s name and registration number (California Code of Regulations, title 16, section 2721).</li>
        <li><strong>Invoices</strong> must show the dealer’s state registration number(s), identified as such (section 2725).</li>
        <li><strong>The registration certificate</strong> must be displayed in a conspicuous place at the registered place of business (section 2714).</li>
      </ul>
      <p>Numbers in BHGS’s own published citation list look like <code>A-49953</code> for appliance businesses and <code>E-93487</code> for electronics businesses. {a("lookup", "Source: BHGS citations and disciplinary actions")}. {a("law", "Regulations: BHGS law book (PDF)")}.</p>

      <h2>How to search, step by step</h2>
      <ol>
        <li>Open the {a("search", "DCA License Search")} at search.dca.ca.gov. (BHGS’s own {a("lookup", "license search page")} sends “All Other Industries” — everything except household movers — to this same search.)</li>
        <li>Under <strong>Boards and Bureaus</strong>, choose <strong>Household Goods and Services, Bureau of</strong>.</li>
        <li>Under <strong>License Type</strong>, you can pick <strong>Major Appliance Repair</strong> or <strong>Combination-Electric and Appliance Repair</strong>. If you are not sure which one the shop holds, leave the type unselected so you do not filter it out.</li>
        <li>Search by <strong>License Number</strong> if the shop published one or it appears on your estimate or invoice. Otherwise, search by <strong>Business Name</strong>, or by the owner’s first and last name.</li>
        <li>Open <strong>More Details</strong> on the matching record. DCA says each record shows whether a license is current, expired, or has been subject to disciplinary action such as suspension or revocation. {a("search", "Source: DCA License Search")}.</li>
        <li>Check that the name and address on the record match the business you are about to hire. A shop that advertises appliance repair is required to show its firm name and address as they appear on its registration certificate (regulation section 2751).</li>
      </ol>

      <h2>What the results mean</h2>
      <ul>
        <li><strong>Status.</strong> The record tells you whether the registration is current or expired, and whether there has been disciplinary action. When a status has a question-mark hint, DCA says the hint gives that status’s detailed definition — read it rather than guessing. {a("faq", "Source: DCA License Search FAQ")}.</li>
        <li><strong>Icons on “More Details.”</strong> Per DCA, one icon means the record has public record or disciplinary actions; another means public documents are available. Open them. {a("faq", "Source: DCA License Search FAQ")}.</li>
        <li><strong>City filters can miss shops.</strong> DCA says city and county filters use the address of record, which does not always match where a business works. A shop based in Riverside or Temecula can still serve Hemet or San Jacinto, so search by name or number instead of filtering by your own city. {a("faq", "Source: DCA License Search FAQ")}.</li>
        <li><strong>Citations are listed separately.</strong> BHGS publishes a table of citations and disciplinary actions, including fines issued to businesses marked “UNLICENSED.” {a("lookup", "BHGS citations and disciplinary actions")}.</li>
        <li><strong>No match?</strong> Try the exact legal name, the DBA, or the owner’s name before drawing conclusions. DCA’s disclaimer notes its data can contain errors or posting delays. If you still cannot find a current registration, ask the shop for its number and look it up again.</li>
      </ul>

      <h2>Contractor licenses are a separate check</h2>
      <p>A BHGS registration covers appliance repair. Some shops also hold a Contractors State License Board (CSLB) license for other work. CSLB licenses are not in the DCA License Search; DCA points to the {a("cslb", "CSLB license check")} instead. {a("search", "Source: DCA License Search")}.</p>

      <h2>Your rights on a repair (what BHGS says)</h2>
      <ul>
        <li><strong>Written estimate first.</strong> Service dealers must give you a written estimate with the total price before repairs. (Business and Professions Code section 9844.)</li>
        <li><strong>Trip and diagnostic charges.</strong> A trip charge, if any, must be quoted before the service call. The dealer may charge a reasonable diagnostic fee, and charges for the actual repair only if you agree to it.</li>
        <li><strong>More than the estimate.</strong> Extra parts or labor require your approval of the revised total.</li>
        <li><strong>Your old parts.</strong> You can get replaced parts back, except unsafe or toxic parts, parts rebuilt on an exchange basis, or if you waived it.</li>
        <li><strong>Part prices are not regulated.</strong> BHGS says it does not regulate the price of parts.</li>
      </ul>
      <p>{a("ear", "Source: BHGS consumer guide FAQ")}. {a("law", "Law: section 9844 (PDF)")}.</p>

      <h2>How to file a complaint</h2>
      <ol>
        <li><strong>Try the business first.</strong> BHGS suggests writing to the manager, explaining the service, the problem, and the resolution you want, with copies of receipts or warranties.</li>
        <li><strong>File with BHGS.</strong> Use the {a("online", "online complaint form on DCA Connect")} (BHGS’s recommended option), or the {a("form", "printable complaint form (PDF)")} by email or mail. The form asks for the business’s license number if you know it and copies of estimates, invoices, and other papers.</li>
        <li><strong>Include the model and serial number</strong> if your complaint involves an appliance the shop took away. BHGS says that if a dealer went out of business while holding your item, you can call DCA at 1-800-952-5210 or file with BHGS, and it will try to help locate the item.</li>
      </ol>
      <p><strong>What can happen.</strong> BHGS reviews whether a complaint is within its authority. Depending on the investigation, outcomes range from education or a warning letter to a citation and fine, probation, suspension or revocation, or a referral to law enforcement or a district attorney. BHGS says a refund, repair, or replacement is not guaranteed, and it cannot force a business to settle or refund you. For money recovery, it points to small claims court (claims under $10,000) or civil court. Manufacturer-warranty and home-warranty problems go elsewhere (the Song-Beverly Warranty Act and the California Department of Insurance, respectively). {a("complaint", "Source: BHGS File a Complaint page")}.</p>
      <p>BHGS’s phone number, as published on its website and complaint form: (916) 999-2041.</p>

      <h2>How we use registration on this site</h2>
      <p>On our {f'<a href="{e(riverside)}">Riverside County pages</a>'}, when a shop publishes a registration number on its own website, we quote it as the shop’s claim and link to the official search. We do not invent license numbers, and a number on a shop’s website is not proof that the registration is current today. Look it up before you book.</p>

      <section class="sources" aria-label="Sources">
        <h2>Sources</h2>
        <ul>
          <li>{a("ear", "BHGS — A Consumer Guide to Electronic and Appliance Repair")} (accessed 2026-11-19)</li>
          <li>{a("law", "BHGS — Electronic and Appliance Repair Dealer Registration Law and Regulations, 2024 edition (PDF)")}: B&amp;P Code §§ 9801, 9830, 9832, 9840, 9844; 16 CCR §§ 2714, 2721, 2725, 2751 (accessed 2026-11-19)</li>
          <li>{a("search", "DCA License Search")}, its {a("faq", "FAQ")}, and its disclaimer (accessed 2026-11-19)</li>
          <li>{a("lookup", "BHGS — License Search and Citations and Disciplinary Actions")} (accessed 2026-11-19)</li>
          <li>{a("complaint", "BHGS — File a Complaint")} and {a("form", "BHGS complaint form (PDF, rev. 02/26)")} (accessed 2026-11-19)</li>
        </ul>
      </section>

      <h2>Find a local tech</h2>
      <p>Browse the <a href="{e(riverside)}">Riverside County directory</a> — Riverside, Moreno Valley, Corona, Temecula, Murrieta, Hemet, San Jacinto, Menifee, Perris, Lake Elsinore, and the Coachella Valley. Before you book, look up the shop’s registration with the steps above. Related: <a href="{e(href(page, "/guides/repair-vs-replace/"))}">repair or replace?</a> and <a href="{e(href(page, "/compare/independent-vs-chains/"))}">independent shops vs. chains</a>.</p>
    </article>
    """
    desc = (
        "How to look up a California appliance repair shop's BHGS service dealer registration in the DCA "
        "License Search, what the results mean, and how to file a complaint. Official sources cited."
    )
    faq = ld_json({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": "Do appliance repair businesses in California need to register?",
             "acceptedAnswer": {"@type": "Answer", "text": "Yes. Under California Business and Professions Code section 9840, it is unlawful to act as a service dealer — a business that repairs, services, or maintains major home appliances or home electronics for pay — without a currently valid registration with the Bureau of Household Goods and Services (BHGS)."}},
            {"@type": "Question", "name": "How do I check an appliance repair shop's BHGS registration?",
             "acceptedAnswer": {"@type": "Answer", "text": "Use the DCA License Search at search.dca.ca.gov. Choose Household Goods and Services, Bureau of; optionally pick the Major Appliance Repair or Combination-Electric and Appliance Repair license type; then search by license number, business name, or owner name and open More Details to see whether the registration is current, expired, or subject to discipline."}},
            {"@type": "Question", "name": "Where do I file a complaint about an appliance repair in California?",
             "acceptedAnswer": {"@type": "Answer", "text": "BHGS accepts complaints about the repair or installation of major home appliances. BHGS recommends filing online through DCA Connect; a printable complaint form can be sent by email or mail. BHGS says a refund is not guaranteed and it cannot force a business to settle."}},
        ],
    })
    crumbs = [("/", "Home"), ("/riverside-county/", "Riverside County"), (BHGS_GUIDE_PATH, "Check a BHGS registration")]
    write_page(page, layout(page, "How to check a California appliance repair shop’s BHGS registration — Indie Appliance Repair", desc, body, "guides", crumbs, extra_head=faq))


FEES_PATH = "/riverside-county/service-call-fees/"


def page_rc_fees() -> None:
    """Riverside County: sourced table of shop-published service-call / diagnostic fees."""
    page = "riverside-county/service-call-fees/index.html"
    by_slug = {l["slug"]: l for l in LISTINGS}
    # (slug, fee shown in table, fee number for sorting, what the shop says, source url, accessed)
    rows = [
        ("appliance-solutions-corona", "$25", 25,
         "Service call waived with repair charges; the listing page also offers free phone estimates. The page did not load when we re-checked on 2026-11-23, so treat this figure as older.",
         "http://www.shopcorona.com/appliancesolutionsnow", "2026-11-18"),
        ("techpulse-services", "$60", 60,
         "Service call applied to the repair if you go ahead.",
         "https://techpulseapplianceservice.com/", "2026-11-23"),
        ("av-appliance-repair", "$65 or $85", 65,
         "$65 for refrigerator, washer, dryer, dishwasher, gas range/cooktop, disposal, and wine cooler visits; $85 for built-in refrigerator, electric range/oven, microwave, and A/C visits. Waived when a repair is done with your consent.",
         "https://avappliancerepair.com/appliance-service-call-pricing/", "2026-11-23"),
        ("quick-n-easy-appliance", "From $75", 75,
         "Service call starts at $75; labor starts at $175, which includes the service call fee. The fee is applied toward labor if you proceed; the site says same-day emergency calls carry a higher fee.",
         "https://www.quickneasy.net/", "2026-11-23"),
        ("appliance-showroom-hemet", "$76, $109, or $129", 76,
         "Priced by city: $76 for Hemet, San Jacinto, Valle Vista, Homeland, Nuevo, Romoland; $109 for Sun City, Menifee, Perris, Winchester, Moreno Valley, Canyon Lake, Banning, Beaumont; $129 for Temecula, Murrieta, Wildomar, Lake Elsinore, Sage, Anza, Aguanga, Idyllwild. Basic labor is listed as the initial visit plus $99.",
         "https://www.applianceshowroom.com/copy-of-sales", "2026-11-23"),
        ("nash-appliance-group", "$79", 79,
         "Diagnostic fee waived with repair.",
         "https://nashappliance.com/", "2026-11-23"),
        ("tims-fridge-repair", "$80 or $120", 80,
         "$80 residential refrigerator or freezer diagnostic, applied to the final balance if you move forward; $120 diagnostic for business refrigerators. Mileage of $0.55 per mile may apply when travel is over one hour.",
         "https://chillynow.com/", "2026-11-23"),
    ]
    rows = [r for r in rows if r[0] in by_slug]
    no_number = [
        ("mmo-appliance-repair", "Service-call fee waived with a completed repair; call or text your ZIP code to confirm the rate for your address.", "https://mmoappliancerepair.com/"),
        ("mg-service", "Service call waived with a repair (the diagnostic fee is waived when you book the repair).", "https://mgserviceappliance.com/"),
        ("solvanta-home-services", "“$0 service call with completed repair” — the service-call fee is waived when you proceed.", "https://www.solvanta-appliancerepair.com/"),
        ("action-appliance-temecula", "Staff tell you the cost of the initial visit and diagnosis when they call to confirm the appointment.", "https://www.actionmaytag.com/service-request"),
    ]
    no_number = [r for r in no_number if r[0] in by_slug]
    lo = min(r[2] for r in rows)
    hi_vals = [129 if r[0] == "appliance-showroom-hemet" else (120 if r[0] == "tims-fridge-repair" else (85 if r[0] == "av-appliance-repair" else r[2])) for r in rows]
    hi = max(hi_vals)
    bhgs = "https://www.bhgs.dca.ca.gov/consumers/ear.html"
    law = "https://www.bhgs.dca.ca.gov/laws/ear_law_book-effective_1-1-24_with_links.pdf"

    def base(l: dict) -> str:
        city = (l.get("address") or {}).get("city")
        return city or "Riverside County"

    trs = []
    for slug, fee, _n, note, url, acc in rows:
        l = by_slug[slug]
        trs.append(
            f'<tr><th scope="row"><a href="{e(href(page, listing_url(l)))}">{e(l["name"])}</a>'
            f'<br><span class="meta">{e(base(l))}</span></th>'
            f'<td><strong>{e(fee)}</strong></td><td>{e(note)}</td>'
            f'<td><a href="{e(url)}" rel="noopener noreferrer">Shop website</a><br><span class="meta">accessed {e(acc)}</span></td></tr>'
        )
    lis = []
    for slug, note, url in no_number:
        l = by_slug[slug]
        lis.append(
            f'<li><a href="{e(href(page, listing_url(l)))}">{e(l["name"])}</a> ({e(base(l))}): {e(note)} '
            f'<a href="{e(url)}" rel="noopener noreferrer">Source</a> (accessed 2026-11-23).</li>'
        )
    riverside = href(page, "/riverside-county/")
    guide = href(page, BHGS_GUIDE_PATH)
    city_links = ", ".join(
        f'<a href="{e(href(page, "/riverside-county/" + c["slug"] + "/"))}">{e(c["name"])}</a>'
        for m in cities if m.get("slug") == "riverside-county" for c in m.get("cities", [])
    )
    body = f"""
    <article class="prose hero">
      <p class="kicker">Guide · Riverside County, California</p>
      <h1>Appliance repair service-call fees in Riverside County: what local shops publish</h1>
      <p class="lede">Before an appliance tech drives to your house, most will charge a service-call or diagnostic fee. Here are the fees that independent shops in our Riverside County directory publish on their own websites — {len(rows)} shops with a dollar figure, from ${lo} to ${hi} — plus what “waived with repair” means and what California requires a shop to tell you first.</p>
      <p class="note">These are each shop’s own published numbers, copied with the date we read them. They are not our prices, not quotes, and not an average of the market. Fees change; confirm the amount for your address when you call. Last checked: November 23, 2026.</p>

      <h2>Published service-call and diagnostic fees</h2>
      <p>Sorted from the lowest starting fee. Each shop name links to its profile in our directory; the source link goes to the page where the shop states the fee.</p>
      <div class="table-scroll">
      <table>
        <thead><tr><th scope="col">Shop (base)</th><th scope="col">Published fee</th><th scope="col">What the shop says</th><th scope="col">Source</th></tr></thead>
        <tbody>
          {"".join(trs)}
        </tbody>
      </table>
      </div>

      <h3>Shops that waive the fee but do not publish a number</h3>
      <ul>
        {"".join(lis)}
      </ul>

      <h2>What “waived with repair” usually means</h2>
      <p>Most of the shops above use some version of the same policy: you pay the service-call or diagnostic fee only if you decide <em>not</em> to go ahead with the repair. If you approve the repair, the fee is either dropped or credited toward the bill. The wording matters, so read it closely:</p>
      <ul>
        <li><strong>“Waived”</strong> (AV Appliance Repair, NaSh, MMO, MG Service, Solvanta): the fee goes away when the repair is done.</li>
        <li><strong>“Applied to the repair” or “applied toward labor”</strong> (TechPulse, Tim’s Fridge Repair, Quick N’ Easy): the fee counts toward the final bill. Quick N’ Easy, for example, says labor starts at $175 and that figure already includes the service call.</li>
        <li><strong>Priced by distance</strong> (Appliance Showroom in Hemet): the same visit costs $76, $109, or $129 depending on which city you live in. Tim’s Fridge Repair says mileage may be added when travel is over an hour. If you live at the edge of a shop’s area, ask.</li>
      </ul>

      <h2>What California requires (BHGS)</h2>
      <p>Appliance repair dealers in California are regulated by the Bureau of Household Goods and Services (BHGS). Its consumer guide answers the fee question directly:</p>
      <ul>
        <li><strong>Trip charges must be quoted first.</strong> BHGS says a service dealer must quote a trip charge, if any, for each service call before it happens.</li>
        <li><strong>A reasonable diagnostic fee is allowed.</strong> The dealer can charge a reasonable fee to find the problem, and charges for the actual repair work only if you agree to the repairs.</li>
        <li><strong>Written estimate before repairs.</strong> Service dealers must give you a written estimate of the cost, including the total price, before repairs.</li>
      </ul>
      <p><a href="{e(bhgs)}" rel="noopener noreferrer">Source: BHGS, A Consumer Guide to Electronic and Appliance Repair</a>. <a href="{e(law)}" rel="noopener noreferrer">Law: Business and Professions Code section 9844 (PDF)</a>. To confirm a shop is registered, follow our <a href="{e(guide)}">step-by-step BHGS lookup guide</a>.</p>

      <h2>Questions to ask when you book</h2>
      <ol>
        <li>What is the service-call or diagnostic fee to my address (give your ZIP code)?</li>
        <li>Is it waived, or credited toward the repair, if I go ahead? Is there a minimum labor charge?</li>
        <li>Is the fee different for built-in refrigerators, gas appliances, or a second appliance on the same visit?</li>
        <li>Will I get a written estimate before any repair starts?</li>
        <li>What warranty comes with the repair, and does it cover parts, labor, or both?</li>
        <li>What is your BHGS registration number? (Then look it up yourself.)</li>
      </ol>
      <p>Have the brand, model number, and a short description of the problem ready; several shops ask for it, and it helps them bring the right part.</p>

      <h2>Find a tech</h2>
      <p>Browse the <a href="{e(riverside)}">Riverside County directory</a> or go straight to a city: {city_links}. Related: <a href="{e(href(page, "/guides/repair-vs-replace/"))}">repair or replace?</a> and <a href="{e(href(page, "/compare/independent-vs-chains/"))}">independent shops vs. chains</a>.</p>

      <p class="note">Run a shop on this list and your fee changed? Or publish a fee we missed? Use the <a href="{e(href(page, "/get-listed/"))}">get listed / corrections page</a> and include the URL where the fee is posted.</p>

      <section class="sources" aria-label="Sources">
        <h2>Sources</h2>
        <ul>
          {"".join(f'<li><a href="{e(url)}" rel="noopener noreferrer">{e(by_slug[slug]["name"])} — fee page</a> (accessed {e(acc)})</li>' for slug, _f, _n, _x, url, acc in rows)}
          {"".join(f'<li><a href="{e(url)}" rel="noopener noreferrer">{e(by_slug[slug]["name"])} — fee policy</a> (accessed 2026-11-23)</li>' for slug, _x, url in no_number)}
          <li><a href="{e(bhgs)}" rel="noopener noreferrer">BHGS — A Consumer Guide to Electronic and Appliance Repair (FAQ on trip charges, diagnostic fees, written estimates)</a> (accessed 2026-11-23)</li>
        </ul>
      </section>
    </article>
    """
    desc = (
        f"Service-call and diagnostic fees published by {len(rows)} independent Riverside County appliance repair shops "
        f"(${lo}–${hi}), what ‘waived with repair’ means, and California’s BHGS rules. Sourced, dated."
    )
    faq = ld_json({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": "How much is an appliance repair service call in Riverside County?",
             "acceptedAnswer": {"@type": "Answer", "text": f"Among {len(rows)} independent Riverside County shops in our directory that publish a dollar figure, the published service-call or diagnostic fees ran from ${lo} to ${hi} when we checked in November 2026. Several shops price by distance or appliance type. Confirm the fee for your address when you call."}},
            {"@type": "Question", "name": "What does 'service call waived with repair' mean?",
             "acceptedAnswer": {"@type": "Answer", "text": "You pay the service-call or diagnostic fee only if you decline the repair. If you approve it, the shop either drops the fee or credits it toward the final bill. Ask which one applies and whether there is a minimum labor charge."}},
            {"@type": "Question", "name": "Can a California appliance repair shop charge a trip fee and a diagnostic fee?",
             "acceptedAnswer": {"@type": "Answer", "text": "BHGS says a service dealer must quote any trip charge before the service call, may charge a reasonable diagnostic fee to find the problem, and may charge for the actual repair only if you agree. Dealers must give a written estimate with the total price before repairs."}},
        ],
    })
    crumbs = [("/", "Home"), ("/riverside-county/", "Riverside County"), (FEES_PATH, "Service-call fees")]
    write_page(page, layout(page, "Appliance repair service-call fees in Riverside County (published by local shops) — Indie Appliance Repair", desc, body, "riverside-county", crumbs, extra_head=faq))


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
    page_bhgs_guide(); remember("guides/check-california-bhgs-registration/index.html")
    page_rc_fees(); remember("riverside-county/service-call-fees/index.html")
    page_compare(); remember("compare/independent-vs-chains/index.html")
    page_subzero(); remember("best/sub-zero/index.html")
    page_get_listed(); remember("get-listed/index.html")
    page_disclosure(); remember("disclosure/index.html")
    page_about(); remember("about/index.html")
    page_404()
    write_robots_and_sitemap()
    write_cname()
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    remove_do_not_list_profiles()
    print(f"Built {len(SITEMAP_PATHS)} indexable pages + 404. Listings: {len(LISTINGS)}")


def remove_do_not_list_profiles() -> None:
    """Delete leftover profile folders for shops that must stay off the site."""
    metros = [c["slug"] for c in cities]
    for entry in do_not_list:
        slug = (entry.get("slug") or entry.get("id") or "").strip()
        if not slug:
            continue
        city = (entry.get("citySlug") or "").strip()
        targets = [city] if city else metros
        for metro in targets:
            path = ROOT / metro / "techs" / slug
            if path.exists():
                shutil.rmtree(path)
                print(f"Removed do-not-list profile directory: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
