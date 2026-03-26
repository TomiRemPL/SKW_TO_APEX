# apex_export_to_md/renderers/html_renderer.py
"""Renderer interaktywnego HTML — self-contained plik z vis.js i Prism.js.

Zawiera 3 zakładki:
1. Diagram relacji (vis.js network graph)
2. Przeglądarka bazy danych (drzewo + panel szczegółów)
3. Mapa APEX ↔ DB (połączenia stron ze tabelami + panel szczegółów strony)

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
                     "params": ", ".join(f"{pr.name} {pr.direction} {pr.data_type}"
                                         for pr in s.parameters),
                     "return": s.return_type or "",
                     "desc": s.description or ""}
                    for s in p.body_subprograms
                ],
                "body_source": p.body_source,
                "constants": p.constants,
                "error_codes": [{"code": c, "text": t} for c, t in p.error_codes],
            })

        # Sekwencje
        sequences = [{"name": s.name, "start": s.start_with or "",
                       "incr": s.increment_by or "",
                       "cache": "NOCACHE" if s.nocache else (s.cache or "")}
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

        # Strony APEX — pełne dane
        pages = []
        for p in app.pages:
            pages.append({
                "id": p.id,
                "name": p.name,
                "title": p.title or p.name,
                "page_mode": p.page_mode,
                "regions": [
                    {
                        "name": r.name,
                        "type": r.type,
                        "title": r.title or r.name,
                        "source_table": r.source_table or "",
                        "source_sql": r.source_sql or "",
                        "parent_region": r.parent_region or "",
                        "editable": r.editable,
                        "allowed_operations": r.allowed_operations,
                        "columns": [
                            {
                                "name": col.name,
                                "type": col.type,
                                "heading": col.heading or "",
                                "source_column": col.source_column or "",
                                "data_type": col.data_type or "",
                                "link_target": col.link_target or "",
                                "lov": col.lov or "",
                                "primary_key": col.primary_key,
                            }
                            for col in r.columns
                        ],
                    }
                    for r in p.regions
                ],
                "items": [
                    {
                        "name": it.name,
                        "type": it.type,
                        "label": it.label or "",
                        "source_column": it.source_column or "",
                        "lov": it.lov or "",
                        "default_value": it.default_value or "",
                    }
                    for it in p.items
                ],
                "buttons": [
                    {
                        "name": b.name,
                        "label": b.label or b.name,
                        "action": b.action or "",
                        "target_page": b.target_page,
                        "is_hot": b.is_hot,
                    }
                    for b in p.buttons
                ],
                "processes": [
                    {
                        "name": pr.name,
                        "type": pr.type,
                        "language": pr.language or "",
                        "point": pr.point,
                        "code": pr.code or "",
                        "condition": pr.condition or "",
                        "when_button_pressed": pr.when_button_pressed or "",
                    }
                    for pr in p.processes
                ],
                "dynamic_actions": [
                    {
                        "name": da.name,
                        "event": da.event,
                        "selection_type": da.selection_type or "",
                        "trigger_selector": da.trigger_selector or "",
                        "actions": [
                            {
                                "type": step.type,
                                "code": step.code or "",
                                "affected_elements": step.affected_elements or "",
                                "fire_on_initialization": step.fire_on_initialization,
                            }
                            for step in da.actions
                        ],
                    }
                    for da in p.dynamic_actions
                ],
                "validations": [
                    {
                        "name": v.name,
                        "type": v.type,
                        "code": v.code or "",
                        "condition": v.condition or "",
                    }
                    for v in p.validations
                ],
                "branches": [
                    {
                        "name": br.name or "",
                        "type": br.type,
                        "target_page": br.target_page,
                        "target_url": br.target_url or "",
                        "point": br.point,
                        "condition": br.condition or "",
                    }
                    for br in p.branches
                ],
                "css_inline": p.css_inline or "",
                "js_inline": p.js_inline or "",
            })

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
{self._prism_css_inline()}
</style>
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
      <div class="map-sidebar">
        <div id="apex-pages" class="map-column">
          <h3>Strony APEX</h3>
          <div id="page-list"></div>
        </div>
        <div id="db-objects" class="map-column">
          <h3>Obiekty bazy danych</h3>
          <div id="db-list"></div>
        </div>
      </div>
      <div id="page-detail-panel" class="page-detail-panel">
        <div class="page-detail-placeholder">
          \u2190 Kliknij na stron\u0119 APEX, aby zobaczy\u0107 szczeg\u00f3\u0142y
        </div>
      </div>
    </div>
  </div>
</main>

<footer>
  <span>Wygenerowano narz\u0119dziem <strong>apex_export_to_md</strong></span>
  <span>Autor: <strong>{author}</strong></span>
  <span>Wsp\u00f3\u0142praca: <strong>Claude</strong> (Anthropic)</span>
</footer>

<script>
// === DATA ===
const DATA = {data_json};
</script>

<script>
{self._vis_js_inline()}
</script>

<script>
{self._prism_js_inline()}
</script>

<script>
{self._javascript()}
</script>

</body>
</html>'''

    def _vis_js_inline(self) -> str:
        """Zwróć vis-network.min.js jako inline string."""
        vis_path = Path(__file__).parent / "vendor" / "vis-network.min.js"
        if vis_path.exists():
            return vis_path.read_text(encoding="utf-8")
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

    def _prism_js_inline(self) -> str:
        """Zwróć prism.min.js jako inline string."""
        prism_path = Path(__file__).parent / "vendor" / "prism.min.js"
        if prism_path.exists():
            return prism_path.read_text(encoding="utf-8")
        logger.warning("prism.min.js nie znaleziony w vendor/")
        return '/* prism.js not bundled */\n'

    def _prism_css_inline(self) -> str:
        """Zwróć prism.min.css jako inline string."""
        css_path = Path(__file__).parent / "vendor" / "prism.min.css"
        if css_path.exists():
            return css_path.read_text(encoding="utf-8")
        return '/* prism.css not bundled */\n'

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
/* === MAP LAYOUT === */
.map-layout { display: flex; gap: 16px; align-items: flex-start; }
.map-sidebar { display: flex; flex-direction: column; gap: 12px; width: 320px;
               flex-shrink: 0; }
.map-column { background: #fff; border: 1px solid #ddd; border-radius: 4px;
              padding: 12px; max-height: 35vh; overflow-y: auto; }
.map-column h3 { font-size: 14px; color: #1a365d; margin-bottom: 8px; }
.map-item { padding: 6px 10px; cursor: pointer; border-radius: 3px;
            font-size: 13px; margin: 2px 0; }
.map-item:hover { background: #e8edf3; }
.map-item.highlight { background: #d4a843; color: #1a365d; font-weight: 600; }
.map-item.selected { background: #1a365d; color: white; font-weight: 600; }
/* === PAGE DETAIL PANEL === */
.page-detail-panel { flex: 1; background: #fff; border: 1px solid #ddd;
                     border-radius: 4px; padding: 16px; max-height: 80vh;
                     overflow-y: auto; }
.page-detail-placeholder { color: #999; font-style: italic; text-align: center;
                           padding: 40px 20px; }
.page-detail-panel h2 { font-size: 18px; color: #1a365d; margin-bottom: 4px; }
.page-detail-panel .page-meta { color: #666; font-size: 13px; margin-bottom: 16px; }
/* === COLLAPSIBLE SECTIONS === */
.section { margin-bottom: 12px; border: 1px solid #e2e8f0; border-radius: 4px; }
.section-header { display: flex; align-items: center; gap: 8px; padding: 10px 14px;
                  background: #f7fafc; cursor: pointer; user-select: none;
                  border-radius: 4px; }
.section-header:hover { background: #edf2f7; }
.section-header h3 { font-size: 14px; color: #1a365d; margin: 0; flex: 1; }
.section-badge { background: #1a365d; color: white; border-radius: 10px;
                 padding: 1px 8px; font-size: 11px; font-weight: 600; }
.section-arrow { font-size: 10px; color: #999; transition: transform 0.2s; }
.section.open .section-arrow { transform: rotate(90deg); }
.section-body { display: none; padding: 12px 14px; border-top: 1px solid #e2e8f0; }
.section.open .section-body { display: block; }
/* === CODE BLOCKS (Prism overrides) === */
.page-detail-panel pre[class*="language-"] { margin: 8px 0; border-radius: 4px;
    font-size: 12px; max-height: 400px; overflow: auto; }
.page-detail-panel code[class*="language-"] { font-family: "Fira Code", Consolas,
    "Courier New", monospace; font-size: 12px; }
/* === SUBSECTIONS === */
.subsection { margin: 8px 0; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.subsection:last-child { border-bottom: none; }
.subsection-title { font-weight: 600; color: #2d3748; font-size: 13px;
                    margin-bottom: 4px; }
.subsection-meta { font-size: 12px; color: #718096; margin-bottom: 6px; }
.badge { display: inline-block; padding: 1px 6px; border-radius: 3px;
         font-size: 11px; font-weight: 500; margin-right: 4px; }
.badge-type { background: #e2e8f0; color: #4a5568; }
.badge-hot { background: #fed7d7; color: #c53030; }
.badge-point { background: #c6f6d5; color: #276749; }
.badge-event { background: #bee3f8; color: #2b6cb0; }
.badge-trigger { background: #fefcbf; color: #975a16; }
.badge-lang { background: #e9d8fd; color: #6b46c1; }
.badge-pk { background: #fed7d7; color: #c53030; font-weight: 700; }
.badge-link { background: #bee3f8; color: #2b6cb0; }
.db-links-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
.db-link-chip { background: #edf2f7; border: 1px solid #cbd5e0; border-radius: 4px;
                padding: 2px 8px; font-size: 12px; color: #2d3748; }
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
        """Logika JS — zakładki, diagram, przeglądarka, mapa, szczegóły strony."""
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
  const network = new vis.Network(container, { nodes: new vis.DataSet(nodes), edges }, {
    layout: { hierarchical: { direction: "UD", sortMethod: "hubsize", nodeSpacing: 200 } },
    physics: false,
    interaction: { hover: true, dragNodes: true },
    edges: { smooth: { type: "cubicBezier" } }
  });
  network.once("afterDrawing", () => {
    const positions = network.getPositions();
    network.setOptions({
      layout: { hierarchical: { enabled: false } },
      physics: { enabled: false }
    });
    Object.keys(positions).forEach(id => {
      network.body.nodes[id].x = positions[id].x;
      network.body.nodes[id].y = positions[id].y;
    });
    network.redraw();
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
         + "<td>" + (c.default || "\\u2014") + "</td>"
         + "<td>" + (c.comment || "\\u2014") + "</td></tr>";
  });
  html += "</table>";
  if (t.constraints.length) {
    html += "<h4>Constraints</h4><ul>";
    t.constraints.forEach(c => {
      let desc = c.type + ": " + c.name;
      if (c.type === "FK") desc += " \\u2192 " + c.ref_table + "(" + c.ref_columns.join(",") + ")";
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
        "<td>" + (c.default || "\\u2014") + "</td>" +
        "<td>" + (c.comment || "\\u2014") + "</td></tr>";
    });
    html += "</table>";
    if (t.constraints.length) {
      html += "<h4>Constraints</h4><ul>";
      t.constraints.forEach(c => {
        let d = "<strong>" + c.type + "</strong>: " + c.name + " (" + c.columns.join(", ") + ")";
        if (c.type === "FK") d += " \\u2192 " + c.ref_table;
        if (c.type === "CHK") d += " \\u2014 " + c.check_expr;
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
    if (v.sql) html += codeBlock(v.sql, "sql");
    detail.innerHTML = html;
    highlightCode(detail);
  } else if (type === "package") {
    const p = DATA.packages.find(x => x.name === name);
    if (!p) return;
    let html = "<h3>Pakiet: " + p.name + "</h3>";
    if (p.spec.length) {
      html += "<h4>Specyfikacja</h4><table><tr><th>Nazwa</th><th>Typ</th><th>Parametry</th><th>Zwraca</th><th>Opis</th></tr>";
      p.spec.forEach(s => {
        html += "<tr><td>" + s.name + "</td><td>" + s.type + "</td><td>" + (s.params||"\\u2014") + "</td><td>" + (s["return"]||"\\u2014") + "</td><td>" + (s.desc||"\\u2014") + "</td></tr>";
      });
      html += "</table>";
    }
    if (p.body_source) {
      html += "<details><summary>Implementacja (body)</summary>" + codeBlock(p.body_source, "plsql") + "</details>";
    }
    detail.innerHTML = html;
    highlightCode(detail);
  } else if (type === "sequence") {
    const s = DATA.sequences.find(x => x.name === name);
    if (!s) return;
    detail.innerHTML = "<h3>Sekwencja: " + s.name + "</h3><p>Start: " + s.start + ", Increment: " + s.incr + "</p>";
  }
}

// === HELPERS ===
function escapeHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function codeBlock(code, lang) {
  if (!code) return "";
  return "<pre class=\\"language-" + lang + "\\"><code class=\\"language-" + lang + "\\">" + escapeHtml(code) + "</code></pre>";
}

function highlightCode(container) {
  if (typeof Prism !== "undefined") {
    container.querySelectorAll("pre code").forEach(el => Prism.highlightElement(el));
  }
}

function detectLang(code, langHint) {
  if (langHint) {
    const h = langHint.toLowerCase();
    if (h.includes("plsql") || h.includes("pl/sql")) return "plsql";
    if (h.includes("javascript") || h.includes("js")) return "javascript";
  }
  if (!code) return "sql";
  const upper = code.toUpperCase();
  if (upper.includes("BEGIN") || upper.includes("DECLARE") || upper.includes("EXCEPTION"))
    return "plsql";
  if (code.includes("function") || code.includes("var ") || code.includes("apex."))
    return "javascript";
  return "sql";
}

// === MAP ===
function initMap() {
  window._mapInit = true;
  const pageList = document.getElementById("page-list");
  const dbList = document.getElementById("db-list");
  let pHtml = "";
  DATA.pages.forEach(p => {
    pHtml += "<div class=\\"map-item\\" data-page=\\""+ p.id +"\\" onclick=\\"selectPage("+ p.id +")\\">" +
             "Strona " + p.id + ": " + p.name + "</div>";
  });
  pageList.innerHTML = pHtml;
  let dHtml = "";
  const allObjects = [...DATA.tables.map(t=>t.name), ...DATA.views.map(v=>v.name)];
  allObjects.forEach(n => {
    dHtml += "<div class=\\"map-item\\" data-obj=\\""+ n +"\\" onclick=\\"highlightFromObject('"+ n +"')\\">" + n + "</div>";
  });
  dbList.innerHTML = dHtml;
}

function selectPage(pageId) {
  // Podświetl stronę i powiązane obiekty DB
  clearHighlights();
  document.querySelectorAll("[data-page]").forEach(e => e.classList.remove("selected"));
  document.querySelectorAll("[data-page=\\""+ pageId +"\\"]").forEach(e => e.classList.add("selected"));
  const linked = DATA.links.filter(l => l.page_id === pageId);
  const objects = new Set();
  linked.forEach(l => l.objects.forEach(o => objects.add(o)));
  objects.forEach(o => {
    document.querySelectorAll("[data-obj=\\""+ o +"\\"]").forEach(e => e.classList.add("highlight"));
  });
  // Pokaż szczegóły strony
  showPageDetail(pageId);
}

function highlightFromObject(name) {
  clearHighlights();
  document.querySelectorAll("[data-page]").forEach(e => e.classList.remove("selected"));
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

// === PAGE DETAIL ===
function showPageDetail(pageId) {
  const page = DATA.pages.find(p => p.id === pageId);
  if (!page) return;
  const panel = document.getElementById("page-detail-panel");
  let html = "<h2>Strona " + page.id + ": " + page.name + "</h2>";
  html += "<div class=\\"page-meta\\">";
  if (page.title && page.title !== page.name) html += "Tytu\\u0142: " + escapeHtml(page.title) + " | ";
  html += "Tryb: " + page.page_mode;
  html += "</div>";

  // Powiązania DB
  const linked = DATA.links.filter(l => l.page_id === pageId);
  if (linked.length) {
    const dbObjs = new Set();
    linked.forEach(l => l.objects.forEach(o => dbObjs.add(o)));
    html += "<div class=\\"db-links-list\\" style=\\"margin-bottom:12px\\">";
    dbObjs.forEach(o => { html += "<span class=\\"db-link-chip\\">" + o + "</span>"; });
    html += "</div>";
  }

  // Regiony
  if (page.regions.length) {
    html += section("Regiony", page.regions.length, renderRegions(page.regions), true);
  }
  // Elementy formularza
  if (page.items.length) {
    html += section("Elementy formularza", page.items.length, renderItems(page.items));
  }
  // Przyciski
  if (page.buttons.length) {
    html += section("Przyciski", page.buttons.length, renderButtons(page.buttons));
  }
  // Procesy
  if (page.processes.length) {
    html += section("Procesy", page.processes.length, renderProcesses(page.processes));
  }
  // Dynamic Actions
  if (page.dynamic_actions.length) {
    html += section("Dynamic Actions", page.dynamic_actions.length, renderDynamicActions(page.dynamic_actions));
  }
  // Walidacje
  if (page.validations.length) {
    html += section("Walidacje", page.validations.length, renderValidations(page.validations));
  }
  // Branching
  if (page.branches.length) {
    html += section("Branching", page.branches.length, renderBranches(page.branches));
  }
  // Inline CSS
  if (page.css_inline) {
    html += section("Inline CSS", null, codeBlock(page.css_inline, "css"));
  }
  // Inline JS
  if (page.js_inline) {
    html += section("Inline JavaScript", null, codeBlock(page.js_inline, "javascript"));
  }

  panel.innerHTML = html;
  highlightCode(panel);

  // Domyślnie otwórz sekcję Regiony
  const firstSection = panel.querySelector(".section");
  if (firstSection) firstSection.classList.add("open");
}

function section(title, count, bodyHtml, openByDefault) {
  const badge = count !== null ? " <span class=\\"section-badge\\">" + count + "</span>" : "";
  return "<div class=\\"section" + (openByDefault ? " open" : "") + "\\">" +
    "<div class=\\"section-header\\" onclick=\\"this.parentElement.classList.toggle('open')\\">" +
    "<span class=\\"section-arrow\\">\\u25B6</span>" +
    "<h3>" + title + badge + "</h3></div>" +
    "<div class=\\"section-body\\">" + bodyHtml + "</div></div>";
}

function renderRegions(regions) {
  let html = "";
  regions.forEach(r => {
    html += "<div class=\\"subsection\\">";
    html += "<div class=\\"subsection-title\\">" + escapeHtml(r.title || r.name) + "</div>";
    html += "<div class=\\"subsection-meta\\">";
    html += "<span class=\\"badge badge-type\\">" + r.type + "</span>";
    if (r.source_table) html += " \\u2190 tabela: <strong>" + r.source_table + "</strong>";
    if (r.editable) html += " <span class=\\"badge badge-hot\\">edytowalny</span>";
    if (r.allowed_operations.length) html += " [" + r.allowed_operations.join(", ") + "]";
    if (r.parent_region) html += " | region nadrz\\u0119dny: " + r.parent_region;
    html += "</div>";
    if (r.source_sql) {
      html += codeBlock(r.source_sql, "sql");
    }
    if (r.columns.length) {
      html += "<table><tr><th>Kolumna</th><th>Typ</th><th>Nag\\u0142\\u00f3wek</th><th>\\u0179r\\u00f3d\\u0142o</th><th>Info</th></tr>";
      r.columns.forEach(c => {
        let info = "";
        if (c.primary_key) info += "<span class=\\"badge badge-pk\\">PK</span> ";
        if (c.link_target) info += "<span class=\\"badge badge-link\\">\\u2192 str." + c.link_target + "</span> ";
        if (c.lov) info += "LOV: " + c.lov;
        html += "<tr><td>" + c.name + "</td><td>" + c.type + "</td>" +
          "<td>" + (c.heading || "\\u2014") + "</td>" +
          "<td>" + (c.source_column || "\\u2014") + "</td>" +
          "<td>" + (info || "\\u2014") + "</td></tr>";
      });
      html += "</table>";
    }
    html += "</div>";
  });
  return html;
}

function renderItems(items) {
  let html = "<table><tr><th>Nazwa</th><th>Typ</th><th>Label</th><th>Kolumna</th><th>LOV</th><th>Domy\\u015blnie</th></tr>";
  items.forEach(it => {
    html += "<tr><td>" + it.name + "</td><td>" + it.type + "</td>" +
      "<td>" + (it.label || "\\u2014") + "</td>" +
      "<td>" + (it.source_column || "\\u2014") + "</td>" +
      "<td>" + (it.lov || "\\u2014") + "</td>" +
      "<td>" + (it.default_value || "\\u2014") + "</td></tr>";
  });
  return html + "</table>";
}

function renderButtons(buttons) {
  let html = "";
  buttons.forEach(b => {
    html += "<div class=\\"subsection\\">";
    html += "<span class=\\"subsection-title\\">" + b.name + "</span>";
    if (b.is_hot) html += " <span class=\\"badge badge-hot\\">PRIMARY</span>";
    html += "<div class=\\"subsection-meta\\">";
    html += "Label: <strong>" + (b.label || b.name) + "</strong>";
    if (b.action) html += " | Akcja: " + b.action;
    if (b.target_page) html += " | \\u2192 Strona " + b.target_page;
    html += "</div></div>";
  });
  return html;
}

function renderProcesses(processes) {
  let html = "";
  processes.forEach(pr => {
    html += "<div class=\\"subsection\\">";
    html += "<div class=\\"subsection-title\\">" + escapeHtml(pr.name) + "</div>";
    html += "<div class=\\"subsection-meta\\">";
    html += "<span class=\\"badge badge-type\\">" + pr.type + "</span>";
    if (pr.language) html += " <span class=\\"badge badge-lang\\">" + pr.language + "</span>";
    html += " <span class=\\"badge badge-point\\">" + pr.point + "</span>";
    if (pr.when_button_pressed) html += " | przycisk: <strong>" + pr.when_button_pressed + "</strong>";
    if (pr.condition) html += " | warunek: " + escapeHtml(pr.condition);
    html += "</div>";
    if (pr.code) {
      const lang = detectLang(pr.code, pr.language);
      html += codeBlock(pr.code, lang);
    }
    html += "</div>";
  });
  return html;
}

function renderDynamicActions(das) {
  let html = "";
  das.forEach(da => {
    html += "<div class=\\"subsection\\">";
    html += "<div class=\\"subsection-title\\">" + escapeHtml(da.name) + "</div>";
    html += "<div class=\\"subsection-meta\\">";
    html += "<span class=\\"badge badge-event\\">" + da.event + "</span>";
    if (da.selection_type) html += " <span class=\\"badge badge-trigger\\">" + da.selection_type + "</span>";
    if (da.trigger_selector) html += " \\u2192 " + escapeHtml(da.trigger_selector);
    html += "</div>";
    if (da.actions.length) {
      da.actions.forEach((step, i) => {
        html += "<div style=\\"margin-left:16px;margin-top:6px\\">";
        html += "<strong>Krok " + (i+1) + ":</strong> " + step.type;
        if (step.affected_elements) html += " \\u2192 " + escapeHtml(step.affected_elements);
        if (step.fire_on_initialization) html += " <span class=\\"badge badge-point\\">init</span>";
        if (step.code) {
          const lang = detectLang(step.code, step.type);
          html += codeBlock(step.code, lang);
        }
        html += "</div>";
      });
    }
    html += "</div>";
  });
  return html;
}

function renderValidations(validations) {
  let html = "";
  validations.forEach(v => {
    html += "<div class=\\"subsection\\">";
    html += "<div class=\\"subsection-title\\">" + escapeHtml(v.name) + "</div>";
    html += "<div class=\\"subsection-meta\\">";
    html += "<span class=\\"badge badge-type\\">" + v.type + "</span>";
    if (v.condition) html += " | warunek: " + escapeHtml(v.condition);
    html += "</div>";
    if (v.code) {
      html += codeBlock(v.code, detectLang(v.code, "plsql"));
    }
    html += "</div>";
  });
  return html;
}

function renderBranches(branches) {
  let html = "";
  branches.forEach(br => {
    html += "<div class=\\"subsection\\">";
    html += "<div class=\\"subsection-title\\">" + (br.name || br.type) + "</div>";
    html += "<div class=\\"subsection-meta\\">";
    if (br.target_page) html += "\\u2192 Strona " + br.target_page;
    if (br.target_url) html += "\\u2192 URL: " + escapeHtml(br.target_url);
    html += " <span class=\\"badge badge-point\\">" + br.point + "</span>";
    if (br.condition) html += " | warunek: " + escapeHtml(br.condition);
    html += "</div></div>";
  });
  return html;
}

// === SEARCH ===
function handleSearch(query) {
  if (!query || query.length < 2) return;
  const q = query.toUpperCase();
  document.querySelectorAll(".tree-item").forEach(el => {
    el.style.display = el.textContent.toUpperCase().includes(q) ? "" : "none";
  });
}

// Init first tab on load
window.addEventListener("DOMContentLoaded", () => { initDiagram(); });
'''
