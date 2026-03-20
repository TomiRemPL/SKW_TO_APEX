# apex_export_to_md/renderers/html_renderer.py
"""Renderer interaktywnego HTML — self-contained plik z vis.js.

Zawiera 3 zakładki:
1. Diagram relacji (vis.js network graph)
2. Przeglądarka bazy danych (drzewo + panel szczegółów)
3. Mapa APEX ↔ DB (połączenia stron ze tabelami)

Branding: logo TR (inline SVG), autor, stopka.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models.apex_models import ApexApp
from apex_export_to_md.models.db_models import DbSchema
from apex_export_to_md.linker.apex_db_linker import ApexDbLink

logger = logging.getLogger(__name__)


class HtmlRenderer:
    """Generuje self-contained interaktywny HTML."""

    def __init__(self, config: AppConfig):
        self._config = config

    def render(self, app: ApexApp, schema: DbSchema,
               links: list[ApexDbLink]) -> str:
        """Generuj pełny plik HTML."""
        data = self._prepare_data(app, schema, links)
        return self._build_html(app.name, data)

    def _prepare_data(self, app: ApexApp, schema: DbSchema,
                      links: list[ApexDbLink]) -> dict:
        """Przygotuj dane JSON do osadzenia w HTML."""
        # Tabele
        tables = []
        for t in schema.tables:
            tables.append({
                "name": t.name,
                "comment": t.comment or "",
                "columns": [
                    {
                        "name": c.name,
                        "type": c.data_type,
                        "nullable": c.nullable,
                        "default": c.default or "",
                        "identity": c.identity,
                        "comment": c.comment or "",
                    }
                    for c in t.columns
                ],
                "constraints": [
                    {
                        "name": c.name,
                        "type": c.constraint_type,
                        "columns": c.columns,
                        "ref_table": c.ref_table or "",
                        "ref_columns": c.ref_columns,
                        "check_expr": c.check_expression or "",
                    }
                    for c in t.constraints
                ],
                "indexes": [
                    {
                        "name": i.name,
                        "columns": i.columns,
                        "unique": i.unique,
                    }
                    for i in t.indexes
                ],
            })

        # Widoki
        views = [{"name": v.name, "comment": v.comment or "",
                  "columns": v.columns, "sql": v.sql}
                 for v in schema.views]

        # Pakiety
        packages = []
        for p in schema.packages:
            packages.append({
                "name": p.name,
                "spec": [
                    {"name": s.name, "type": s.subprogram_type,
                     "params": ", ".join(f"{pr.name} {pr.direction} {pr.data_type}"
                                         for pr in s.parameters),
                     "return": s.return_type or "",
                     "desc": s.description or ""}
                    for s in p.spec_subprograms
                ],
                "body": [
                    {"name": s.name, "type": s.subprogram_type,
                     "visibility": s.visibility,
                     "desc": s.description or ""}
                    for s in p.body_subprograms
                ],
                "body_source": p.body_source,
            })

        # Sekwencje
        sequences = [{"name": s.name, "start": s.start_with or "",
                       "incr": s.increment_by or ""}
                     for s in schema.sequences]

        # FK edges dla diagramu
        edges = []
        for t in schema.tables:
            for c in t.constraints:
                if c.constraint_type == "FK" and c.ref_table:
                    edges.append({
                        "from": t.name,
                        "to": c.ref_table,
                        "label": c.name,
                    })

        # Strony APEX
        pages = [{"id": p.id, "name": p.name} for p in app.pages]

        # Linki APEX↔DB
        link_data = [
            {"page_id": l.page_id, "page_name": l.page_name,
             "objects": l.db_objects, "source_type": l.source_type,
             "source_name": l.source_name}
            for l in links
        ]

        return {
            "tables": tables,
            "views": views,
            "packages": packages,
            "sequences": sequences,
            "edges": edges,
            "pages": pages,
            "links": link_data,
        }

    def _build_html(self, app_name: str, data: dict) -> str:
        """Zbuduj pełny HTML z danymi, stylami i JS."""
        data_json = json.dumps(data, ensure_ascii=False, indent=2)
        author = self._config.author_name

        return f'''<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{app_name} — Dokumentacja projektu</title>
<style>
{self._css()}
</style>
</head>
<body>

<header>
  <div class="header-left">
    {self._logo_svg()}
    <h1>{app_name} — Dokumentacja projektu</h1>
  </div>
  <div class="search-box">
    <input type="text" id="search" placeholder="Szukaj..." oninput="handleSearch(this.value)">
  </div>
</header>

<nav class="tabs">
  <button class="tab active" onclick="switchTab('diagram')">Diagram relacji</button>
  <button class="tab" onclick="switchTab('browser')">Baza danych</button>
  <button class="tab" onclick="switchTab('map')">APEX ↔ DB</button>
</nav>

<main>
  <div id="tab-diagram" class="tab-content active">
    <div id="er-network" style="width:100%;height:600px;border:1px solid #ddd;"></div>
    <div id="node-detail" class="detail-panel"></div>
  </div>

  <div id="tab-browser" class="tab-content" style="display:none">
    <div class="browser-layout">
      <div id="object-tree" class="tree-panel"></div>
      <div id="object-detail" class="detail-panel"></div>
    </div>
  </div>

  <div id="tab-map" class="tab-content" style="display:none">
    <div class="map-layout">
      <div id="apex-pages" class="map-column">
        <h3>Strony APEX</h3>
        <div id="page-list"></div>
      </div>
      <div id="map-connections" class="map-connections"></div>
      <div id="db-objects" class="map-column">
        <h3>Obiekty bazy danych</h3>
        <div id="db-list"></div>
      </div>
    </div>
  </div>
</main>

<footer>
  <span>Wygenerowano narzędziem <strong>apex_export_to_md</strong></span>
  <span>Autor: <strong>{author}</strong></span>
  <span>Współpraca: <strong>Claude</strong> (Anthropic)</span>
</footer>

<script>
// === DATA ===
const DATA = {data_json};
</script>

<script>
{self._vis_js_inline()}
</script>

<script>
{self._javascript()}
</script>

</body>
</html>'''

    def _vis_js_inline(self) -> str:
        """Zwróć vis-network.min.js jako inline string.

        Plik jest ładowany z bundled resource przy imporcie modułu.
        Jeśli niedostępny, zwraca minimalny stub z komunikatem.
        """
        vis_path = Path(__file__).parent / "vendor" / "vis-network.min.js"
        if vis_path.exists():
            return vis_path.read_text(encoding="utf-8")
        # Fallback: CDN + ostrzeżenie w konsoli
        logger.warning("vis-network.min.js nie znaleziony w vendor/ — HTML nie będzie działał offline")
        return (
            '/* vis-network not bundled — fallback */\n'
            'document.addEventListener("DOMContentLoaded", function() {\n'
            '  var s = document.createElement("script");\n'
            '  s.src = "https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js";\n'
            '  s.onload = function() { if(typeof initErTab === "function") initErTab(); };\n'
            '  document.head.appendChild(s);\n'
            '});\n'
        )

    def _logo_svg(self) -> str:
        """Inline SVG logo — inicjały TR w geometrycznym okręgu."""
        return '''<svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
  <circle cx="20" cy="20" r="19" fill="#1a365d" stroke="#d4a843" stroke-width="2"/>
  <text x="20" y="26" text-anchor="middle" font-family="Arial,sans-serif"
        font-size="16" font-weight="bold" fill="#d4a843">TR</text>
</svg>'''

    def _css(self) -> str:
        """Style CSS."""
        return '''
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
       color: #333; background: #f5f5f5; }
header { display: flex; justify-content: space-between; align-items: center;
         padding: 12px 24px; background: #1a365d; color: white; }
.header-left { display: flex; align-items: center; gap: 12px; }
header h1 { font-size: 18px; font-weight: 500; }
.search-box input { padding: 6px 12px; border: none; border-radius: 4px; width: 220px; }
.tabs { display: flex; gap: 0; background: #fff; border-bottom: 2px solid #ddd;
        padding: 0 24px; }
.tab { padding: 10px 20px; border: none; background: none; cursor: pointer;
       font-size: 14px; color: #666; border-bottom: 2px solid transparent; }
.tab.active { color: #1a365d; border-bottom-color: #d4a843; font-weight: 600; }
.tab:hover { color: #1a365d; }
main { padding: 16px 24px; min-height: 70vh; }
.tab-content { display: none; }
.tab-content.active { display: block; }
.detail-panel { background: #fff; border: 1px solid #ddd; border-radius: 4px;
                padding: 16px; margin-top: 12px; max-height: 400px; overflow-y: auto; }
.browser-layout { display: flex; gap: 16px; }
.tree-panel { width: 280px; background: #fff; border: 1px solid #ddd;
              border-radius: 4px; padding: 12px; max-height: 70vh; overflow-y: auto; }
.tree-panel h4 { color: #1a365d; margin: 8px 0 4px; font-size: 13px; }
.tree-item { padding: 4px 8px; cursor: pointer; border-radius: 3px; font-size: 13px; }
.tree-item:hover { background: #e8edf3; }
.tree-item.active { background: #1a365d; color: white; }
.browser-layout .detail-panel { flex: 1; margin-top: 0; max-height: 70vh; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; }
th { background: #f0f0f0; font-weight: 600; }
.map-layout { display: flex; gap: 16px; align-items: flex-start; }
.map-column { flex: 1; background: #fff; border: 1px solid #ddd; border-radius: 4px;
              padding: 12px; max-height: 70vh; overflow-y: auto; }
.map-column h3 { font-size: 14px; color: #1a365d; margin-bottom: 8px; }
.map-item { padding: 6px 10px; cursor: pointer; border-radius: 3px;
            font-size: 13px; margin: 2px 0; }
.map-item:hover { background: #e8edf3; }
.map-item.highlight { background: #d4a843; color: #1a365d; font-weight: 600; }
.map-connections { width: 60px; }
footer { display: flex; justify-content: center; gap: 24px; padding: 16px;
         background: #1a365d; color: #aaa; font-size: 12px; }
footer strong { color: #d4a843; }
pre { background: #f8f8f8; border: 1px solid #ddd; padding: 12px; overflow-x: auto;
      font-size: 12px; border-radius: 4px; }
code { font-family: "Fira Code", Consolas, monospace; }
.search-results { background: #ffe; padding: 8px; border: 1px solid #dda; margin: 8px 0;
                  border-radius: 4px; display: none; }
'''

    def _javascript(self) -> str:
        """Logika JS — zakładki, diagram, przeglądarka, mapa."""
        return '''
// === TABS ===
function switchTab(name) {
  document.querySelectorAll(".tab-content").forEach(t => {
    t.style.display = "none";
    t.classList.remove("active");
  });
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  const panel = document.getElementById("tab-" + name);
  if (panel) { panel.style.display = "block"; panel.classList.add("active"); }
  event.target.classList.add("active");
  if (name === "diagram" && !window._diagramInit) initDiagram();
  if (name === "browser" && !window._browserInit) initBrowser();
  if (name === "map" && !window._mapInit) initMap();
}

// === DIAGRAM (vis.js) ===
function initDiagram() {
  window._diagramInit = true;
  const nodes = DATA.tables.map(t => ({
    id: t.name, label: t.name, shape: "box",
    color: getNodeColor(t.name),
    title: t.comment + " (" + t.columns.length + " kolumn)",
    font: { size: 12 }
  }));
  const edges = DATA.edges.map(e => ({
    from: e.from, to: e.to, label: e.label,
    arrows: "to", font: { size: 9, align: "middle" },
    color: { color: "#999" }
  }));
  const container = document.getElementById("er-network");
  const network = new vis.Network(container, { nodes, edges }, {
    layout: { hierarchical: { direction: "UD", sortMethod: "hubsize", nodeSpacing: 200 } },
    physics: false,
    interaction: { hover: true },
    edges: { smooth: { type: "cubicBezier" } }
  });
  network.on("click", params => {
    if (params.nodes.length) showNodeDetail(params.nodes[0]);
  });
}

function getNodeColor(name) {
  if (name.startsWith("B_SL_")) return { background: "#c6f6d5", border: "#38a169" };
  if (name.includes("_HIST") || name.includes("_TMP") || name.includes("IMPORT"))
    return { background: "#e2e8f0", border: "#718096" };
  return { background: "#bee3f8", border: "#3182ce" };
}

function showNodeDetail(name) {
  const t = DATA.tables.find(x => x.name === name);
  if (!t) return;
  let html = "<h3>" + t.name + "</h3>";
  if (t.comment) html += "<p><em>" + t.comment + "</em></p>";
  html += "<table><tr><th>Kolumna</th><th>Typ</th><th>NULL</th><th>Default</th><th>Komentarz</th></tr>";
  t.columns.forEach(c => {
    html += "<tr><td>" + c.name + "</td><td>" + c.type + "</td>"
         + "<td>" + (c.nullable ? "NULL" : "NOT NULL") + "</td>"
         + "<td>" + (c.default || "\u2014") + "</td>"
         + "<td>" + (c.comment || "\u2014") + "</td></tr>";
  });
  html += "</table>";
  if (t.constraints.length) {
    html += "<h4>Constraints</h4><ul>";
    t.constraints.forEach(c => {
      let desc = c.type + ": " + c.name;
      if (c.type === "FK") desc += " \u2192 " + c.ref_table + "(" + c.ref_columns.join(",") + ")";
      if (c.type === "CHK") desc += " " + c.check_expr;
      html += "<li>" + desc + "</li>";
    });
    html += "</ul>";
  }
  document.getElementById("node-detail").innerHTML = html;
}

// === BROWSER ===
function initBrowser() {
  window._browserInit = true;
  const tree = document.getElementById("object-tree");
  let html = "<h4>Tabele</h4>";
  DATA.tables.forEach(t => {
    html += "<div class=\\"tree-item\\" onclick=\\"showObject('table','" + t.name + "')\\">" + t.name + "</div>";
  });
  html += "<h4>Widoki</h4>";
  DATA.views.forEach(v => {
    html += "<div class=\\"tree-item\\" onclick=\\"showObject('view','" + v.name + "')\\">" + v.name + "</div>";
  });
  html += "<h4>Pakiety</h4>";
  DATA.packages.forEach(p => {
    html += "<div class=\\"tree-item\\" onclick=\\"showObject('package','" + p.name + "')\\">" + p.name + "</div>";
  });
  html += "<h4>Sekwencje</h4>";
  DATA.sequences.forEach(s => {
    html += "<div class=\\"tree-item\\" onclick=\\"showObject('sequence','" + s.name + "')\\">" + s.name + "</div>";
  });
  tree.innerHTML = html;
}

function showObject(type, name) {
  document.querySelectorAll(".tree-item").forEach(i => i.classList.remove("active"));
  event.target.classList.add("active");
  const detail = document.getElementById("object-detail");
  if (type === "table") {
    const t = DATA.tables.find(x => x.name === name);
    if (!t) return;
    let html = "<h3>Tabela: " + t.name + "</h3>";
    if (t.comment) html += "<p><em>" + t.comment + "</em></p>";
    html += "<table><tr><th>Kolumna</th><th>Typ</th><th>NULL</th><th>Default</th><th>Komentarz</th></tr>";
    t.columns.forEach(c => {
      html += "<tr><td>" + c.name + "</td><td>" + c.type +
        (c.identity ? " (IDENTITY)" : "") + "</td>" +
        "<td>" + (c.nullable ? "NULL" : "NOT NULL") + "</td>" +
        "<td>" + (c.default || "\u2014") + "</td>" +
        "<td>" + (c.comment || "\u2014") + "</td></tr>";
    });
    html += "</table>";
    if (t.constraints.length) {
      html += "<h4>Constraints</h4><ul>";
      t.constraints.forEach(c => {
        let d = "<strong>" + c.type + "</strong>: " + c.name + " (" + c.columns.join(", ") + ")";
        if (c.type === "FK") d += " \u2192 " + c.ref_table;
        if (c.type === "CHK") d += " \u2014 " + c.check_expr;
        html += "<li>" + d + "</li>";
      });
      html += "</ul>";
    }
    if (t.indexes.length) {
      html += "<h4>Indeksy</h4><ul>";
      t.indexes.forEach(i => {
        html += "<li>" + i.name + " (" + i.columns.join(", ") + ")" + (i.unique ? " UNIQUE" : "") + "</li>";
      });
      html += "</ul>";
    }
    detail.innerHTML = html;
  } else if (type === "view") {
    const v = DATA.views.find(x => x.name === name);
    if (!v) return;
    let html = "<h3>Widok: " + v.name + "</h3>";
    if (v.comment) html += "<p><em>" + v.comment + "</em></p>";
    if (v.columns.length) html += "<p><strong>Kolumny:</strong> " + v.columns.join(", ") + "</p>";
    if (v.sql) html += "<pre><code>" + escapeHtml(v.sql) + "</code></pre>";
    detail.innerHTML = html;
  } else if (type === "package") {
    const p = DATA.packages.find(x => x.name === name);
    if (!p) return;
    let html = "<h3>Pakiet: " + p.name + "</h3>";
    if (p.spec.length) {
      html += "<h4>Specyfikacja</h4><table><tr><th>Nazwa</th><th>Typ</th><th>Parametry</th><th>Zwraca</th><th>Opis</th></tr>";
      p.spec.forEach(s => {
        html += "<tr><td>" + s.name + "</td><td>" + s.type + "</td><td>" + (s.params||"\u2014") + "</td><td>" + (s["return"]||"\u2014") + "</td><td>" + (s.desc||"\u2014") + "</td></tr>";
      });
      html += "</table>";
    }
    if (p.body_source) {
      html += "<details><summary>Implementacja (body)</summary><pre><code>" + escapeHtml(p.body_source) + "</code></pre></details>";
    }
    detail.innerHTML = html;
  } else if (type === "sequence") {
    const s = DATA.sequences.find(x => x.name === name);
    if (!s) return;
    detail.innerHTML = "<h3>Sekwencja: " + s.name + "</h3><p>Start: " + s.start + ", Increment: " + s.incr + "</p>";
  }
}

function escapeHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

// === MAP ===
function initMap() {
  window._mapInit = true;
  const pageList = document.getElementById("page-list");
  const dbList = document.getElementById("db-list");
  // Strony APEX
  let pHtml = "";
  DATA.pages.forEach(p => {
    pHtml += "<div class=\\"map-item\\" data-page=\\""+ p.id +"\\" onclick=\\"highlightFromPage("+ p.id +")\\">" +
             "Strona " + p.id + ": " + p.name + "</div>";
  });
  pageList.innerHTML = pHtml;
  // Obiekty DB
  let dHtml = "";
  const allObjects = [...DATA.tables.map(t=>t.name), ...DATA.views.map(v=>v.name)];
  allObjects.forEach(n => {
    dHtml += "<div class=\\"map-item\\" data-obj=\\""+ n +"\\" onclick=\\"highlightFromObject('"+ n +"')\\">" + n + "</div>";
  });
  dbList.innerHTML = dHtml;
}

function highlightFromPage(pageId) {
  clearHighlights();
  const linked = DATA.links.filter(l => l.page_id === pageId);
  const objects = new Set();
  linked.forEach(l => l.objects.forEach(o => objects.add(o)));
  document.querySelectorAll("[data-page=\\""+ pageId +"\\"]").forEach(e => e.classList.add("highlight"));
  objects.forEach(o => {
    document.querySelectorAll("[data-obj=\\""+ o +"\\"]").forEach(e => e.classList.add("highlight"));
  });
}

function highlightFromObject(name) {
  clearHighlights();
  const linked = DATA.links.filter(l => l.objects.includes(name));
  const pages = new Set(linked.map(l => l.page_id));
  document.querySelectorAll("[data-obj=\\""+ name +"\\"]").forEach(e => e.classList.add("highlight"));
  pages.forEach(p => {
    document.querySelectorAll("[data-page=\\""+ p +"\\"]").forEach(e => e.classList.add("highlight"));
  });
}

function clearHighlights() {
  document.querySelectorAll(".map-item").forEach(e => e.classList.remove("highlight"));
}

// === SEARCH ===
function handleSearch(query) {
  if (!query || query.length < 2) return;
  const q = query.toUpperCase();
  // Podświetl w drzewie przeglądarki
  document.querySelectorAll(".tree-item").forEach(el => {
    el.style.display = el.textContent.toUpperCase().includes(q) ? "" : "none";
  });
}

// Init first tab on load
window.addEventListener("DOMContentLoaded", () => { initDiagram(); });
'''
