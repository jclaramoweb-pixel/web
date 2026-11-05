#!/usr/bin/env python3
"""Builds the static site.

Page bodies live in site-src/pages/*.html. Each starts with a small header block:

    ---
    title: Page title tag
    description: Meta description
    path: /charters/            (URL; the page is written to site/charters/index.html)
    nav: charters               (which top-nav item is active: charters, rates, reports, about, contact)
    trip: inshore               (optional: trip preselected in the booking widget)
    bar: trips                  (optional: mobile bar shows "View trips" instead of "Check open dates")
    noindex: yes                (optional)
    ---

This script wraps each body with the shared head, top bar, header, menus, footer,
mobile action bar and booking popup, then writes the finished pages into site/.
Run:  python3 site-src/build.py
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
PAGES = ROOT / "pages"
OUT = ROOT.parent / "site"
SITE_URL = "https://crystalriver-charters.com"

# PRE-LAUNCH SWITCH: while True, every page gets <meta name="robots" content="noindex, nofollow">,
# robots.txt disallows all crawling, and vercel.json sends an X-Robots-Tag: noindex header.
# Set to False (and rebuild) when the client approves the site to go live.
BLOCK_INDEXING = True

PHONE = "(352) 577-4084"
TEL = "tel:+13525774084"
SMS = "sms:+13525774084"
EMAIL = "captaintannermartin@gmail.com"

# Social / review profile links. Paste the real URLs here; a link left blank is hidden.
SOCIAL = {
    "facebook": "",
    "instagram": "",
    "tripadvisor": "",
    "yelp": "",
}

TRIPS = [
    # key, name, short name, url, image, price, mega meta, mobile meta, sheet meta
    dict(key="inshore", name="Inshore charter", url="/charters/inshore-fishing/", img="b-trip-inshore.jpg",
         price="From $600", mega="4 or 7 hrs · up to 4", mm="From $600 · redfish, trout, snook · year-round",
         sheet="4 or 7 hrs • up to 4 anglers"),
    dict(key="fly", name="Fly & light tackle", url="/charters/fly-fishing/", img="b-trip-fly.jpg",
         price="From $600", mega="4 or 7 hrs · 1 or 2", mm="From $600 · sight fishing · year-round",
         sheet="4 or 7 hrs • 1 or 2 anglers", mmname="Backcountry fly & light tackle"),
    dict(key="tarpon", name="Homosassa tarpon", url="/charters/homosassa-tarpon/", img="b-trip-tarpon.jpg",
         price="$900", mega="8 hrs · up to 2", mm="$900 · mid-April to July", sheet="8 hrs • Apr to Jul"),
    dict(key="scalloping", name="Scalloping", url="/charters/scalloping/", img="b-trip-scalloping.jpg",
         price="From $600", mega="Jul to Sep · up to 6", mm="From $600 · July to September", sheet="Jul to Sep • up to 6"),
    dict(key="duck", name="Duck hunts", url="/charters/duck-hunting/", img="b-trip-duck.jpg",
         price="$500", mega="Nov to Jan · 2 hunters", mm="$500 · mid-Nov to January", sheet="Nov to Jan • 2 hunters"),
    dict(key="mud", name="Mud boat trip", url="/charters/mud-boat-fishing/", img="mud-main.jpg",
         price="From $500", mega="Nov to Feb · up to 3", mm="From $500 · Nov to Feb · backcountry creeks",
         sheet="4 to 6 hrs • Nov to Feb"),
]

PLAN = [
    ("Where we fish", "/where-we-fish/", "Kings Bay, Ozello, Homosassa · by season", "b-map.jpg"),
    ("Where we meet", "/where-we-meet/", "Pete’s Pier · MacRae’s of Homosassa · drive times", "b-map.jpg"),
    ("Scalloping season", "/scalloping-season/", "Dates, limits and what to bring", "b-trip-scalloping.jpg"),
    ("Tarpon season", "/tarpon-season/", "When the silver kings show up", "b-trip-tarpon.jpg"),
    ("Fishing reports", "/crystal-river-fishing-reports/", "Latest from the water", "flats-class-thumb.jpg"),
]

REPORTS = [  # newest first; used by the mega menu
    ("Late Summer 2026", "/crystal-river-fishing-reports/late-summer-2026/", "Oversized redfish on the flats and the last weeks of scallop season.", "b-trip-scalloping.jpg"),
    ("June 2026", "/crystal-river-fishing-reports/june-2026/", "Tarpon stayed outstanding from early April through the end of June.", "b-trip-tarpon.jpg"),
    ("November 2025", "/crystal-river-fishing-reports/november-2025/", "Bait is moving, heat is gone, the fall shift on the Nature Coast.", "b-trip-inshore.jpg"),
]

NAV = [
    ("rates", "Rates", "/rates/"),
    ("reports", "Fishing Reports", "/crystal-river-fishing-reports/"),
    ("about", "About Capt. Tanner", "/about/"),
    ("contact", "Contact", "/contact/"),
]

ICON = {
    "facebook": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13.5 22v-8h2.7l.4-3.2h-3.1V8.8c0-.9.3-1.5 1.6-1.5h1.7V4.4c-.3 0-1.3-.1-2.5-.1-2.4 0-4.1 1.5-4.1 4.2v2.3H7.5V14h2.7v8h3.3z"/></svg>',
    "instagram": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 7.3a4.7 4.7 0 1 0 0 9.4 4.7 4.7 0 0 0 0-9.4zm0 7.7a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm6-7.9a1.1 1.1 0 1 1-2.2 0 1.1 1.1 0 0 1 2.2 0zM21.9 8c-.1-1.6-.4-3-1.6-4.2S17.6 2.2 16 2.1C14.4 2 9.6 2 8 2.1 6.4 2.2 5 2.5 3.8 3.7S2.2 6.4 2.1 8C2 9.6 2 14.4 2.1 16c.1 1.6.4 3 1.6 4.2s2.6 1.5 4.2 1.6c1.6.1 6.4.1 8 0 1.6-.1 3-.4 4.2-1.6s1.5-2.6 1.6-4.2c.1-1.6.1-6.4 0-8zm-2.1 9.7a3.3 3.3 0 0 1-1.8 1.8c-1.3.5-4.3.4-5.7.4s-4.4.1-5.7-.4a3.3 3.3 0 0 1-1.8-1.8c-.5-1.3-.4-4.3-.4-5.7s-.1-4.4.4-5.7a3.3 3.3 0 0 1 1.8-1.8c1.3-.5 4.3-.4 5.7-.4s4.4-.1 5.7.4a3.3 3.3 0 0 1 1.8 1.8c.5 1.3.4 4.3.4 5.7s.1 4.4-.4 5.7z"/></svg>',
    "tripadvisor": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 6.6c-2.3 0-4.6.6-6.4 1.9H2l1.4 1.6a4.6 4.6 0 1 0 6.3 6.6L12 19l2.3-2.3a4.6 4.6 0 1 0 6.3-6.6L22 8.5h-3.6A11.4 11.4 0 0 0 12 6.6zM6.9 16.3a2.8 2.8 0 1 1 0-5.6 2.8 2.8 0 0 1 0 5.6zm10.2 0a2.8 2.8 0 1 1 0-5.6 2.8 2.8 0 0 1 0 5.6zm-10.2-4a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4zm10.2 0a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4zM12 8.4c1.2 0 2.4.2 3.5.7a4.6 4.6 0 0 0-3.5 4.4 4.6 4.6 0 0 0-3.5-4.4c1.1-.5 2.3-.7 3.5-.7z"/></svg>',
    "yelp": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11.2 2.3c-.6-.4-4.5.7-5.3 1.5-.3.3-.4.7-.3 1l3.9 6.6c.5.8 1.8.5 1.8-.5V2.9c0-.3-.1-.5-.1-.6zM10 14.7l-4.4 1.2c-.6.2-.8.6-.7 1.1.2 1.3 1.5 3.1 2.6 3.6.4.2.8.1 1.1-.2l3-3.3c.6-.7 0-1.8-.9-1.7l-.7.3zm1.6-2.4 6.4-2.1c.6-.2.8-.8.5-1.3-.6-1.1-2-2.5-3.1-2.9-.4-.1-.8 0-1.1.3l-3.7 5.2c-.5.7.2 1.6 1 1.3v-.5zm7 2.6-4.2-1.4c-.9-.3-1.6.7-1.1 1.4l2.4 3.8c.3.4.8.5 1.2.3 1-.6 2.1-2 2.3-3.1 0-.5-.2-.9-.6-1z"/></svg>',
}

CHEVRON = '<svg width="12" height="7" viewBox="0 0 12 7" aria-hidden="true"><path d="M1 1l5 5 5-5" fill="none" stroke="currentColor" stroke-width="2"/></svg>'
X_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" aria-hidden="true"><path d="M5 5l14 14M19 5L5 19"/></svg>'
MENU_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg>'


def esc(s):
    return html.escape(s, quote=True)


def social_links(cls=""):
    out = []
    for k, label in (("facebook", "Facebook"), ("instagram", "Instagram"), ("tripadvisor", "Tripadvisor"), ("yelp", "Yelp")):
        if SOCIAL[k]:
            out.append(f'<a href="{SOCIAL[k]}" target="_blank" rel="noopener" aria-label="{label}">{ICON[k]}</a>')
    return "".join(out)


def text_socials(keys=("facebook", "instagram"), cls=""):
    return "".join(f'<a class="{cls}" href="{SOCIAL[k]}" target="_blank" rel="noopener">{k.capitalize() if k != "tripadvisor" else "Tripadvisor"}</a>'
                   for k in keys if SOCIAL[k])


def header(meta):
    nav = meta.get("nav", "")
    cur_path = meta["path"]
    items = []
    charters_active = ' class="is-active"' if nav == "charters" else ""
    items.append(f'<li><button type="button" id="mega-btn" aria-expanded="false" aria-controls="mega"{charters_active}>Charters {CHEVRON}</button></li>')
    for key, label, url in NAV:
        cur = ' aria-current="page"' if cur_path == url else (' class="is-active"' if nav == key else "")
        items.append(f'<li><a href="{url}"{cur}>{label}</a></li>')

    mega_trips = "".join(
        f'<a class="mega-trip" href="{t["url"]}"><span><b>{esc(t["name"])}</b><small>{esc(t["mega"])}</small></span><em>{t["price"]}</em></a>'
        for t in TRIPS)
    species = [("Speckled trout", "Inshore · year-round", "b-trip-inshore.jpg", "/charters/inshore-fishing/"),
               ("Redfish", "Inshore · Aug to Oct peak", "b-trip-fly.jpg", "/charters/fly-fishing/"),
               ("Tarpon", "Homosassa · mid-Apr to Jul", "b-trip-tarpon.jpg", "/charters/homosassa-tarpon/"),
               ("Scallops", "Jul to Sep", "b-trip-scalloping.jpg", "/charters/scalloping/"),
               ("Ducks", "mid-Nov to Jan", "b-trip-duck.jpg", "/charters/duck-hunting/")]
    species_html = "".join(f'<a href="{u}"><img src="/img/{i}" alt="" loading="lazy" width="118" height="88"><b>{n}</b><small>{m}</small></a>' for n, m, i, u in species)
    plan_html = "".join(f'<a href="{u}">{n}&nbsp;›</a>' for n, u, _, _ in PLAN[:4])
    reports_html = "".join(
        f'<a class="mega-report" href="{u}"><img src="/img/{i}" alt="" loading="lazy" width="88" height="66"><span><small>Fishing report</small><b>{n}</b><span>{d}</span></span></a>'
        for n, u, d, i in REPORTS)

    socials = text_socials()
    topbar = f'''<div class="topbar"><div class="wrap">
  <div class="left"><span class="stars" aria-hidden="true">★★★★★</span><strong>5.0 on Tripadvisor</strong><span class="dot" aria-hidden="true">•</span><span>Pete's Pier, Crystal River &nbsp;•&nbsp; MacRae's of Homosassa</span></div>
  <div class="right"><span>Licenses included on every fishing trip</span>{socials}</div>
</div></div>'''

    return f'''{topbar}
<header class="site-header" id="top">
  <div class="header-main"><div class="wrap">
    <a class="brand" href="/" aria-label="Florida's On The Fly Charters, home">
      <img class="navy" src="/img/logo-navy.png" alt="" width="66" height="58">
      <img class="white" src="/img/logo-white.png" alt="" width="66" height="58">
      <span><span class="brand-name">Florida's On The Fly</span><span class="brand-sub"><span class="bs-x">Charters  •  </span>Crystal River, FL</span></span>
    </a>
    <nav class="main-nav" aria-label="Main"><ul>{"".join(items)}</ul></nav>
    <div class="header-cta">
      <a class="header-phone" href="{TEL}"><b>{PHONE}</b><span>Call or text Capt. Tanner</span></a>
      <button class="btn btn-blue btn-sm" type="button" data-open="booking">Check open dates</button>
    </div>
    <button class="book-mini" type="button" data-open="booking">Book</button>
    <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="mobile-menu" aria-label="Open menu">{MENU_ICON}</button>
  </div></div>
  <div class="mega" id="mega" role="region" aria-label="Charters menu"><div class="wrap">
    <div class="mega-trips">
      <span class="mega-label">Private trips</span>
      {mega_trips}
      <p class="mega-note">Per group, not per person. Licenses, rods, reels and tackle included.</p>
      <div class="mega-links"><a href="/charters/">View all trips&nbsp; ›</a><a href="/homosassa-fishing-charters/">Fishing out of Homosassa&nbsp; ›</a><a href="/corporate-fishing-trips/">Corporate &amp; group trips&nbsp; ›</a></div>
    </div>
    <div class="mega-mid">
      <span class="mega-label">Fish by species</span>
      <div class="species">{species_html}</div>
      <div class="plan-links"><span class="mega-label">Plan your trip</span>{plan_html}</div>
      <div class="mega-reports-head"><span class="mega-label">Latest fishing reports</span><a href="/crystal-river-fishing-reports/">All reports&nbsp; ›</a></div>
      <div class="mega-reports">{reports_html}</div>
    </div>
    <div class="mega-cta">
      <h3>Know your dates?</h3>
      <p>See open dates and book online. One price per group. $100 deposit holds your day.</p>
      <button class="btn btn-blue" type="button" data-open="booking">Check open dates</button>
      <a class="btn btn-ghost" href="{TEL}">Call now</a>
      <small>{PHONE} · 7 AM start in summer, 8 AM fall and winter</small>
    </div>
  </div></div>
</header>
<div class="mega-scrim" id="mega-scrim"></div>
{mobile_menu(meta)}'''


def mobile_menu(meta):
    cur = meta["path"]

    def row(name, url, small, img, round_=False):
        c = ' aria-current="page"' if url == cur else ""
        im = f'<img src="/img/{img}" alt="" loading="lazy"{' class="round"' if round_ else ""}>' if img else ""
        return f'<a class="mm-row" href="{url}"{c}>{im}<div><b>{esc(name)}</b><small>{esc(small)}</small></div></a>'

    trips = "".join(row(t.get("mmname", t["name"]), t["url"], t["mm"], t["img"]) for t in TRIPS)
    trips += row("View all trips", "/charters/", "Rates, what’s included, deposit and weather", None)
    trips += row("Rates", "/rates/", "Every trip and price on one page", None)
    plan = "".join(row(n, u, s, i) for n, u, s, i in PLAN)
    about = row("Capt. Tanner Martin", "/about/", "Born and raised on the Nature Coast · since 2018", "tanner-headshot.png", True)
    about += row("Homosassa fishing charters", "/homosassa-fishing-charters/", "Tarpon, inshore and scallops out of MacRae’s", None)
    about += row("Corporate & group trips", "/corporate-fishing-trips/", "Several boats, one dock, priced per boat", None)
    about += row("Contact us", "/contact/", "Call, text or send a message", None)
    socials = text_socials(("facebook", "instagram", "tripadvisor"), "s")
    return f'''<div class="mobile-menu" id="mobile-menu" role="dialog" aria-modal="true" aria-label="Menu">
  <div class="mm-head">
    <div class="mm-strip">Licenses included on every fishing trip &nbsp;•&nbsp; Pete's Pier, Crystal River</div>
    <div class="mm-bar">
      <a class="brand" href="/"><img src="/img/logo-navy.png" alt="" width="50" height="44"><span><span class="brand-name">Florida's On The Fly</span><span class="brand-sub">Crystal River, FL</span></span></a>
      <span style="display:flex;gap:10px;align-items:center">
        <button class="book-mini" style="display:inline-flex" type="button" data-open="booking">Book</button>
        <button class="menu-close" type="button" aria-label="Close menu" style="width:44px;height:44px;display:grid;place-items:center;background:var(--navy);color:#fff"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 5l14 14M19 5L5 19"/></svg></button>
      </span>
    </div>
  </div>
  <div class="mm-body">
    <div class="mm-actions"><button class="btn btn-blue" type="button" data-open="booking">Check open dates</button><a class="btn btn-navy" href="{TEL}">Call {PHONE}</a></div>
    <div class="mm-group"><h2>Fishing charters</h2>{trips}</div>
    <div class="mm-group"><h2>Plan your trip</h2>{plan}</div>
    <div class="mm-group"><h2>About</h2>{about}</div>
    <div class="mm-foot">Pete's Pier, Crystal River, FL &nbsp;•&nbsp; MacRae's of Homosassa, FL<br><a href="mailto:{EMAIL}">{EMAIL}</a><br>{socials}</div>
  </div>
</div>'''


def footer():
    charters = "".join(f'<a href="{u}">{n}</a>' for n, u in [
        ("Inshore charter", "/charters/inshore-fishing/"), ("Backcountry fly & light tackle", "/charters/fly-fishing/"),
        ("Homosassa tarpon", "/charters/homosassa-tarpon/"), ("Crystal River scalloping", "/charters/scalloping/"),
        ("Duck hunts", "/charters/duck-hunting/"), ("Mud boat trip", "/charters/mud-boat-fishing/"),
        ("Homosassa fishing charters", "/homosassa-fishing-charters/"), ("Corporate & group trips", "/corporate-fishing-trips/"),
        ("Rates & what’s included", "/rates/")])
    plan = "".join(f'<a href="{u}">{n}</a>' for n, u in [
        ("Where we meet", "/where-we-meet/"), ("Where we fish", "/where-we-fish/"), ("Scalloping season", "/scalloping-season/"),
        ("Tarpon season", "/tarpon-season/"), ("Fishing reports", "/crystal-river-fishing-reports/"),
        ("About Capt. Tanner", "/about/"), ("Contact", "/contact/")])
    socials = social_links()
    socials_html = f'<div class="socials">{socials}</div>' if socials else ""
    return f'''<footer class="footer">
  <div class="footer-cta"><div class="wrap">
    <div><h2>Ready to fish the Nature Coast?</h2><p>Check open dates and book in two minutes, or call Capt. Tanner.</p></div>
    <div class="btn-row"><button class="btn btn-white btn-sm" type="button" data-open="booking">Check open dates</button><a class="btn btn-ghost btn-sm" href="{TEL}">Call {PHONE}</a></div>
  </div></div>
  <div class="footer-main"><div class="wrap">
    <div class="f-about">
      <a class="brand" href="/"><img src="/img/logo-white.png" alt="" width="72" height="63"><span><span class="brand-name">Florida's On The Fly</span><span class="brand-sub">Charters  •  Crystal River, FL</span></span></a>
      <p>Private fishing charters, scalloping and duck hunts out of Crystal River and Homosassa on Florida’s Nature Coast. Capt. Tanner Martin, born and raised here, guiding since 2018.</p>
      <div class="rating"><span class="stars" aria-hidden="true">★★★★★</span><b>5.0 on Tripadvisor</b></div>
      {socials_html}
    </div>
    <div class="f-cols">
      <nav class="f-col" aria-label="Fishing charters"><h3>Fishing charters</h3>{charters}</nav>
      <nav class="f-col" aria-label="Plan your trip"><h3>Plan your trip</h3>{plan}</nav>
    </div>
    <div class="f-contact">
      <h3>Book your trip</h3>
      <div><a href="{TEL}">{PHONE}</a><span>Call or text, 7 days</span></div>
      <div><a href="mailto:{EMAIL}">{EMAIL}</a><span>Email</span></div>
      <div><a href="/where-we-meet/">Pete's Pier, Crystal River, FL</a><span>Inshore, fly &amp; scallop trips</span></div>
      <div><a href="/where-we-meet/">MacRae's of Homosassa, FL</a><span>Tarpon trips</span></div>
    </div>
  </div></div>
  <div class="footer-legal"><div class="wrap">
    <span>© 2026 Florida’s On The Fly Charters &nbsp;•&nbsp; Florida License #M635816994170</span>
    <span><a href="/privacy/">Privacy Policy</a> &nbsp;•&nbsp; <a href="/accessibility/">Accessibility</a> &nbsp;•&nbsp; Website by FishySites</span>
  </div></div>
</footer>'''


def sheets(meta):
    trip = meta.get("trip", "")
    picks = "".join(
        f'<a class="pick-row" href="{t["url"]}"><img src="/img/{t["img"]}" alt="" loading="lazy"><div><b>{esc(t["name"].capitalize())}</b><small>{esc(t["sheet"])}</small></div><em>{t["price"]}</em></a>'
        for t in TRIPS)
    return f'''<div class="sheet sheet-booking" id="sheet-booking" role="dialog" aria-modal="true" aria-label="Check open dates">
  <div class="scrim" data-close></div>
  <div class="panel"><button class="close" type="button" data-close aria-label="Close">{X_ICON}</button><div class="widget" data-widget data-trip="{trip}"></div></div>
</div>
<div class="sheet sheet-trips" id="sheet-trips" role="dialog" aria-modal="true" aria-label="Pick your trip">
  <div class="scrim" data-close></div>
  <div class="panel"><button class="close" type="button" data-close aria-label="Close">{X_ICON}</button>
    <h2>Pick your trip</h2><p class="sub">Tap a trip for details, dates and booking</p>
    {picks}
    <div class="sheet-foot"><a href="/charters/">View all trips&nbsp;›</a><a href="{TEL}">Not sure? Call {PHONE}</a></div>
  </div>
</div>
<div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Photo viewer"><button class="lb-close" type="button" aria-label="Close">×</button><button class="lb-prev" type="button" aria-label="Previous photo">‹</button><button class="lb-next" type="button" aria-label="Next photo">›</button></div>'''


def mbar(meta):
    if meta.get("bar") == "dock":
        return (f'<div class="mbar dock"><button class="dock-info" type="button" data-open="booking"><b>{esc(meta.get("dock_name", ""))} ⌃</b>'
                f'<small>{esc(meta.get("dock_meta", ""))}</small></button><a class="dock-call" href="{TEL}">Call</a>'
                f'<button class="dock-book" type="button" data-open="booking">Book</button></div>')
    if meta.get("bar") == "trips":
        return f'<div class="mbar"><a href="{TEL}">Call now</a><button type="button" data-open="trips">View trips</button></div>'
    return f'<div class="mbar"><a href="{TEL}">Call</a><button type="button" data-open="booking">Check open dates</button></div>'


LOCAL_BUSINESS = {
    "@context": "https://schema.org", "@type": "LocalBusiness", "name": "Florida's On The Fly Charters",
    "url": SITE_URL + "/", "telephone": "+1-352-577-4084", "email": EMAIL,
    "image": SITE_URL + "/img/b2-hero.jpg",
    "address": {"@type": "PostalAddress", "addressLocality": "Crystal River", "addressRegion": "FL", "addressCountry": "US"},
    "areaServed": ["Crystal River, FL", "Homosassa, FL"],
    "founder": {"@type": "Person", "name": "Capt. Tanner Martin"},
}


def page(meta, body):
    title = meta["title"]
    desc = meta.get("description", "")
    path = meta["path"]
    canonical = SITE_URL + path
    robots = '<meta name="robots" content="noindex, nofollow">' if (BLOCK_INDEXING or meta.get("noindex")) else ""
    schema = ""
    if path == "/":
        schema = LOCAL_BUSINESS
    elif meta.get("schema") == "homosassa":
        schema = dict(LOCAL_BUSINESS, areaServed=["Homosassa, FL", "Crystal River, FL"],
                      location={"@type": "Place", "name": "MacRae's of Homosassa", "address": {"@type": "PostalAddress", "streetAddress": "5290 S Cherokee Way", "addressLocality": "Homosassa", "addressRegion": "FL", "postalCode": "34448", "addressCountry": "US"}})
    elif meta.get("schema") == "meet":
        schema = dict(LOCAL_BUSINESS, location=[
            {"@type": "Place", "name": "Pete's Pier", "address": {"@type": "PostalAddress", "streetAddress": "1 SW 1st Place", "addressLocality": "Crystal River", "addressRegion": "FL", "postalCode": "34428", "addressCountry": "US"}},
            {"@type": "Place", "name": "MacRae's of Homosassa", "address": {"@type": "PostalAddress", "streetAddress": "5290 S Cherokee Way", "addressLocality": "Homosassa", "addressRegion": "FL", "postalCode": "34448", "addressCountry": "US"}}])
    schema = f'<script type="application/ld+json">{json.dumps(schema)}</script>' if schema else ""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{robots}
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE_URL}/img/{meta.get("og", "b2-hero.jpg")}">
<meta name="theme-color" content="#072c3d">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.png" type="image/png" sizes="64x64">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Antonio:wght@400;700&family=Barlow:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/styles.css">
{schema}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{header(meta)}
<main id="main">
{body}
</main>
{footer()}
{mbar(meta)}
{sheets(meta)}
<script src="/js/site.js" defer></script>
</body>
</html>
'''


MAP_HTML = """<div class="map" role="img" aria-label="Map of Crystal River and Homosassa showing Pete's Pier and MacRae's">
  <div class="pin" style="left:50%;top:28%"><a href="/where-we-meet/#petes-pier"><b>Pete's Pier, Crystal River</b><small>Inshore, fly &amp; scallop trips</small></a></div>
  <div class="pin" style="left:46.9%;top:69%"><a href="/where-we-meet/#macraes"><b>MacRae's of Homosassa</b><small>Tarpon trips</small></a></div>
  <div class="drive"><b>Drive to Crystal River (approx.)</b><p>Ocala 50 min &nbsp;•&nbsp; The Villages 1 hr &nbsp;•&nbsp; Gainesville 1 hr 20<br>Tampa 1 hr 30 &nbsp;•&nbsp; Orlando 1 hr 45</p>
    <div class="links"><a href="https://www.google.com/maps/search/?api=1&amp;query=Pete%27s+Pier+Crystal+River+FL" target="_blank" rel="noopener">Directions to Pete's Pier&nbsp; ›</a><a href="https://www.google.com/maps/search/?api=1&amp;query=MacRae%27s+of+Homosassa+FL" target="_blank" rel="noopener">Directions to MacRae's&nbsp; ›</a></div></div>
  <span class="credit">© OpenStreetMap contributors</span>
</div>"""


SIDECARDS_HTML = """<div class="side-card"><div class="who"><img src="/img/tanner-headshot.png" alt="" width="56" height="56"><div><h3>Not sure which trip?</h3><span>Capt. Tanner Martin  •  owner and guide</span></div></div>
<p>Call or text Tanner at <a class="text-link" href="tel:+13525774084">(352) 577-4084</a> with your dates and group size. He will match you to the right trip for the season and tell you straight if the fishing is off.</p></div>
<div class="policies"><span class="label">Good to know</span><dl>
<dt>Deposit</dt><dd>$100 holds the date, balance after the trip</dd>
<dt>Cancellation</dt><dd>Free outside 14 days; inside 14 days credited to a future trip</dd>
<dt>Weather</dt><dd>Captain’s call: full refund or reschedule</dd>
<dt>Payment</dt><dd>Cash or card (3.5% card fee)</dd>
<dt>Tip</dt><dd>20% customary, cash preferred</dd></dl></div>"""


REVIEWS_HTML = """<section class="sec bg-navy on-dark" id="reviews" aria-labelledby="h-reviews">
  <div class="wrap">
    <div class="sec-head center">
      <p class="eyebrow">★ &nbsp;5.0 Star Rating on Google</p>
      <h2 class="h2" id="h-reviews">Crystal River fishing charter reviews</h2>
      <hr class="rule">
    </div>
    <div class="reviews-grid">
      <figure class="review-feature" style="margin:0">
        <h3>“The best trip I’ve ever had!”</h3>
        <blockquote style="margin:0"><p>Capt. Tanner was able to put me on my first snook and first tarpon. 100% recommend and will be booking him again very soon!!</p></blockquote>
        <figcaption class="who"><span>Jacob G. &nbsp;•&nbsp; Solo trip &nbsp;•&nbsp; Sept 2025</span><span class="stars" aria-label="5 stars">★★★★★</span></figcaption>
      </figure>
      <div class="review-cards">
        <figure class="review-card" style="margin:0"><h3>“Amazing trip!”</h3><p>The captain was so knowledgeable regarding everything. He knew about the plant life as well as marine life. He knew the water channels like the back of his hand.</p><figcaption class="who"><span>Sherry T.</span><span class="stars" aria-label="5 stars">★★★★★</span></figcaption></figure>
        <figure class="review-card" style="margin:0"><h3>“The best day!”</h3><p>Tanner was very knowledgeable and took us right to the fish! He spent a lot of time explaining our surroundings and was very personable.</p><figcaption class="who"><span>Reneholt4</span><span class="stars" aria-label="5 stars">★★★★★</span></figcaption></figure>
        <figure class="review-card" style="margin:0"><h3>“Perfect”</h3><p>Captain Martin is a wonderful guide and host. His knowledge of these waters is incredible and he always has ways to adapt to changing conditions.</p><figcaption class="who"><span>Mitchell W.</span><span class="stars" aria-label="5 stars">★★★★★</span></figcaption></figure>
        <figure class="review-card" style="margin:0"><h3>“Excellent Charter”</h3><p>Captain Tanner Martin was raised on the river. Knows the area better than anyone. Works hard to make sure you get a good catch.</p><figcaption class="who"><span>Josh Y.</span><span class="stars" aria-label="5 stars">★★★★★</span></figcaption></figure>
      </div>
    </div>
    <!--tripadvisor--><div class="center-row"><a class="btn btn-ghost-soft" href="{{TRIPADVISOR}}" target="_blank" rel="noopener">Read every review on Tripadvisor</a></div><!--/tripadvisor-->
  </div>
</section>
"""


def fill(body):
    body = body.replace("{{REVIEWS}}", REVIEWS_HTML).replace("{{MAP}}", MAP_HTML).replace("{{SIDECARDS}}", SIDECARDS_HTML)
    if SOCIAL["tripadvisor"]:
        body = body.replace("{{TRIPADVISOR}}", SOCIAL["tripadvisor"])
    else:
        body = re.sub(r"<!--tripadvisor-->.*?<!--/tripadvisor-->", "", body, flags=re.S)
    if SOCIAL["instagram"]:
        body = body.replace("{{INSTAGRAM}}", SOCIAL["instagram"])
    else:
        body = re.sub(r"<!--instagram-->.*?<!--/instagram-->", "", body, flags=re.S)
    return (body.replace("{{TEL}}", TEL).replace("{{SMS}}", SMS)
                .replace("{{PHONE}}", PHONE).replace("{{EMAIL}}", EMAIL))


def tidy(doc):
    """Final clean-up so every page validates: encode stray ampersands outside <script>,
    give star ratings an image role, type every <input>, strip trailing spaces."""
    parts = re.split(r"(<script\b.*?</script>)", doc, flags=re.S)
    for i in range(0, len(parts), 2):
        t = re.sub(r"&(?![a-zA-Z][a-zA-Z0-9]*;|#[0-9]+;|#x[0-9a-fA-F]+;)", "&amp;", parts[i])
        t = t.replace('class="stars" aria-label=', 'class="stars" role="img" aria-label=')
        t = re.sub(r"<input(?![^>]*\btype=)", '<input type="text"', t)
        parts[i] = t
    return "\n".join(line.rstrip() for line in "".join(parts).split("\n"))


def parse(src):
    m = re.match(r"---\n(.*?)\n---\n", src, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, src[m.end():]


def main():
    count = 0
    for f in sorted(PAGES.glob("*.html")):
        meta, body = parse(f.read_text(encoding="utf-8"))
        out_html = tidy(page(meta, fill(body)))
        path = meta["path"]
        if path == "/404/":
            target = OUT / "404.html"
        else:
            target = OUT / path.strip("/") / "index.html" if path != "/" else OUT / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out_html, encoding="utf-8")
        count += 1
    write_robots()
    print(f"Built {count} pages into {OUT}")


def write_robots():
    if BLOCK_INDEXING:
        txt = "# Pre-launch: keep this site out of search engines.\nUser-agent: *\nDisallow: /\n"
    else:
        txt = f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n"
    (OUT / "robots.txt").write_text(txt, encoding="utf-8")
    vj = OUT / "vercel.json"
    if vj.exists():
        cfg = json.loads(vj.read_text(encoding="utf-8"))
        cfg["headers"] = [h for h in cfg.get("headers", []) if h.get("source") != "/(.*)" or not any(x["key"] == "X-Robots-Tag" for x in h["headers"])]
        if BLOCK_INDEXING:
            cfg["headers"].insert(0, {"source": "/(.*)", "headers": [{"key": "X-Robots-Tag", "value": "noindex, nofollow"}]})
        vj.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
