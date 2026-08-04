#!/usr/bin/env python3
"""Render every Markdown file in the repo to a standalone HTML page.

Output goes to docs_html/, mirroring the source directory layout, plus a
generated docs_html/index.html linking to every page.

The output is a self-contained (no external requests) documentation site with:
  * a persistent, collapsible left-nav sidebar (grouped by track/service) with
    a live filter box,
  * a reading-progress bar, breadcrumbs, and prev/next pager,
  * a right-hand "on this page" TOC with scroll-spy,
  * IDE-style code blocks with copy buttons + language badges,
  * auto-styled [Documented] / [Inferred] epistemic badges,
  * a light/dark theme (no flash-of-wrong-theme), and
  * GitHub-compatible heading anchors so in-page `#slug` links resolve.
"""

import html
import pathlib
import re
from itertools import groupby

from markdown_it import MarkdownIt

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "docs_html"

EXCLUDE_DIRS = {".venv", ".git", "docs_html", "__pycache__"}

SITE_NAME = "AWS &amp; GCP Mastery"

# Nice labels for path tokens used in nav groups + breadcrumbs.
TOKEN_LABELS = {
    "aws": "AWS", "gcp": "GCP", "azure": "Azure",
    "vpc": "VPC", "iam": "IAM", "s3": "S3", "ec2": "EC2", "ebs": "EBS",
    "rds": "RDS", "kms": "KMS", "elb": "ELB", "dynamodb": "DynamoDB",
    "docs": "Docs", "quizzes": "Quizzes", "labs": "Labs", "notes": "Notes",
    "terraform": "Terraform", "cloudformation": "CloudFormation",
    "cdk": "CDK", "boto3": "Boto3", "python": "Python",
    "cheatsheets": "Cheatsheets", "diagrams": "Diagrams",
}

# Runs in <head> before paint so the theme never flashes.
BOOT = (
    "(function(){try{var t=localStorage.getItem('cm-theme');"
    "if(!t){t=(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)')"
    ".matches)?'dark':'light';}"
    "document.documentElement.setAttribute('data-theme',t);}catch(e){}})();"
)

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &middot; {site}</title>
<script>{boot}</script>
<style>{css}</style>
</head>
<body>
<div class="progress" id="progress"></div>
<header class="topbar">
  <button class="menu-btn" id="menu-btn" type="button" aria-label="Toggle navigation">&#9776;</button>
  <a class="brand" href="{index_href}"><span class="brand-mark">&#9729;</span> {site}</a>
  <div class="topbar-actions">
    <a class="topbar-link" href="{index_href}">Home</a>
    <button id="theme-toggle" class="theme-toggle" type="button" aria-label="Toggle theme">&#9789;</button>
  </div>
</header>
<div class="scrim" id="scrim"></div>
<div class="shell">
  <aside class="sidebar" id="sidebar" aria-label="Site navigation">
    <input id="nav-filter" class="nav-filter" type="search" placeholder="Filter pages  ( / )" autocomplete="off">
    <nav class="nav">{sidebar}</nav>
  </aside>
  <main class="content" id="content">
    <nav class="breadcrumbs">{breadcrumbs}</nav>
{body}
    <nav class="pager">{pager}</nav>
  </main>
  <aside class="toc" id="toc" aria-label="On this page"></aside>
</div>
<footer class="site-footer">Rendered from Markdown &middot; {site}</footer>
<script>{js}</script>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{site} &middot; Docs</title>
<script>{boot}</script>
<style>{css}</style>
</head>
<body>
<div class="progress" id="progress"></div>
<header class="topbar">
  <button class="menu-btn" id="menu-btn" type="button" aria-label="Toggle navigation">&#9776;</button>
  <a class="brand" href="index.html"><span class="brand-mark">&#9729;</span> {site}</a>
  <div class="topbar-actions">
    <button id="theme-toggle" class="theme-toggle" type="button" aria-label="Toggle theme">&#9789;</button>
  </div>
</header>
<div class="scrim" id="scrim"></div>
<div class="shell shell--home">
  <aside class="sidebar" id="sidebar" aria-label="Site navigation">
    <input id="nav-filter" class="nav-filter" type="search" placeholder="Filter pages  ( / )" autocomplete="off">
    <nav class="nav">{sidebar}</nav>
  </aside>
  <main class="content home" id="content">
    <section class="hero">
      <span class="hero-badge">Architecture &amp; Internals &middot; not certs</span>
      <h1>{site}</h1>
      <p class="hero-sub">Deep-dives across <strong>AWS</strong> and <strong>GCP</strong>
      &mdash; why each service exists, how it's built inside, and the networking,
      storage, security, and production patterns behind it.</p>
      <input id="doc-filter" class="doc-filter" type="search" placeholder="Search all pages&hellip;" autocomplete="off">
    </section>
{body}
  </main>
</div>
<footer class="site-footer">Rendered from Markdown &middot; {site}</footer>
<script>{js}</script>
</body>
</html>
"""

CSS = """
:root {
  --bg: #ffffff;
  --bg-soft: #f6f7f9;
  --surface: #ffffff;
  --surface-2: #eef1f5;
  --text: #1f2328;
  --muted: #5b6472;
  --border: #e3e7ed;
  --accent: #6366f1;
  --accent-soft: rgba(99, 102, 241, 0.12);
  --accent-2: #0ea5e9;
  --ok: #059669; --ok-soft: rgba(16,185,129,.14);
  --warn: #b45309; --warn-soft: rgba(245,158,11,.14);
  --code-bg: #1e293b;
  --code-text: #e2e8f0;
  --shadow: 0 1px 2px rgba(16,24,40,.05), 0 10px 26px rgba(16,24,40,.06);
  --radius: 14px;
  --topbar-h: 56px;
}
:root[data-theme="dark"] {
  --bg: #0b0f17;
  --bg-soft: #0b0f17;
  --surface: #121826;
  --surface-2: #182031;
  --text: #e6edf3;
  --muted: #9aa4b2;
  --border: #243044;
  --accent: #8b93ff;
  --accent-soft: rgba(139, 147, 255, 0.16);
  --accent-2: #38bdf8;
  --ok: #6ee7b7; --ok-soft: rgba(16,185,129,.16);
  --warn: #fcd34d; --warn-soft: rgba(245,158,11,.16);
  --code-bg: #0d1424;
  --code-text: #e2e8f0;
  --shadow: 0 1px 2px rgba(0,0,0,.4), 0 14px 34px rgba(0,0,0,.4);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 72px; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 17px; line-height: 1.7; color: var(--text);
  background: var(--bg-soft); -webkit-font-smoothing: antialiased;
}

/* ---------- Reading progress ---------- */
.progress { position: fixed; top: 0; left: 0; height: 3px; width: 0;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  z-index: 100; transition: width .1s linear; }

/* ---------- Top bar ---------- */
.topbar {
  position: sticky; top: 0; z-index: 60; height: var(--topbar-h);
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  padding: 0 1.1rem;
  background: color-mix(in srgb, var(--bg) 85%, transparent);
  backdrop-filter: saturate(180%) blur(10px);
  border-bottom: 1px solid var(--border);
}
.brand { display: inline-flex; align-items: center; gap: .55rem; font-weight: 700;
  letter-spacing: -.01em; color: var(--text); text-decoration: none; }
.brand-mark { font-size: 1.15rem; }
.topbar-actions { display: flex; align-items: center; gap: .4rem; }
.topbar-link { color: var(--muted); text-decoration: none; font-size: .92rem;
  padding: .35rem .6rem; border-radius: 8px; }
.topbar-link:hover { color: var(--text); background: var(--surface-2); }
.theme-toggle, .menu-btn {
  cursor: pointer; border: 1px solid var(--border); background: var(--surface);
  color: var(--text); width: 38px; height: 38px; border-radius: 10px;
  font-size: 1rem; line-height: 1; display: grid; place-items: center;
  transition: transform .15s ease, background .15s ease;
}
.theme-toggle:hover, .menu-btn:hover { background: var(--surface-2); transform: translateY(-1px); }
.menu-btn { display: none; }

/* ---------- Shell layout ---------- */
.shell { display: grid; grid-template-columns: 268px minmax(0, 1fr) 232px;
  gap: 0; align-items: start; max-width: 1500px; margin: 0 auto; }
.shell--home { grid-template-columns: 268px minmax(0, 1fr); }

/* ---------- Sidebar ---------- */
.sidebar {
  position: sticky; top: var(--topbar-h); align-self: start;
  height: calc(100vh - var(--topbar-h)); overflow-y: auto;
  padding: 1rem .7rem 2rem; border-right: 1px solid var(--border);
  background: color-mix(in srgb, var(--surface) 40%, transparent);
}
.nav-filter { width: 100%; padding: .5rem .7rem; margin-bottom: .8rem;
  border: 1px solid var(--border); border-radius: 9px; background: var(--surface);
  color: var(--text); font-size: .85rem; }
.nav-filter:focus { outline: none; border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft); }
.nav-group { margin: 0 0 .15rem; }
.nav-group > summary { list-style: none; cursor: pointer; user-select: none;
  font-size: .71rem; text-transform: uppercase; letter-spacing: .07em;
  color: var(--muted); padding: .55rem .5rem .35rem; display: flex; align-items: center; gap: .45rem; }
.nav-group > summary::-webkit-details-marker { display: none; }
.nav-group > summary::before { content: "\\25B8"; font-size: .8em; transition: transform .15s ease; opacity: .7; }
.nav-group[open] > summary::before { transform: rotate(90deg); }
.nav-group > summary:hover { color: var(--text); }
.nav-link { display: block; color: var(--muted); text-decoration: none; font-size: .89rem;
  padding: .34rem .65rem; border-radius: 9px; border-left: 2px solid transparent;
  margin: 1px 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.nav-link:hover { background: var(--surface-2); color: var(--text); }
.nav-link.active { background: var(--accent-soft); color: var(--accent); font-weight: 600; border-left-color: var(--accent); }
.nav-link.hidden { display: none; }

/* ---------- Content ---------- */
.content {
  min-width: 0; max-width: 900px; margin: 1.5rem 1.4rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); box-shadow: var(--shadow);
  padding: 2.2rem clamp(1.1rem, 3.5vw, 3rem) 3rem; overflow-wrap: break-word;
}
.content.home { max-width: none; background: transparent; border: none; box-shadow: none;
  padding: 1rem clamp(1rem, 3vw, 2rem) 3rem; }

/* ---------- Breadcrumbs ---------- */
.breadcrumbs { font-size: .8rem; color: var(--muted); margin: 0 0 1.4rem;
  display: flex; flex-wrap: wrap; gap: .35rem; align-items: center; }
.breadcrumbs a { color: var(--muted); text-decoration: none; }
.breadcrumbs a:hover { color: var(--accent); }
.breadcrumbs .sep { opacity: .45; }
.breadcrumbs .crumb-current { color: var(--text); font-weight: 600; }

/* ---------- Right TOC ---------- */
.toc { position: sticky; top: calc(var(--topbar-h) + 12px); align-self: start;
  max-height: calc(100vh - var(--topbar-h) - 24px); overflow-y: auto;
  margin: 1.5rem 1rem 1.5rem 0; padding: .4rem .2rem .4rem 1rem;
  border-left: 1px solid var(--border); font-size: .84rem; }
.toc:empty { display: none; }
.toc h4 { margin: .2rem 0 .6rem; font-size: .68rem; text-transform: uppercase;
  letter-spacing: .09em; color: var(--muted); }
.toc a { display: block; color: var(--muted); text-decoration: none; padding: .18rem 0;
  border-left: 2px solid transparent; margin-left: -1rem; padding-left: 1rem;
  transition: color .12s ease, border-color .12s ease;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.toc a:hover { color: var(--text); }
.toc a.h3 { padding-left: 1.9rem; font-size: .8rem; }
.toc a.active { color: var(--accent); border-left-color: var(--accent); font-weight: 600; }

/* ---------- Pager ---------- */
.pager { display: flex; justify-content: space-between; gap: 1rem;
  margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--border); }
.pager > * { flex: 1 1 0; min-width: 0; }
.pager a { display: block; text-decoration: none; border: 1px solid var(--border);
  border-radius: 11px; padding: .75rem 1rem; color: var(--text); background: var(--surface);
  transition: border-color .15s ease, transform .15s ease; }
.pager a:hover { border-color: var(--accent); transform: translateY(-1px); }
.pager .pager-next { text-align: right; }
.pager .pager-label { display: block; font-size: .7rem; text-transform: uppercase;
  letter-spacing: .06em; color: var(--muted); margin-bottom: .15rem; }
.pager .pager-title { color: var(--accent); font-weight: 600;
  display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ---------- Scrim (mobile drawer) ---------- */
.scrim { position: fixed; inset: 0; background: rgba(0,0,0,.45); opacity: 0;
  pointer-events: none; transition: opacity .2s ease; z-index: 40; }
body.nav-open .scrim { opacity: 1; pointer-events: auto; }

@media (max-width: 1180px) {
  .shell { grid-template-columns: 268px minmax(0, 1fr); }
  .toc { display: none; }
}
@media (max-width: 900px) {
  .shell, .shell--home { grid-template-columns: 1fr; }
  .menu-btn { display: grid; }
  .sidebar { position: fixed; top: var(--topbar-h); left: 0; z-index: 50;
    width: 280px; height: calc(100vh - var(--topbar-h)); background: var(--surface);
    transform: translateX(-100%); transition: transform .22s ease; }
  body.nav-open .sidebar { transform: translateX(0); box-shadow: var(--shadow); }
  .content { margin: 1.1rem .8rem; }
}

/* ---------- Typography ---------- */
.content h1, .content h2, .content h3, .content h4 {
  line-height: 1.25; letter-spacing: -.015em; scroll-margin-top: 72px; position: relative; }
.content h1 { font-size: 2.05rem; margin: .2rem 0 1.2rem; padding-bottom: .5rem; border-bottom: 1px solid var(--border); }
.content h2 { font-size: 1.5rem; margin: 2.4rem 0 1rem; padding-top: .4rem; }
.content h3 { font-size: 1.2rem; margin: 1.8rem 0 .7rem; }
.content h4 { font-size: 1.02rem; margin: 1.4rem 0 .6rem; color: var(--muted); }
.content h2::before { content: ""; position: absolute; left: -1rem; top: .95rem;
  width: 5px; height: 1.05rem; border-radius: 3px; background: var(--accent); opacity: 0; transition: opacity .15s; }
.content h2:hover::before { opacity: 1; }
.anchor { position: absolute; left: -1.3rem; opacity: 0; text-decoration: none; color: var(--muted); font-weight: 400; }
.content h1:hover .anchor, .content h2:hover .anchor,
.content h3:hover .anchor, .content h4:hover .anchor { opacity: .7; }
.content p { margin: .9rem 0; }
.content a { color: var(--accent); text-decoration: none; border-bottom: 1px solid transparent; }
.content a:hover { border-bottom-color: var(--accent); }
.content hr { border: none; border-top: 1px solid var(--border); margin: 2.2rem 0; }
.content ul, .content ol { padding-left: 1.4rem; }
.content li { margin: .3rem 0; }
.content li::marker { color: var(--accent); }
strong { font-weight: 700; }

/* ---------- Epistemic badges (auto-applied by JS) ---------- */
.badge-doc, .badge-inf { display: inline-block; font-size: .72em; font-weight: 700;
  letter-spacing: .02em; padding: .06em .5em; border-radius: 999px; vertical-align: baseline; white-space: nowrap; }
.badge-doc { color: var(--ok); background: var(--ok-soft); border: 1px solid color-mix(in srgb, var(--ok) 45%, transparent); }
.badge-inf { color: var(--warn); background: var(--warn-soft); border: 1px solid color-mix(in srgb, var(--warn) 45%, transparent); }

/* ---------- Code ---------- */
code, pre, .codewrap { font-family: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
.content :not(pre) > code { background: var(--accent-soft); color: var(--text);
  padding: .12em .4em; border-radius: 6px; font-size: .86em;
  border: 1px solid color-mix(in srgb, var(--accent) 22%, transparent); }
.codewrap { position: relative; margin: 1.3rem 0; border-radius: 11px; overflow: hidden;
  box-shadow: var(--shadow); border: 1px solid rgba(0,0,0,.35); }
.codewrap .lang-badge { position: absolute; top: 0; left: 0; font-size: .68rem;
  letter-spacing: .06em; text-transform: uppercase; color: #9fb0c7;
  background: rgba(255,255,255,.05); padding: .25rem .6rem; border-bottom-right-radius: 8px; user-select: none; }
.codewrap .copy-btn { position: absolute; top: .4rem; right: .4rem; font-size: .72rem;
  color: #cbd5e1; cursor: pointer; background: rgba(255,255,255,.08);
  border: 1px solid rgba(255,255,255,.14); padding: .28rem .55rem; border-radius: 7px;
  transition: background .15s, color .15s; }
.codewrap .copy-btn:hover { background: rgba(255,255,255,.18); color: #fff; }
.codewrap .copy-btn.copied { color: #86efac; border-color: #86efac55; }
pre { margin: 0; background: var(--code-bg); color: var(--code-text);
  padding: 1.5rem 1.1rem 1.1rem; overflow-x: auto; font-size: .85rem; line-height: 1.6; }
pre code { background: none; padding: 0; border: none; color: inherit; font-size: inherit; }

/* ---------- Tables ---------- */
.content table { border-collapse: collapse; display: block; width: max-content;
  max-width: 100%; overflow-x: auto; margin: 1.3rem 0; font-size: .92rem;
  border: 1px solid var(--border); border-radius: 11px; }
.content th, .content td { border-bottom: 1px solid var(--border);
  border-right: 1px solid var(--border); padding: .55rem .85rem; text-align: left; }
.content tr td:last-child, .content tr th:last-child { border-right: none; }
.content thead th { background: var(--surface-2); font-weight: 700; position: sticky; top: 0; }
.content tbody tr:nth-child(even) { background: color-mix(in srgb, var(--surface-2) 55%, transparent); }
.content tbody tr:hover { background: var(--accent-soft); }
.content tbody tr:last-child td { border-bottom: none; }

/* ---------- Blockquote callouts ---------- */
.content blockquote { margin: 1.3rem 0; padding: .9rem 1.1rem; color: var(--text);
  background: var(--accent-soft); border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
  border-left: 4px solid var(--accent); border-radius: 11px; }
.content blockquote p { margin: .4rem 0; }
.content blockquote strong:first-child { color: var(--accent); }
.content img { max-width: 100%; border-radius: 8px; }

/* ---------- Home / index ---------- */
.hero { padding: 1.6rem 0 1.2rem; }
.hero-badge { display: inline-block; font-size: .72rem; text-transform: uppercase;
  letter-spacing: .08em; color: var(--accent); background: var(--accent-soft);
  border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
  padding: .3rem .7rem; border-radius: 999px; margin-bottom: 1rem; }
.hero h1 { font-size: 2.4rem; margin: 0 0 .5rem; letter-spacing: -.02em; }
.hero-sub { color: var(--muted); font-size: 1.05rem; max-width: 62ch; margin: 0 0 1.3rem; }
.doc-filter { width: 100%; max-width: 460px; padding: .7rem .9rem; border: 1px solid var(--border);
  border-radius: 11px; background: var(--surface); color: var(--text); font-size: .95rem; }
.doc-filter:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.section-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.1rem; margin-top: 1.4rem; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  box-shadow: var(--shadow); padding: 1.2rem 1.3rem; transition: transform .15s ease, border-color .15s ease; }
.card:hover { transform: translateY(-2px); border-color: var(--accent); }
.card h3 { margin: 0 0 .3rem; font-size: 1.05rem; letter-spacing: -.01em; display: flex; align-items: center; gap: .5rem; }
.card .card-badge { font-size: .68rem; text-transform: uppercase; letter-spacing: .06em;
  color: var(--accent); background: var(--accent-soft); padding: .12rem .5rem; border-radius: 999px; }
.card ul { list-style: none; padding: 0; margin: .6rem 0 0; }
.card li { margin: .12rem 0; }
.card a { color: var(--text); text-decoration: none; display: flex; justify-content: space-between;
  gap: .6rem; padding: .3rem .5rem; border-radius: 8px; font-size: .92rem; }
.card a:hover { background: var(--accent-soft); color: var(--accent); }
.card a .fname { color: var(--muted); font-size: .8em; font-family: ui-monospace, Menlo, Consolas, monospace; }
.card.hidden, .card li.hidden { display: none; }

.site-footer { text-align: center; color: var(--muted); font-size: .82rem; padding: 2rem 1rem 3rem; }
::selection { background: var(--accent-soft); }
"""

JS = """
(function () {
  var root = document.documentElement;

  // --- Theme toggle (initial theme already set by the boot script) ---
  function syncToggle() {
    var btn = document.getElementById('theme-toggle');
    if (btn) btn.innerHTML = (root.getAttribute('data-theme') === 'dark') ? '\\u2600' : '\\u263D';
  }
  syncToggle();
  var toggle = document.getElementById('theme-toggle');
  if (toggle) toggle.addEventListener('click', function () {
    var next = (root.getAttribute('data-theme') === 'dark') ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('cm-theme', next); } catch (e) {}
    syncToggle();
  });

  // --- Reading progress bar ---
  var progress = document.getElementById('progress');
  if (progress) {
    var upd = function () {
      var max = root.scrollHeight - root.clientHeight;
      progress.style.width = (max > 0 ? (root.scrollTop / max) * 100 : 0) + '%';
    };
    window.addEventListener('scroll', upd, { passive: true });
    window.addEventListener('resize', upd);
    upd();
  }

  var content = document.getElementById('content');

  // --- Anchor links on headings ---
  if (content) {
    content.querySelectorAll('h1[id], h2[id], h3[id], h4[id]').forEach(function (h) {
      var a = document.createElement('a');
      a.className = 'anchor'; a.href = '#' + h.id; a.textContent = '#';
      a.setAttribute('aria-hidden', 'true');
      h.insertBefore(a, h.firstChild);
    });
  }

  // --- Auto-badge [Documented] / [Inferred] epistemic tags ---
  if (content) {
    var rx = /\\[(Documented|Inferred)\\]/g;
    var skip = /^(CODE|PRE|SCRIPT|STYLE|A)$/;
    var walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT, null);
    var targets = [];
    while (walker.nextNode()) {
      var node = walker.currentNode;
      if (node.parentNode && skip.test(node.parentNode.nodeName)) continue;
      rx.lastIndex = 0;
      if (rx.test(node.nodeValue)) targets.push(node);
    }
    targets.forEach(function (node) {
      var s = node.nodeValue, frag = document.createDocumentFragment(), last = 0, m;
      rx.lastIndex = 0;
      while ((m = rx.exec(s))) {
        if (m.index > last) frag.appendChild(document.createTextNode(s.slice(last, m.index)));
        var span = document.createElement('span');
        span.className = (m[1] === 'Documented') ? 'badge-doc' : 'badge-inf';
        span.textContent = m[1];
        frag.appendChild(span);
        last = m.index + m[0].length;
      }
      if (last < s.length) frag.appendChild(document.createTextNode(s.slice(last)));
      node.parentNode.replaceChild(frag, node);
    });
  }

  // --- Build on-page TOC from h2/h3 ---
  var toc = document.getElementById('toc');
  if (toc && content) {
    var heads = content.querySelectorAll('h2[id], h3[id]');
    if (heads.length > 2) {
      var html = '<h4>On this page</h4>';
      heads.forEach(function (h) {
        var lvl = h.tagName.toLowerCase();
        var text = h.textContent.replace(/^#/, '').trim();
        html += '<a class="' + lvl + '" href="#' + h.id + '">' + escapeHtml(text) + '</a>';
      });
      toc.innerHTML = html;
      var links = {};
      toc.querySelectorAll('a').forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
      var spy = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            Object.keys(links).forEach(function (k) { links[k].classList.remove('active'); });
            if (links[en.target.id]) links[en.target.id].classList.add('active');
          }
        });
      }, { rootMargin: '-80px 0px -70% 0px' });
      heads.forEach(function (h) { spy.observe(h); });
    }
  }

  // --- Code blocks: language badge + copy button ---
  if (content) {
    content.querySelectorAll('pre').forEach(function (pre) {
      var wrap = document.createElement('div');
      wrap.className = 'codewrap';
      pre.parentNode.insertBefore(wrap, pre);
      wrap.appendChild(pre);
      var code = pre.querySelector('code'), lang = '';
      if (code) (code.className || '').split(/\\s+/).forEach(function (c) {
        if (c.indexOf('language-') === 0) lang = c.slice(9);
      });
      if (lang) {
        var badge = document.createElement('span');
        badge.className = 'lang-badge'; badge.textContent = lang;
        wrap.appendChild(badge);
      }
      var btn = document.createElement('button');
      btn.className = 'copy-btn'; btn.type = 'button'; btn.textContent = 'Copy';
      btn.addEventListener('click', function () {
        navigator.clipboard.writeText((code || pre).innerText).then(function () {
          btn.textContent = 'Copied'; btn.classList.add('copied');
          setTimeout(function () { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 1400);
        });
      });
      wrap.appendChild(btn);
    });
  }

  // --- Sidebar filter ---
  var navFilter = document.getElementById('nav-filter');
  if (navFilter) {
    navFilter.addEventListener('input', function () {
      var q = navFilter.value.toLowerCase();
      document.querySelectorAll('.nav-group').forEach(function (g) {
        var any = false;
        g.querySelectorAll('.nav-link').forEach(function (a) {
          var match = a.textContent.toLowerCase().indexOf(q) !== -1;
          a.classList.toggle('hidden', !match);
          if (match) any = true;
        });
        g.style.display = any ? '' : 'none';
        if (q && any) g.open = true;
      });
    });
  }

  // --- Home page card filter ---
  var filter = document.getElementById('doc-filter');
  if (filter) {
    filter.addEventListener('input', function () {
      var q = filter.value.toLowerCase();
      document.querySelectorAll('.card').forEach(function (card) {
        var anyVisible = false;
        card.querySelectorAll('li').forEach(function (li) {
          var match = li.textContent.toLowerCase().indexOf(q) !== -1;
          li.classList.toggle('hidden', !match);
          if (match) anyVisible = true;
        });
        card.classList.toggle('hidden', !anyVisible);
      });
    });
  }

  // --- Mobile drawer ---
  var menuBtn = document.getElementById('menu-btn');
  var scrim = document.getElementById('scrim');
  function closeNav() { document.body.classList.remove('nav-open'); }
  if (menuBtn) menuBtn.addEventListener('click', function () { document.body.classList.toggle('nav-open'); });
  if (scrim) scrim.addEventListener('click', closeNav);
  document.querySelectorAll('.nav-link').forEach(function (a) { a.addEventListener('click', closeNav); });

  // --- Keyboard: "/" focuses the filter ---
  document.addEventListener('keydown', function (e) {
    if (e.key !== '/') return;
    var tag = document.activeElement && document.activeElement.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;
    var f = document.getElementById('nav-filter') || document.getElementById('doc-filter');
    if (f) { e.preventDefault(); f.focus(); }
  });

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
})();
"""


def find_markdown_files():
    for path in sorted(ROOT.rglob("*.md")):
        rel_parts = path.relative_to(ROOT).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        yield path


def render_markdown(md, text):
    def link_open(self, tokens, idx, options, env):
        token = tokens[idx]
        href = token.attrGet("href")
        if href and not href.startswith(("http://", "https://", "#")):
            base, _, anchor = href.partition("#")
            if base.endswith(".md"):
                new_href = base[:-3] + ".html"
                if anchor:
                    new_href += "#" + anchor
                token.attrSet("href", new_href)
        return self.renderToken(tokens, idx, options, env)

    md.add_render_rule("link_open", link_open)
    return md.render(text)


def slugify(text):
    """GitHub-compatible heading slug so in-page `#anchor` links resolve."""
    slug = text.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)   # drop punctuation (keeps unicode word chars)
    slug = re.sub(r"\s", "-", slug)         # spaces -> hyphens (repeats preserved)
    return slug


def add_heading_ids(rendered):
    """Inject unique, GitHub-style id attributes into <h1>..<h6> tags."""
    seen = {}

    def repl(match):
        level, attrs, inner = match.group(1), match.group(2), match.group(3)
        text = re.sub(r"<[^>]+>", "", inner)          # strip inline tags
        text = html.unescape(text)
        base = slugify(text)
        if not base:
            base = "section"
        slug = base
        if slug in seen:
            seen[slug] += 1
            slug = f"{base}-{seen[base]}"
        else:
            seen[slug] = 0
        if "id=" in attrs:
            return match.group(0)
        return f"<h{level}{attrs} id=\"{slug}\">{inner}</h{level}>"

    return re.sub(r"<h([1-6])([^>]*)>(.*?)</h\1>", repl, rendered, flags=re.DOTALL)


def extract_title(text, fallback):
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return re.sub(r"[`*_]", "", line[2:].strip())
    return fallback


def prettify(name):
    name = re.sub(r"^\d+[_-]", "", name)
    return name.replace("_", " ").replace("-", " ").strip().title()


def token_label(tok):
    return TOKEN_LABELS.get(tok.lower(), prettify(tok))


def group_label(key):
    if key == "":
        return "Overview"
    return " / ".join(token_label(t) for t in key.split("/"))


def _group_of(out_rel):
    parent = out_rel.parent.as_posix()
    return "" if parent == "." else parent


def _group_sort_key(key):
    # Overview (root) first, then alphabetical by path.
    return (0, "") if key == "" else (1, key)


def ordered_pages(pages):
    """Return [(group_key, out_rel, title)] in display + pager order."""
    groups = {}
    for out_rel, title in pages:
        groups.setdefault(_group_of(out_rel), []).append((out_rel, title))
    ordered = []
    for key in sorted(groups, key=_group_sort_key):
        for out_rel, title in sorted(groups[key], key=lambda p: p[0].parts):
            ordered.append((key, out_rel, title))
    return ordered


def build_sidebar(ordered, current_out_rel):
    prefix = "../" * (len(current_out_rel.parts) - 1) if current_out_rel else ""
    parts = []
    for key, group in groupby(ordered, key=lambda t: t[0]):
        group = list(group)
        active_group = current_out_rel is not None and any(o == current_out_rel for _, o, _ in group)
        links = []
        for _, out_rel, title in group:
            href = prefix + out_rel.as_posix()
            cls = "nav-link active" if out_rel == current_out_rel else "nav-link"
            links.append(f'<a class="{cls}" href="{href}">{html.escape(title)}</a>')
        open_attr = " open" if (active_group or current_out_rel is None) else ""
        parts.append(
            f'<details class="nav-group"{open_attr}>'
            f'<summary>{html.escape(group_label(key))}</summary>'
            f'{"".join(links)}</details>'
        )
    return "".join(parts)


def build_breadcrumbs(out_rel, title, prefix):
    crumbs = [f'<a href="{prefix}index.html">Home</a>']
    for tok in out_rel.parts[:-1]:
        crumbs.append('<span class="sep">/</span>')
        crumbs.append(f'<span>{html.escape(token_label(tok))}</span>')
    crumbs.append('<span class="sep">/</span>')
    crumbs.append(f'<span class="crumb-current">{html.escape(title)}</span>')
    return "".join(crumbs)


def build_pager(ordered, current_out_rel, prefix):
    idx = next(i for i, (_, o, _) in enumerate(ordered) if o == current_out_rel)
    prev_page = ordered[idx - 1] if idx > 0 else None
    next_page = ordered[idx + 1] if idx < len(ordered) - 1 else None

    def link(page, side, label):
        _, out_rel, title = page
        href = prefix + out_rel.as_posix()
        return (
            f'<a class="pager-{side}" href="{href}">'
            f'<span class="pager-label">{label}</span>'
            f'<span class="pager-title">{html.escape(title)}</span></a>'
        )

    left = link(prev_page, "prev", "&larr; Previous") if prev_page else "<span></span>"
    right = link(next_page, "next", "Next &rarr;") if next_page else "<span></span>"
    return left + right


def build():
    md = MarkdownIt("gfm-like")
    rendered = []  # (out_rel, title, body)

    for src in find_markdown_files():
        rel = src.relative_to(ROOT)
        out_rel = rel.with_suffix(".html")
        text = src.read_text(encoding="utf-8")
        body = add_heading_ids(render_markdown(md, text))
        title = extract_title(text, rel.as_posix())
        rendered.append((out_rel, title, body))

    pages = [(o, t) for o, t, _ in rendered]
    ordered = ordered_pages(pages)

    for out_rel, title, body in rendered:
        out_path = OUTPUT_DIR / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        prefix = "../" * (len(out_rel.parts) - 1)
        out_path.write_text(
            PAGE_TEMPLATE.format(
                title=html.escape(title), site=SITE_NAME, css=CSS, js=JS, boot=BOOT,
                index_href=prefix + "index.html",
                sidebar=build_sidebar(ordered, out_rel),
                breadcrumbs=build_breadcrumbs(out_rel, title, prefix),
                body=body,
                pager=build_pager(ordered, out_rel, prefix),
            ),
            encoding="utf-8",
        )

    write_index(pages, ordered)


def write_index(pages, ordered):
    cards = []
    for key, group in groupby(ordered, key=lambda t: t[0]):
        group = list(group)
        items = []
        for _, out_rel, title in group:
            items.append(
                f'<li><a href="{out_rel.as_posix()}"><span>{html.escape(title)}</span>'
                f'<span class="fname">{html.escape(out_rel.name)}</span></a></li>'
            )
        cards.append(
            '<div class="card">'
            f'<h3>{html.escape(group_label(key))} <span class="card-badge">{len(group)}</span></h3>'
            f'<ul>{"".join(items)}</ul></div>'
        )

    body = '<div class="section-grid">' + "".join(cards) + "</div>"
    (OUTPUT_DIR / "index.html").write_text(
        INDEX_TEMPLATE.format(
            site=SITE_NAME, css=CSS, js=JS, boot=BOOT,
            sidebar=build_sidebar(ordered, None), body=body,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    build()
    print(f"Docs written to {OUTPUT_DIR.relative_to(ROOT)}/index.html")
