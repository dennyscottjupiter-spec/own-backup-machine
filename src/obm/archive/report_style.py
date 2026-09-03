# ---
# purpose: the document shell, CSS and JS of BACKUP-README.html -- kept out of the page builder
#          so the builder stays readable
# exports: CSS, JS, page()
# depends: nothing (plain strings)
# gotcha: the page is opened from inside an archive, offline -- no CDN, no fonts, no fetch, ever
# ---
from __future__ import annotations

CSS = """
:root {
  --ground: #141414; --plate: #1c1c1c; --rule: #2b2b2b; --rule-soft: #232323;
  --text: #e5e5e5; --muted: #9ca3af; --accent: #3b82f6;
  --mono: Consolas, "Cascadia Mono", "DejaVu Sans Mono", ui-monospace, monospace;
  --sans: "Segoe UI", system-ui, -apple-system, sans-serif;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--ground); color: var(--text);
  font: 15px/1.55 var(--sans); -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 1080px; margin: 0 auto; padding: 40px 24px 96px; }
h2 {
  font-size: 13px; font-weight: 600; letter-spacing: .02em; color: var(--muted);
  margin: 44px 0 14px; padding-bottom: 8px; border-bottom: 1px solid var(--rule);
}
.num { font-variant-numeric: tabular-nums; }

/* ---- header ledger ---- */
.name {
  font-family: var(--mono); font-size: clamp(20px, 3.4vw, 30px); font-weight: 600;
  letter-spacing: -.01em; word-break: break-all; margin: 0 0 4px;
}
.what { color: var(--muted); max-width: 66ch; margin: 0 0 26px; }
.ledger {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  background: var(--plate); border: 1px solid var(--rule); border-radius: 3px;
}
.ledger div { padding: 14px 16px; border-right: 1px solid var(--rule-soft); }
.ledger div:last-child { border-right: 0; }
.ledger dt { color: var(--muted); font-size: 12px; margin: 0 0 3px; }
.ledger dd { margin: 0; font-family: var(--mono); font-size: 15px; font-variant-numeric: tabular-nums; }

/* ---- kind breakdown ---- */
.share { display: flex; height: 10px; border-radius: 2px; overflow: hidden; margin-bottom: 18px; }
.share span { min-width: 2px; }
.kinds { width: 100%; border-collapse: collapse; }
.kinds td { padding: 7px 0; border-bottom: 1px solid var(--rule-soft); }
.kinds td + td { text-align: right; font-family: var(--mono); font-variant-numeric: tabular-nums; }
.swatch {
  display: inline-block; width: 9px; height: 9px; border-radius: 2px; margin-right: 10px;
  vertical-align: baseline;
}

/* ---- search ---- */
.find { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; margin-bottom: 12px; }
input[type=search] {
  flex: 1 1 260px; min-width: 0; background: var(--plate); color: var(--text);
  border: 1px solid var(--rule); border-radius: 3px; padding: 9px 12px;
  font: 14px var(--mono);
}
input[type=search]:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.hits { color: var(--muted); font-size: 13px; }

/* ---- tree ---- */
.tree { font-family: var(--mono); font-size: 13.5px; }
.node > summary, .row {
  position: relative; display: grid; grid-template-columns: 1fr max-content max-content;
  gap: 18px; align-items: baseline; padding: 4px 10px 4px 22px; border-radius: 2px;
}
.node > summary { cursor: pointer; list-style: none; }
.node > summary::-webkit-details-marker { display: none; }
.node > summary::before {
  content: ""; position: absolute; left: 8px; top: .62em;
  border: 4px solid transparent; border-left-color: var(--muted);
  transition: transform .12s ease; transform-origin: 2px 50%;
}
.node[open] > summary::before { transform: rotate(90deg); }
.node > summary:hover, .row:hover { background: #ffffff0d; }
.node > summary:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.fill {
  position: absolute; left: 0; top: 0; bottom: 0; width: calc(var(--w) * 1%);
  background: var(--tone, var(--accent)); opacity: .16; border-radius: 2px; pointer-events: none;
}
.label { position: relative; overflow-wrap: anywhere; }
.n, .sz { position: relative; color: var(--muted); font-variant-numeric: tabular-nums; }
.sz { color: var(--text); min-width: 8ch; text-align: right; }
.kids { border-left: 1px solid var(--rule-soft); margin-left: 12px; }
.files .row { grid-template-columns: max-content 1fr max-content; padding-left: 10px; gap: 12px; }
.dot { width: 7px; height: 7px; border-radius: 50%; align-self: center; }
.cut { color: var(--muted); font-size: 13px; margin-top: 14px; }
.empty { color: var(--muted); }
[hidden] { display: none !important; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""

JS = """
(function () {
  var box = document.getElementById('q');
  var hits = document.getElementById('hits');
  if (!box) return;
  // data-p carries the lowercased path and sits on the <details>/<div> that owns a whole subtree,
  // so hiding one element hides everything under it. Document order puts parents before children.
  var rows = Array.prototype.slice.call(document.querySelectorAll('[data-p]'));
  var opened = [];

  function reset() {
    for (var i = 0; i < rows.length; i++) rows[i].hidden = false;
    for (var j = 0; j < opened.length; j++) opened[j].open = opened[j].dataset.wasOpen === '1';
    opened = [];
    hits.textContent = '';
  }

  function reveal(el) {
    for (var p = el.parentElement; p && !p.classList.contains('wrap'); p = p.parentElement) {
      p.hidden = false;
      if (p.tagName === 'DETAILS' && !p.open) {
        p.dataset.wasOpen = '0';
        opened.push(p);
        p.open = true;
      }
    }
  }

  function run(q) {
    if (!q) { reset(); return; }
    var shown = 0;
    for (var i = 0; i < rows.length; i++) {
      var hit = rows[i].dataset.p.indexOf(q) !== -1;
      rows[i].hidden = !hit;
      if (hit) { shown++; reveal(rows[i]); }
    }
    hits.textContent = shown ? shown + (shown === 1 ? ' match' : ' matches') : 'no matches';
  }

  var timer;
  box.addEventListener('input', function () {
    clearTimeout(timer);
    var q = box.value.trim().toLowerCase();
    timer = setTimeout(function () { run(q); }, 90);
  });
})();
"""


def page(
    title: str,
    ledger: str,
    kinds: str,
    tree: str,
    files: str,
    manifest_name: str,
) -> str:
    kinds_section = f"<h2>What kind of files</h2>{kinds}" if kinds else ""
    files_section = f"<h2>Every file in this archive</h2>{files}" if files else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{CSS}</style></head>
<body><main class="wrap">
<h1 class="name">{title}</h1>
<p class="what">Only the files that changed since the last run, with their folders kept intact.
Extract the whole archive to put a path back where it came from, or pull one file out of it.</p>
<dl class="ledger">{ledger}</dl>

{kinds_section}

<h2>Find a file or folder</h2>
<div class="find">
  <input type="search" id="q" placeholder="Type part of a name or path" autocomplete="off" spellcheck="false">
  <span class="hits" id="hits" role="status"></span>
</div>

<h2>Where the files came from</h2>
{tree}

{files_section}

<h2>Also written</h2>
<p class="cut">{manifest_name} sits next to the archive: the same listing as JSON, plus every scan
issue. BACKUP-README.txt in this archive is the same index as plain text.</p>
</main>
<script>{JS}</script>
</body></html>
"""
