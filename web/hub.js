/* Claude Hub — dashboard front end. Vanilla JS, no build step.
   Recreated from design_handoff_claude_hub. Wires the design to the brain dashboard's
   real endpoints; where a metric has no data source yet (token/spend analytics), it shows
   an honest "—" rather than inventing numbers. */
(() => {
"use strict";

// ── helpers ────────────────────────────────────────────────────────────────
let TOKEN = null;
async function token() {
  if (TOKEN) return TOKEN;
  const r = await fetch("/api/config", { cache: "no-store" });
  TOKEN = (await r.json()).token;
  return TOKEN;
}
async function api(path, opts = {}) {
  const t = await token();
  const r = await fetch(path, {
    ...opts,
    headers: { Authorization: `Bearer ${t}`, "Content-Type": "application/json", ...(opts.headers || {}) },
    cache: "no-store",
  });
  if (!r.ok) {
    let msg = `${path} → ${r.status}`;
    try { const j = await r.json(); if (j && j.error) msg = j.error; } catch {}
    const err = new Error(msg); err.status = r.status;
    throw err;
  }
  return r.status === 204 ? null : r.json();
}
const enc = encodeURIComponent;
const $ = (s, r = document) => r.querySelector(s);
function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}
function frag(...nodes) { const f = document.createDocumentFragment(); nodes.forEach((n) => n && f.append(n)); return f; }

const PALETTE = ["#6B9E72", "#7B8CC4", "#C4A05F", "#B0736F", "#8A8578", "#8B6BE8", "#9C7BF0", "#6D4AC4"];
const _pc = {};
function projColor(name) {
  if (_pc[name]) return _pc[name];
  let h = 0; for (const ch of name || "") h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return (_pc[name] = PALETTE[h % PALETTE.length]);
}
function pdot(name) { const d = el("span", "pdot"); d.style.background = projColor(name); return d; }
function relTime(iso) {
  if (!iso) return "";
  const t = Date.parse(iso); if (isNaN(t)) return "";
  const s = Math.max(0, (Date.now() - t) / 1000);
  if (s < 90) return "just now";
  if (s < 3600) return `${Math.round(s / 60)}m ago`;
  if (s < 86400) return `${Math.round(s / 3600)}h ago`;
  return `${Math.round(s / 86400)}d ago`;
}

// ── nav / routing ──────────────────────────────────────────────────────────
const VIEWS = {
  overview:   { label: "Overview",   sec: "WORKSPACE", title: "Overview" },
  board:      { label: "Board",      sec: "WORKSPACE", title: "Board", sub: "Tasks across every project · drag to move, or say “move it to done”" },
  artifacts:  { label: "Artifacts",  sec: "WORKSPACE", title: "Artifacts" },
  projects:   { label: "All apps",   sec: "APPS", title: "Apps", sub: "Everything you have going, across chat and Claude Code" },
  command:    { label: "Command",    sec: "TOOLS", title: "Command", sub: "Orchestrator moving work through brainstorm, plan, build, review, ship · talk to it below" },
  connectors: { label: "Connectors", sec: "TOOLS", title: "Connectors", sub: "MCP servers and integrations available to every session" },
  usage:      { label: "Usage",      sec: "ACCOUNT", title: "Usage", sub: "Current billing period" },
  project:    { hidden: true, sub: "Developer dashboard" },
};
let current = "overview", currentArg;
let stopActive = null;  // teardown for the current view's pollers
let APPS = [];          // registered projects, listed first-class in the rail

function navItem(view, arg, label, dotColor) {
  const b = el("button", "item");
  b.dataset.view = view;
  if (arg) b.dataset.arg = arg;
  const dot = el("span", "dot");
  if (dotColor) dot.style.background = dotColor;
  b.append(dot, el("span", "lbl", label));
  b.onclick = () => go(view, arg);
  return b;
}
function buildNav() {
  const nav = $("#nav"); nav.innerHTML = "";
  for (const sec of ["WORKSPACE", "APPS", "TOOLS", "ACCOUNT"]) {
    nav.append(el("div", "sec", sec));
    if (sec === "APPS") APPS.forEach((a) => nav.append(navItem("project", a.name, a.name, projColor(a.name))));
    for (const [key, v] of Object.entries(VIEWS)) if (!v.hidden && v.sec === sec) nav.append(navItem(key, null, v.label));
  }
  highlightNav();
}
function highlightNav() {
  document.querySelectorAll(".nav .item").forEach((b) => b.classList.toggle("on",
    current === "project" ? b.dataset.view === "project" && b.dataset.arg === currentArg : b.dataset.view === current));
}
function setNavMeta(counts) {
  document.querySelectorAll(".nav .item").forEach((b) => {
    const c = counts[b.dataset.view];
    let m = b.querySelector(".meta");
    if (c == null) { if (m) m.remove(); return; }
    if (!m) { m = el("span", "meta"); b.append(m); }
    m.textContent = c;
  });
}
async function go(key, arg) {
  if (stopActive) { stopActive(); stopActive = null; }
  current = key; currentArg = arg;
  const v = VIEWS[key];
  highlightNav();
  $("#view-title").textContent = arg || v.title;
  $("#view-sub").textContent = v.sub || "";
  const hash = arg ? `#/${key}/${enc(arg)}` : `#/${key}`;
  if (location.hash !== hash) history.pushState(null, "", hash);
  const pane = $("#pane"); pane.innerHTML = ""; pane.classList.remove("fill");
  pane.append(el("p", "empty", "loading…"));
  try { await RENDER[key](pane, arg); } catch (e) { pane.innerHTML = ""; pane.append(el("p", "empty", "failed: " + e.message)); }
  pane.scrollTop = 0;
}
function route() {
  const [key, ...rest] = location.hash.replace(/^#\/?/, "").split("/");
  const arg = rest.length ? decodeURIComponent(rest.join("/")) : undefined;
  if (key === "project" && arg) return go("project", arg);
  return go(VIEWS[key] && !VIEWS[key].hidden ? key : "overview");
}

// ── shared bits ─────────────────────────────────────────────────────────────
function tile(lbl, val, delta, up) {
  const t = el("div", "tile");
  t.append(el("div", "lbl", lbl), el("div", "val", val));
  if (delta != null) t.append(el("div", "delta" + (up ? " up" : ""), delta));
  return t;
}
function sectionHead(title, note, noteR) {
  const h = el("div", "h-row");
  h.append(el("h2", null, title));
  if (note) h.append(el("span", "note", note));
  if (noteR) h.append(el("span", "note r", noteR));
  return h;
}

// ── views ────────────────────────────────────────────────────────────────────
const RENDER = {};

RENDER.overview = async (pane) => {
  const [projects, tasks, arts] = await Promise.all([api("/api/projects"), api("/api/tasks"), api("/api/artifacts").catch(() => ({ items: [] }))]);
  pane.innerHTML = "";
  const active = projects.filter((p) => p.status === "active").length;
  const open = tasks.filter((t) => t.status !== "done").length;
  const artCount = (arts.items || []).length;
  const tiles = el("div", "tiles");
  tiles.append(
    tile("PROJECTS", String(projects.length), `${active} active`, active > 0),
    tile("OPEN TASKS", String(open), `${tasks.length} total`),
    tile("ARTIFACTS", String(artCount), "in the archive"),
    tile("TOKENS TODAY", "—", "not tracked yet"),
  );
  pane.append(tiles);

  // Pick up where you left off — most recently updated tasks
  const recent = [...tasks].filter((t) => t.updated).sort((a, b) => (a.updated < b.updated ? 1 : -1)).slice(0, 3);
  pane.append(sectionHeadBlock("Pick up where you left off", `${recent.length} RECENT`));
  const rg = el("div", "resume-grid");
  recent.forEach((t) => {
    const c = el("div", "resume");
    const rn = el("div", "rn"); rn.append(pdot(t.project), el("span", null, t.project));
    const time = el("span", "mono"); time.style.marginLeft = "auto"; time.style.fontSize = "10.5px"; time.style.color = "var(--faint)"; time.textContent = relTime(t.updated);
    rn.append(time);
    c.append(rn, el("div", "snip", t.title));
    const rb = el("div", "rb");
    const btn = el("button", null, "Open board"); btn.onclick = () => go("board");
    rb.append(btn, el("span", "mono", (t.status || "").toUpperCase()));
    c.append(rb);
    rg.append(c);
  });
  if (!recent.length) rg.append(el("div", "dash", "nothing recent"));
  pane.append(rg);

  // two-col: activity chart + recent artifacts
  const two = el("div", "two block");
  const left = el("div", "card"); left.style.padding = "15px 16px";
  left.append(sectionHead("Activity, last 14 days", null, "TASKS TOUCHED"));
  left.append(activityBars(tasks));
  const right = el("div", "card"); right.style.padding = "15px 16px";
  right.append(sectionHead("Recent artifacts"));
  (arts.items || []).slice(0, 6).forEach((a) => {
    const row = el("div"); row.style.display = "flex"; row.style.alignItems = "center"; row.style.gap = "10px"; row.style.padding = "7px 0";
    row.append(el("span", "thumb"));
    const mid = el("div"); mid.style.flex = "1"; mid.style.minWidth = "0";
    const nm = el("div", null, a.name); nm.style.fontSize = "12.5px"; nm.style.whiteSpace = "nowrap"; nm.style.overflow = "hidden"; nm.style.textOverflow = "ellipsis";
    mid.append(nm, el("div", "mono", `${(a.kind || "").toUpperCase()} · ${a.project}`));
    mid.querySelector(".mono").style.fontSize = "9.5px"; mid.querySelector(".mono").style.color = "var(--muted)";
    row.append(mid);
    right.append(row);
  });
  if (!(arts.items || []).length) right.append(el("div", "dash", "no artifacts yet"));
  two.append(left, right);
  pane.append(two);
};

function sectionHeadBlock(title, note) {
  const h = el("div", "h-row block");
  h.append(el("h2", null, title));
  if (note) { const n = el("span", "note", note); h.append(n); }
  return h;
}
function activityBars(tasks) {
  const days = Array(14).fill(0);
  const now = new Date(); now.setHours(0, 0, 0, 0);
  tasks.forEach((t) => {
    const d = Date.parse(t.updated); if (isNaN(d)) return;
    const diff = Math.floor((now - new Date(d).setHours(0, 0, 0, 0)) / 86400000);
    if (diff >= 0 && diff < 14) days[13 - diff]++;
  });
  const max = Math.max(1, ...days);
  const wrap = el("div", "bars");
  days.forEach((v, i) => {
    const b = el("i"); b.style.height = `${Math.max(4, (v / max) * 100)}%`;
    if (i === 13) b.className = "today"; else if (i >= 10) b.className = "recent";
    b.title = `${v} tasks`;
    wrap.append(b);
  });
  return wrap;
}

let projectsFilter = "all";
RENDER.projects = async (pane) => {
  const all = await api("/api/projects");
  pane.innerHTML = "";
  const chips = el("div", "chips");
  [["all", "All projects"], ["active", "Active"], ["shipped", "Shipped"], ["archived", "Archived"]].forEach(([key, label]) => {
    const ch = el("span", "chip" + (projectsFilter === key ? " on" : ""), label);
    ch.onclick = () => { projectsFilter = key; RENDER.projects(pane); };
    chips.append(ch);
  });
  pane.append(chips);
  const projects = projectsFilter === "all" ? all : all.filter((p) => p.status === projectsFilter);
  const card = el("div", "card"); card.style.overflow = "hidden";
  const tbl = el("table", "tbl");
  tbl.innerHTML = "<thead><tr><th>PROJECT</th><th>PHASE</th><th>REPO</th><th>TASKS</th><th>STATUS</th></tr></thead>";
  const tb = el("tbody");
  if (!projects.length) { const tr = el("tr"); const c = el("td", "empty", "no projects match"); c.colSpan = 5; tr.append(c); tb.append(tr); }
  projects.forEach((p) => {
    const tr = el("tr", "click");
    tr.onclick = () => go("project", p.name);
    const nameTd = el("td"); const nm = el("div", "pname"); nm.append(pdot(p.name), el("span", null, p.name)); nameTd.append(nm);
    const repo = (p.root || "").split("/").slice(-1)[0];
    tr.append(nameTd, td(p.phase || "—"), tdm(repo), td(`${p.tasks_open}/${p.tasks_total}`), statusTd(p.status));
    tb.append(tr);
  });
  tbl.append(tb); card.append(tbl); pane.append(card);
};
function td(t) { const d = el("td", null, t); return d; }
function tdm(t) { const d = el("td"); const s = el("span", "m", t); d.append(s); return d; }
function statusTd(s) { const d = el("td"); d.append(el("span", "pill " + s, (s || "").toUpperCase())); return d; }

let boardFilter = "all";
let boardShowDone = false;
try { boardFilter = localStorage.getItem("boardFilter") || "all"; } catch {}
try { boardShowDone = localStorage.getItem("boardShowDone") === "1"; } catch {}
function setBoardFilter(v) { boardFilter = v; try { localStorage.setItem("boardFilter", v); } catch {} }
function setBoardShowDone(v) { boardShowDone = v; try { localStorage.setItem("boardShowDone", v ? "1" : "0"); } catch {} }

RENDER.board = async (pane) => {
  const [tasks, projects] = await Promise.all([api("/api/tasks"), api("/api/projects")]);
  pane.innerHTML = "";
  // If the remembered project filter no longer exists, fall back to all.
  if (boardFilter !== "all" && !projects.some((p) => p.name === boardFilter)) setBoardFilter("all");
  const chips = el("div", "chips");
  const allc = el("span", "chip" + (boardFilter === "all" ? " on" : ""), "all projects");
  allc.onclick = () => { setBoardFilter("all"); RENDER.board(pane); };
  chips.append(allc);
  projects.forEach((p) => {
    const ch = el("span", "chip" + (boardFilter === p.name ? " on" : ""));
    ch.append(pdot(p.name), el("span", null, p.name));
    ch.onclick = () => { setBoardFilter(p.name); RENDER.board(pane); };
    chips.append(ch);
  });
  const shown = boardFilter === "all" ? tasks : tasks.filter((t) => t.project === boardFilter);
  const blocked = shown.filter((t) => t.status === "review").length;
  const doneCount = shown.filter((t) => t.status === "done").length;
  // "Show done" toggle — collapses the biggest, least-actionable column by default.
  const doneChip = el("span", "chip r toggle" + (boardShowDone ? " on" : ""), `${boardShowDone ? "✓ " : ""}show done · ${doneCount}`);
  doneChip.onclick = () => { setBoardShowDone(!boardShowDone); RENDER.board(pane); };
  chips.append(doneChip);
  const cnt = el("span", "note mono", `${shown.length - (boardShowDone ? 0 : doneCount)} OPEN · ${blocked} WAITING ON YOU`);
  chips.append(cnt);
  pane.append(chips);

  const ALL_COLS = [
    { key: "backlog", label: "BACKLOG", color: "#4A4258", statuses: ["backlog", "ready"] },
    { key: "doing", label: "IN PROGRESS", color: "var(--accent)", statuses: ["doing"] },
    { key: "review", label: "WAITING ON YOU", color: "#C4A05F", statuses: ["review"] },
    { key: "done", label: "DONE", color: "#6B9E72", statuses: ["done"] },
  ];
  const COLS = boardShowDone ? ALL_COLS : ALL_COLS.filter((c) => c.key !== "done");
  const kb = el("div", "kanban" + (boardShowDone ? "" : " cols-3"));
  COLS.forEach((col) => {
    const items = shown.filter((t) => col.statuses.includes(t.status));
    const c = el("div", "kcol"); c.dataset.status = col.key;
    const head = el("div", "khead");
    const d = el("span", "d"); d.style.background = col.color;
    head.append(d, el("span", "t", col.label), el("span", "c", String(items.length)));
    c.append(head);
    items.forEach((t) => c.append(taskCard(t, pane)));
    if (!items.length) c.append(el("div", "dash", "nothing here"));
    // drop target
    c.ondragover = (e) => { e.preventDefault(); };
    c.ondrop = async (e) => {
      e.preventDefault();
      const id = e.dataTransfer.getData("id"), proj = e.dataTransfer.getData("proj"), from = e.dataTransfer.getData("from");
      if (!id || from === col.key) return;
      try { await api(`/api/tasks/${encodeURIComponent(proj)}/${id}/status`, { method: "POST", body: JSON.stringify({ status: col.key }) }); }
      catch (err) { /* transition may be invalid; ignore */ }
      RENDER.board(pane);
    };
    kb.append(c);
  });
  pane.append(kb);
};
function taskCard(t, pane) {
  const c = el("div", "kcard"); c.draggable = true;
  c.ondragstart = (e) => { e.dataTransfer.setData("id", t.id); e.dataTransfer.setData("proj", t.project); e.dataTransfer.setData("from", t.status); c.classList.add("drag"); };
  c.ondragend = () => c.classList.remove("drag");
  const top = el("div", "top");
  top.append(pdot(t.project), el("span", "pn", t.project), el("span", "id", "#" + t.id));
  c.append(top, el("div", "ttl", t.title));
  const foot = el("div", "foot");
  const tagCls = t.status === "review" ? "tag needs" : t.status === "done" ? "tag done" : "tag";
  const tagTx = t.status === "review" ? "NEEDS YOU" : t.type ? t.type.toUpperCase() : "TASK";
  foot.append(el("span", tagCls, tagTx));
  c.append(foot);
  return c;
}

let artifactsFilter = "all";
RENDER.artifacts = async (pane) => {
  const data = await api("/api/artifacts").catch(() => ({ items: [] }));
  pane.innerHTML = "";
  const all = data.items || [];
  $("#view-sub").textContent = `${all.length} artifacts · docs, tasks, sessions and deliverables`;
  const kinds = ["all", ...Array.from(new Set(all.map((a) => a.kind)))];
  const chips = el("div", "chips");
  kinds.forEach((k) => {
    const ch = el("span", "chip" + (artifactsFilter === k ? " on" : ""), k === "all" ? "All" : k.endsWith("s") ? k : k + "s");
    ch.onclick = () => { artifactsFilter = k; RENDER.artifacts(pane); };
    chips.append(ch);
  });
  pane.append(chips);
  const items = artifactsFilter === "all" ? all : all.filter((a) => a.kind === artifactsFilter);
  const grid = el("div", "art-grid");
  items.forEach((a) => {
    const c = el("div", "card art-card int");
    const prev = el("div", "prev");
    const pv = el("div", "pv");
    if (a.title) pv.append(el("div", "pvt", a.title));
    if (a.excerpt) pv.append(el("div", "pvx", a.excerpt));
    if (!a.title && !a.excerpt) pv.append(el("div", "pvt", (a.kind || "file").toUpperCase()));
    prev.append(pv);
    const body = el("div", "body");
    body.append(el("div", "an", a.name), el("div", "ak", `${(a.kind || "").toUpperCase()} · ${relTime(a.modified) || ""}`));
    const ap = el("div", "ap"); ap.append(pdot(a.project), el("span", null, a.project));
    body.append(ap);
    c.append(prev, body);
    grid.append(c);
  });
  if (!items.length) grid.append(el("div", "dash", "no artifacts archived yet — run /sync or open a project"));
  pane.append(grid);
};

RENDER.command = async (pane) => {
  const [runs, agents, pipeline] = await Promise.all([
    api("/api/runs").catch(() => ({ runs: [] })),
    api("/api/agents").catch(() => []),
    api("/api/pipeline").catch(() => ({ columns: [], projects: [] })),
  ]);
  pane.innerHTML = "";
  const runList = runs.runs || runs || [];
  const cost = (runs.totals && runs.totals.cost_usd) || runList.reduce((s, r) => s + (r.cost_usd || r.cost || 0), 0);

  // orchestrator panel
  const orch = el("div", "orch");
  const otop = el("div", "top");
  otop.append(nucleus("avatar"));
  const oid = el("div"); oid.style.minWidth = "0";
  oid.append(el("div", null, "Orchestrator"), el("div", "mono", "opus · planning and dispatch"));
  oid.querySelector("div").style.fontSize = "14.5px"; oid.querySelector("div").style.fontWeight = "600";
  oid.querySelector(".mono").style.color = "var(--v-tx3)"; oid.querySelector(".mono").style.fontSize = "10px";
  otop.append(oid);
  const st = el("div", "st");
  [["IN PIPELINE", pipeline.projects.length], ["RUNS", runList.length], ["SPEND", "$" + cost.toFixed(2)]].forEach(([l, v]) => {
    const s = el("div", "s"); s.append(el("div", "l", l), el("div", "v", String(v))); st.append(s);
  });
  otop.append(st); orch.append(otop, el("div", "div"));
  const cols = el("div", "cols");
  const cd = el("div"); cd.append(el("div", "lbl", "CURRENT DIRECTIVE"), el("div", "directive", "Move each project through brainstorm → plan → build → review → ship. Escalate blocked work to you."));
  const dl = el("div"); dl.append(el("div", "lbl", "DISPATCH LOG"));
  const log = el("div", "dlog");
  runList.slice(0, 5).forEach((r) => {
    const line = el("div"); line.style.color = "var(--a3)";
    line.textContent = `→ ${r.persona || "agent"} · ${(r.task || r.result || "").slice(0, 42)}`;
    log.append(line);
  });
  if (!runList.length) log.append(el("div", "empty", "no dispatches yet"));
  dl.append(log); cols.append(cd, dl); orch.append(cols);
  pane.append(orch);

  // pipeline (projects by workflow phase)
  pane.append(sectionHeadBlock("Pipeline", `${pipeline.columns.length} STAGES · ${pipeline.projects.length} PROJECTS`));
  const STAGES = [["brainstorm", "BRAINSTORM", "#7B8CC4"], ["plan", "PLAN", "var(--accent)"], ["build", "BUILD", "var(--accent)"], ["review", "REVIEW", "#C4A05F"], ["reflect", "SHIP", "#6B9E72"]];
  const grid = el("div", "pipeline");
  STAGES.forEach(([key, label, color], idx) => {
    const col = el("div", "stage");
    const node = el("div", "snode");
    const circ = el("span", "ncirc"); circ.style.borderColor = color;
    if (idx === STAGES.length - 1) circ.style.background = color;
    node.append(circ);
    if (idx < STAGES.length - 1) { const rail = el("span", "nrail"); node.append(rail); }
    const sh = el("div", "sh", label); sh.style.color = color;
    col.append(node, sh, el("div", "sm", ""));
    const inStage = pipeline.projects.filter((p) => p.phase === key || (key === "build" && p.phase === "scaffold"));
    inStage.forEach((p) => {
      const w = el("div", "worker");
      const wn = el("div", "wn"); const sd = el("span", "sd"); sd.style.background = color; wn.append(sd, el("span", null, p.name)); w.append(wn);
      w.append(el("div", "step", p.status ? p.status.toUpperCase() : ""));
      const pt = el("div", "ptrack"); const fill = el("i"); fill.style.width = "60%"; fill.style.background = color; pt.append(fill); w.append(pt);
      col.append(w);
    });
    if (!inStage.length) col.append(el("div", "dash", "idle"));
    grid.append(col);
  });
  pane.append(grid);

  // recent runs table
  pane.append(sectionHeadBlock("Recent runs", `$${cost.toFixed(2)} TOTAL`));
  const card = el("div", "card"); card.style.overflow = "hidden";
  const tbl = el("table", "tbl");
  tbl.innerHTML = "<thead><tr><th>PERSONA</th><th>SCOPE</th><th>TASK</th><th>COST</th></tr></thead>";
  const tb = el("tbody");
  runList.slice(0, 12).forEach((r) => {
    const tr = el("tr");
    const rc = r.cost_usd != null ? r.cost_usd : r.cost;
    tr.append(td(r.persona || "agent"), tdm(r.scoped_dir || r.dir || "—"), td((r.task || r.result || "").slice(0, 60)), tdm(rc != null ? "$" + Number(rc).toFixed(3) : "—"));
    tb.append(tr);
  });
  if (!runList.length) { const tr = el("tr"); const c = el("td", "empty", "no runs yet"); c.colSpan = 4; tr.append(c); tb.append(tr); }
  tbl.append(tb); card.append(tbl); pane.append(card);

  // transcript drawer (closed by default) + voice dock
  pane.append(buildDrawer());
  pane.append(buildDock());
  wireDock();
  renderTranscript();
};

function voiceCard(name, state, color, note, vol) {
  const c = el("div", "card conn-card");
  const ch = el("div", "ch"); const d = el("span", "d"); d.style.background = color;
  ch.append(d, el("span", "n", name)); const s = el("span", "s", state); s.style.color = color; ch.append(s);
  c.append(ch, el("div", "note", note), el("div", "vol", vol));
  return c;
}
RENDER.connectors = async (pane) => {
  const health = await api("/api/health");
  pane.innerHTML = "";

  // Voice input sources (Wispr Flow = external dictation; local daemon = live status).
  pane.append(sectionHead("Voice input"));
  const vgrid = el("div", "conn-grid");
  vgrid.append(voiceCard("Wispr Flow", "ACTIVE", "var(--green)",
    "System-wide AI dictation — types into the focused app (Claude Code, chat, anywhere). External app, no live status.",
    "hold Fn"));
  const dLive = health.voice_connected;
  vgrid.append(voiceCard("Local voice daemon", dLive ? "RUNNING" : "OFF", dLive ? "var(--green)" : "var(--faint)",
    "Local Whisper → claude -p → speech, with the live dashboard visualization. Optional — run `python -m voice.daemon`.",
    "127.0.0.1:8765"));
  pane.append(vgrid);

  pane.append(sectionHead("MCP servers"));
  const grid = el("div", "conn-grid");
  (health.mcps || []).forEach((m) => {
    const connected = m.token_set;
    const needsAuth = m.needs_token && !m.token_set;
    const state = needsAuth ? ["NEEDS AUTH", "var(--red)"] : connected ? ["CONNECTED", "var(--green)"] : ["READY", "var(--sand)"];
    const c = el("div", "card conn-card");
    const ch = el("div", "ch"); const d = el("span", "d"); d.style.background = state[1];
    ch.append(d, el("span", "n", m.name)); const s = el("span", "s", state[0]); s.style.color = state[1]; ch.append(s);
    c.append(ch, el("div", "note", m.needs_token ? "Requires an auth token to be set in settings." : "No auth required."));
    c.append(el("div", "vol", "MCP server"));
    grid.append(c);
  });
  if (!(health.mcps || []).length) grid.append(el("div", "dash", "no MCP servers configured"));
  pane.append(grid);
};

RENDER.usage = async (pane) => {
  const [projects, tasks, arts] = await Promise.all([api("/api/projects"), api("/api/tasks"), api("/api/artifacts").catch(() => ({ items: [] }))]);
  const usage = await api("/api/usage").catch(() => null);
  pane.innerHTML = "";
  const done = tasks.filter((t) => t.status === "done").length;
  const tiles = el("div", "tiles");
  const spend = usage && usage.run_cost != null ? "$" + usage.run_cost.toFixed(2) : "—";
  tiles.append(
    tile("PROJECTS", String(projects.length), `${projects.filter((p) => p.status === "active").length} active`),
    tile("TASKS DONE", String(done), `${tasks.length} total`),
    tile("AGENT SPEND", spend, usage ? `${usage.run_count || 0} runs` : "not tracked"),
    tile("TOKENS", "—", "not tracked yet"),
  );
  pane.append(tiles);

  // by-project task share
  const cols = el("div", "usage-cols block");
  const left = el("div", "card"); left.style.padding = "15px 16px";
  left.append(sectionHead("Tasks by project"));
  const maxT = Math.max(1, ...projects.map((p) => p.tasks_total));
  projects.forEach((p) => left.append(ubar(p.name, p.tasks_total, maxT, projColor(p.name), `${p.tasks_total}`)));
  const right = el("div", "card"); right.style.padding = "15px 16px";
  right.append(sectionHead("Open work by project"));
  const maxO = Math.max(1, ...projects.map((p) => p.tasks_open));
  projects.forEach((p) => right.append(ubar(p.name, p.tasks_open, maxO, "var(--accent)", `${p.tasks_open}`)));
  cols.append(left, right);
  pane.append(cols);
};
function ubar(name, val, max, color, label) {
  const row = el("div", "urow");
  row.append(el("span", "un", name));
  const track = el("div", "track"); const i = el("i"); i.style.width = `${(val / max) * 100}%`; i.style.background = color; track.append(i);
  row.append(track, el("span", "uv", label));
  return row;
}

// ── app dashboards: master–detail, shared by the Hub view and the pop-out strip ─
// Left: a scannable list (servers with on/off switches, scripts by group, project info).
// Right: whatever is selected (description, inline form, run controls, live output).
// The pop-out strip is the same component in "compact" mode: list and detail drill in
// and out instead of sitting side by side. Forms are built once per selection and never
// redrawn by polling, so typing is never interrupted.
const NS = "http://www.w3.org/2000/svg";
const ICONS = {
  server: "M4 4h16v7H4z M4 13h16v7H4z M8 7.5h.01 M8 16.5h.01",
  play: "M8 5.5v13l11-6.5z",
  stop: "M7 7h10v10H7z",
  restart: "M3 12a9 9 0 1 0 2.6-6.4 M3 4v5h5",
  external: "M14 4h6v6 M20 4l-9 9 M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5",
  copy: "M9 9h11v11H9z M5 15H4V4h11v1",
  check: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18z M8 12.5l2.7 2.7L16 9.5",
  ok: "M5 12.5l4.5 4.5L19 7.5",
  x: "M6 6l12 12 M18 6L6 18",
  lock: "M6 11h12v9H6z M8.5 11V8a3.5 3.5 0 0 1 7 0v3",
  tag: "M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z M7.5 7.5h.01",
  list: "M9 6h12 M9 12h12 M9 18h12 M4 6h.01 M4 12h.01 M4 18h.01",
  ban: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18z M5.7 5.7l12.6 12.6",
  users: "M16 20v-1.5a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4V20 M9.5 3.5a3.5 3.5 0 1 0 0 7a3.5 3.5 0 1 0 0-7z M21 20v-1.5a4 4 0 0 0-3-3.9 M15.5 3.6a3.5 3.5 0 0 1 0 6.8",
  trash: "M4 7h16 M9 7V4h6v3 M6 7l1 13h10l1-13",
  browser: "M3 5h18v14H3z M3 9h18 M6 7h.01 M9 7h.01",
  pulse: "M3 12h4l2.5-6 5 12L17 12h4",
  chart: "M5 20v-7 M12 20V5 M19 20v-10 M3 20h18",
  git: "M6 3v12 M6 21a3 3 0 1 0 0-6a3 3 0 1 0 0 6z M18 3a3 3 0 1 0 0 6a3 3 0 1 0 0-6z M18 9a9 9 0 0 1-9 9",
  terminal: "M5 7l5 5-5 5 M12 17h7",
  mail: "M3 6h18v12H3z M3.5 6.5l8.5 6.5 8.5-6.5",
  key: "M8 16a4 4 0 1 0 0-8a4 4 0 1 0 0 8z M12 12h9 M17.5 12v3 M21 12v2",
  popout: "M4 5h16v14H4z M12 12h6v5h-6z",
  back: "M15 6l-6 6 6 6",
  globe: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18z M3 12h18 M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9 M12 3C9.5 5.6 8.2 8.6 8.2 12s1.3 6.4 3.8 9",
  cloud: "M7 18.5a4.5 4.5 0 0 1-.7-8.9 6 6 0 0 1 11.6 1.4A3.8 3.8 0 0 1 17.5 18.5z",
  db: "M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6 M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3",
  review: "M4 13h4l2 3h4l2-3h4 M6 5h12l2.5 8V19h-17v-6z",
  alert: "M12 4 2.5 20h19z M12 10v4.5 M12 17.5h.01",
  book: "M5 4h10a4 4 0 0 1 4 4v12H9a4 4 0 0 1-4-4z M5 16a4 4 0 0 1 4-4h10",
};
function icon(name, size = 16) {
  const s = document.createElementNS(NS, "svg");
  const attrs = { viewBox: "0 0 24 24", width: size, height: size, fill: "none", stroke: "currentColor",
    "stroke-width": "1.8", "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true", class: "ico" };
  for (const [k, v] of Object.entries(attrs)) s.setAttribute(k, v);
  const p = document.createElementNS(NS, "path");
  p.setAttribute("d", ICONS[name] || ICONS.terminal);
  s.append(p);
  return s;
}

const LIVE = ["running", "starting", "external"];
const STRIP_ROUTE = location.hash.startsWith("#/strip/");
const SECRETS_FILE = "~/.claude/brain-dashboard/secrets.json";
const STATE_TXT = { running: "Running", starting: "Starting", external: "Running in a terminal", stopped: "Stopped",
  conflict: "Port in use",
  crashed: "Crashed", idle: "Not run yet", passed: "Passed", failed: "Failed" };
const TONE = { running: "ok", starting: "warn", external: "ok", conflict: "warn", stopped: "off", crashed: "bad", idle: "off", passed: "ok", failed: "bad" };

function winOf(node) { return (node && node.ownerDocument && node.ownerDocument.defaultView) || window; }
function prodUrl(res) {
  return ((res && res.resources || []).find((r) => r.status_check?.config?.prod_url) || {}).status_check?.config?.prod_url;
}
function setupUrl(x) { const m = ((x && x.setup) || "").match(/https?:\/\/[^\s)]+/); return m ? m[0].replace(/[.,]+$/, "") : null; }
function ago(sec) { return sec ? relTime(new Date(sec * 1000).toISOString()) : ""; }
function duration(a) {
  if (!a.started) return "";
  const s = Math.max(0, (a.finished || Date.now() / 1000) - a.started);
  return s < 60 ? `${s.toFixed(1)}s` : `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
}

function btn(label, o = {}) {
  const b = el("button", ["btn", o.kind, o.iconOnly && "only", o.cls].filter(Boolean).join(" "));
  b.type = "button";
  if (o.icon) b.append(icon(o.icon, 15));
  if (o.iconOnly) b.setAttribute("aria-label", label); else b.append(el("span", null, label));
  if (o.title || o.iconOnly) b.title = o.title || label;
  if (o.onClick) b.onclick = o.onClick;
  if (o.busy) b.classList.add("busy");
  if (o.busy || o.disabled) b.disabled = true;
  return b;
}
function linkBtn(label, href, o = {}) {
  const a = el("a", ["btn", o.kind || "ghost", o.iconOnly && "only"].filter(Boolean).join(" "));
  a.href = href; a.target = "_blank"; a.rel = "noopener"; a.title = o.title || href;
  a.append(icon(o.icon || "external", 15));
  if (o.iconOnly) a.setAttribute("aria-label", label); else a.append(el("span", null, label));
  return a;
}
function flash(b, msg) {
  const span = b.querySelector("span");
  if (span) { const o = span.textContent; span.textContent = msg; setTimeout(() => (span.textContent = o), 1300); }
  else { b.dataset.flash = msg; setTimeout(() => delete b.dataset.flash, 1300); }
}
async function copyText(b, text) {
  try { await winOf(b).navigator.clipboard.writeText(text); flash(b, "Copied"); } catch { flash(b, "Copy failed"); }
}
function badge(state, extra) {
  const b = el("span", "badge " + (TONE[state] || "off"));
  b.append(el("span", "bdot"), el("span", null, (STATE_TXT[state] || state) + (extra ? ` · ${extra}` : "")));
  return b;
}
function notice(tone, ic, content, action) {
  const n = el("div", "nt " + tone);
  n.append(icon(ic, 16));
  const t = el("div", "nt-t");
  t.append(typeof content === "string" ? document.createTextNode(content) : content);
  n.append(t);
  if (action) n.append(action);
  return n;
}

// ── selection + operations ────────────────────────────────────────────────────
function findItem(ctx, key) {
  const [kind, ...rest] = key.split(":");
  const name = rest.join(":");
  if (kind === "svc") return ctx.runner.services.find((s) => s.name === name);
  if (kind === "act") return ctx.runner.actions.find((a) => a.name === name);
  return kind === "users" || kind === "res" ? {} : null;
}
function select(ctx, key) {
  ctx.sel = key;
  try { localStorage.setItem(`appsel:${ctx.name}`, key); } catch {}
  if (ctx.compact) ctx.drilled = true;
  ctx.logText = "";
  ctx.draw(true);
  ctx.refresh();
}
async function op(ctx, key, kind, item, opName, body = {}) {
  ctx.pending.add(key);
  delete ctx.err[key];
  ctx.draw(true);
  try {
    await api(`/api/devdash/${enc(ctx.name)}/${kind}/${enc(item)}/${opName}`, { method: "POST", body: JSON.stringify(body) });
  } catch (e) { ctx.err[key] = e.message; }
  ctx.pending.delete(key);
  await ctx.refresh();
  ctx.draw(true);
}
async function toggleServer(ctx, s) {
  const on = LIVE.includes(s.state), ext = s.state === "external";
  if (ext && !winOf(ctx.root).confirm(`${s.label} was started in a terminal. Stop it?`)) return;
  await op(ctx, `svc:${s.name}`, "services", s.name, on ? "stop" : "start", { external: ext });
}
function downNeeds(ctx, a) {
  return a.needs.map((n) => ctx.runner.services.find((s) => s.name === n)).filter((s) => s && !LIVE.includes(s.state));
}
function runnable(ctx, a) {
  const vals = ctx.form[`act:${a.name}`] || {};
  return !a.missing_secrets.length && !downNeeds(ctx, a).length && (!a.confirm || vals.__confirm === a.confirm);
}
function runAction(ctx, a) {
  const key = `act:${a.name}`;
  if (!runnable(ctx, a) || ctx.pending.has(key)) return;
  const vals = ctx.form[key] || {};
  const args = {};
  a.params.forEach((p) => { if (vals[p.name] !== undefined && vals[p.name] !== "") args[p.name] = vals[p.name]; });
  const body = { args };
  if (a.confirm) body.confirm = vals.__confirm;
  op(ctx, key, "actions", a.name, "run", body).then(() => {
    if (a.confirm && !ctx.err[key]) {  // don't leave a destructive action armed
      vals.__confirm = "";
      const inp = ctx.el.formBox && ctx.el.formBox.querySelector("[data-confirm]");
      if (inp) inp.value = "";
      ctx.draw(true);
    }
  });
}
async function testPassword(ctx, email) {
  if (!ctx.creds) ctx.creds = (await api(`/api/devdash/${enc(ctx.name)}/test-credentials`)).users;
  return (ctx.creds.find((u) => u.email === email) || {}).password;
}

// ── status bar ────────────────────────────────────────────────────────────────
function pill(tone, ic, label, value, href, onClick, title) {
  const p = href ? el("a", "pill2 " + tone) : onClick ? el("button", "pill2 " + tone) : el("span", "pill2 " + tone);
  if (href) { p.href = href; p.target = "_blank"; p.rel = "noopener"; }
  if (onClick) { p.type = "button"; p.onclick = onClick; }
  if (ic === "globe" || ic === "cloud" || ic === "db") p.classList.add("health");  // collapse to icon in the strip
  if (ic === "git") p.classList.add("gitp");
  p.title = [`${label}${value ? ` ${value}` : ""}`, title].filter(Boolean).join("\n");
  p.setAttribute("aria-label", `${label}${value ? ` ${value}` : ""}`);
  p.append(el("span", "bdot"), icon(ic, 14), el("b", null, label));
  if (value) p.append(el("span", "pv", value));
  return p;
}
function drawBar(ctx) {
  const B = ctx.el.bar; B.innerHTML = "";
  const { uptime: u, vercel: v, supabase: s, git: g, tracker: t, resources: res } = ctx.st;
  if (ctx.compact) {
    const head = el("div", "st-head");
    head.append(pdot(ctx.name));
    const sel = el("select", "appsel");
    sel.setAttribute("aria-label", "App");
    (ctx.projects || [{ name: ctx.name }]).forEach((p) => { const o = el("option", null, p.name); o.value = p.name; sel.append(o); });
    sel.value = ctx.name;
    sel.onchange = () => ctx.switchTo(sel.value);
    head.append(sel, btn("Refresh", { icon: "restart", kind: "ghost", iconOnly: true, onClick: () => ctx.refresh(true) }));
    B.append(head);
  }
  const pills = el("div", "pills");
  const prod = prodUrl(res);
  pills.append(u.configured
    ? pill(u.ok ? "ok" : "bad", "globe", "Prod", u.ok ? `${u.elapsed_ms}ms` : "down", prod, null, `${u.status_code ?? "no response"} in ${u.elapsed_ms}ms`)
    : pill("off", "globe", "Prod", "not set", null, null, u.reason));
  pills.append(v.configured
    ? pill(v.ok && v.deployment && v.deployment.state === "READY" ? "ok" : "bad", "cloud", "Deploy",
      ((v.deployment && v.deployment.state) || "error").toLowerCase(), null, null, v.deployment && v.deployment.url)
    : pill("off", "cloud", "Deploy", "connect", setupUrl(v), null, v.setup));
  pills.append(s.configured
    ? pill(s.ok && /ACTIVE/i.test(s.status || "") ? "ok" : "bad", "db", "Database", (s.status || "error").toLowerCase())
    : pill("off", "db", "Database", "connect", setupUrl(s), null, s.setup));
  if (g && g.configured) {
    const val = [g.uncommitted ? `${g.uncommitted} changed` : "clean", g.has_upstream && g.behind ? `${g.behind} behind` : ""].filter(Boolean).join(" · ");
    pills.append(pill(g.behind ? "warn" : "off", "git", g.branch, val, null, () => select(ctx, "act:git pull"), "Open Pull latest"));
  }
  const waiting = ((t || {}).in_review || []).length;
  pills.append(pill(waiting ? "warn" : "off", "review", `${waiting} to review`, "", null, () => {
    setBoardFilter(ctx.name);
    if (STRIP_ROUTE) window.open("/#/board", "_blank"); else location.hash = "#/board";
  }, "Open the Board filtered to this app"));
  B.append(pills);
  if (!ctx.compact) {
    B.append(el("span", "grow"));
    const links = el("div", "links");
    (res.resources || []).forEach((r) => {
      if (["hosting", "database", "source"].includes(r.category) && r.urls && r.urls.console) links.append(linkBtn(r.name, r.urls.console));
    });
    B.append(links, btn("Pop out", { icon: "popout", onClick: () => popOut(ctx.name), title: "Open an always-on-top control strip" }));
  }
}

// ── list ──────────────────────────────────────────────────────────────────────
function lrow(ctx, key, ic, label, meta, trailing) {
  const r = el("div", "lrow" + (ctx.sel === key ? " on" : ""));
  const main = el("button", "lrow-main");
  main.type = "button";
  main.setAttribute("aria-current", ctx.sel === key ? "true" : "false");
  main.append(icon(ic, 16), el("span", "lrow-l", label));
  if (meta) main.append(el("span", "lrow-m", meta));
  main.onclick = () => select(ctx, key);
  r.append(main);
  if (trailing) r.append(trailing);
  return r;
}
function serverSwitch(ctx, s) {
  const on = LIVE.includes(s.state);
  const busy = ctx.pending.has(`svc:${s.name}`);
  const sw = el("button", "sw" + (on ? " on" : "") + (busy ? " busy" : ""));
  sw.type = "button";
  sw.setAttribute("role", "switch");
  sw.setAttribute("aria-checked", String(on));
  sw.setAttribute("aria-label", `${s.label} ${on ? "on" : "off"}`);
  sw.title = busy ? "Working…" : on ? (s.state === "external" ? "Running in a terminal. Click to stop." : "Click to stop") : "Click to start";
  sw.disabled = busy || s.state === "conflict";
  sw.append(el("span", "sw-k"));
  sw.onclick = () => toggleServer(ctx, s);
  return sw;
}
function actionMark(ctx, a) {
  const m = el("span", "mark");
  if (ctx.pending.has(`act:${a.name}`) || a.state === "running") { m.classList.add("spin"); m.title = "Running"; return m; }
  if (a.missing_secrets.length) { m.append(icon("lock", 14)); m.classList.add("off"); m.title = `Needs ${a.missing_secrets.join(", ")}`; return m; }
  if (a.state === "passed") { m.append(icon("ok", 14)); m.classList.add("ok"); m.title = `Passed ${ago(a.finished)}`; }
  else if (a.state === "failed") { m.append(icon("x", 14)); m.classList.add("bad"); m.title = `Failed ${ago(a.finished)}`; }
  return m;
}
function drawList(ctx) {
  const L = ctx.el.list; L.innerHTML = "";
  const group = (title) => { const g = el("div", "lgroup"); g.append(el("h3", "lgroup-h", title)); L.append(g); return g; };
  const g1 = group("Servers");
  if (!ctx.runner.services.length) g1.append(el("p", "lnote", "None declared yet. Add them to .brain/services.json."));
  ctx.runner.services.forEach((s) => g1.append(lrow(ctx, `svc:${s.name}`, "server", s.label, s.port ? `:${s.port}` : "", serverSwitch(ctx, s))));
  const g2 = group("Scripts");
  const byGroup = new Map();
  ctx.runner.actions.forEach((a) => { const k = a.group || "Other"; if (!byGroup.has(k)) byGroup.set(k, []); byGroup.get(k).push(a); });
  for (const [name, items] of byGroup) {
    g2.append(el("div", "lsub", name));
    items.forEach((a) => g2.append(lrow(ctx, `act:${a.name}`, a.icon || "terminal", a.label, "", actionMark(ctx, a))));
  }
  const g3 = group("Project");
  const tu = ctx.st.test_users;
  if (tu && tu.declared) g3.append(lrow(ctx, "users", "users", "Test users", String(tu.users.length)));
  g3.append(lrow(ctx, "res", "book", "Resources", String(ctx.st.resources.resources.length)));
}

// ── detail ────────────────────────────────────────────────────────────────────
function drawHead(ctx, kind, item) {
  const H = ctx.el.head; H.innerHTML = "";
  const top = el("div", "dt-top");
  if (ctx.compact) top.append(btn("Back to list", { icon: "back", kind: "ghost", iconOnly: true, onClick: () => { ctx.drilled = false; ctx.draw(true); } }));
  const t = el("div", "dt-title");
  const acts = el("div", "dt-acts");
  const key = ctx.sel, busy = ctx.pending.has(key);
  let desc = "", cmd = "";
  if (kind === "svc") {
    t.append(icon("server", 18), el("h2", null, item.label), badge(item.state));
    const live = LIVE.includes(item.state), ext = item.state === "external";
    const confirmExt = () => !ext || winOf(ctx.root).confirm(`${item.label} was started in a terminal. Stop it?`);
    if (live) {
      if (item.url) acts.append(linkBtn(`Open :${item.port}`, item.url, { title: item.url }));
      acts.append(btn("Restart", { icon: "restart", busy, onClick: () => confirmExt() && op(ctx, key, "services", item.name, "restart", { external: ext }) }));
      acts.append(btn("Stop", { icon: "stop", busy, onClick: () => confirmExt() && op(ctx, key, "services", item.name, "stop", { external: ext }) }));
    } else {
      acts.append(btn("Start", { icon: "play", kind: "primary", busy, disabled: item.state === "conflict",
        onClick: () => op(ctx, key, "services", item.name, "start") }));
    }
    cmd = item.command;
  } else if (kind === "act") {
    const extra = item.state === "running" ? duration(item) : item.finished ? ago(item.finished) : "";
    t.append(icon(item.icon || "terminal", 18), el("h2", null, item.label));
    if (item.state !== "idle") t.append(badge(item.state, extra));
    if (item.state === "running") acts.append(btn("Stop", { icon: "stop", onClick: () => op(ctx, key, "actions", item.name, "stop") }));
    else {
      const b = btn("Run", { icon: "play", kind: item.confirm ? "danger" : "primary", busy, cls: "run",
        disabled: !runnable(ctx, item), onClick: () => runAction(ctx, item) });
      acts.append(b);
    }
    desc = item.description; cmd = item.command;
  } else if (kind === "users") {
    const tu = ctx.st.test_users || {};
    const c = tu.credentials || {};
    t.append(icon("users", 18), el("h2", null, "Test users"),
      el("span", "dt-sub", c.exists ? `Passwords set ${c.seeded_at ? relTime(c.seeded_at) : "on this machine"}` : "Not created on this machine yet"));
    ctx.runner.actions.filter((a) => /test users/i.test(a.group)).forEach((a) =>
      acts.append(btn(a.label, { icon: a.icon || "terminal", kind: "ghost", onClick: () => select(ctx, `act:${a.name}`) })));
    desc = tu.summary || "";
  } else {
    t.append(icon("book", 18), el("h2", null, "Resources"));
    desc = "External services this app depends on. Each name opens its console.";
  }
  top.append(t, acts);
  H.append(top);
  if (desc) H.append(el("p", "dt-desc", desc));
  if (cmd) H.append(el("code", "dt-cmd", "$ " + cmd));
}
function drawNotes(ctx, kind, item) {
  const N = ctx.el.notes; N.innerHTML = "";
  if (ctx.err[ctx.sel]) N.append(notice("bad", "alert", ctx.err[ctx.sel]));
  if (kind === "act") {
    if (item.missing_secrets.length) {
      const msg = el("span");
      msg.append(el("b", null, `Needs ${item.missing_secrets.join(", ")}`),
        document.createTextNode(` in ${SECRETS_FILE} or your environment.`));
      N.append(notice("warn", "lock", msg, btn("Copy path", { icon: "copy", kind: "ghost", onClick: (e) => copyText(e.currentTarget, SECRETS_FILE) })));
    }
    downNeeds(ctx, item).forEach((s) => N.append(notice("warn", "server", `Needs ${s.label} running.`,
      btn(`Start ${s.label}`, { icon: "play", busy: ctx.pending.has(`svc:${s.name}`), onClick: () => op(ctx, `svc:${s.name}`, "services", s.name, "start") }))));
  }
  if (kind === "svc" && item.state === "conflict") {
    const owner = item.owner || "";
    const app = APPS.find((a) => a.root && (owner === a.root || owner.startsWith(a.root + "/")));
    N.append(notice("warn", "alert", `Port ${item.port} is taken by ${app ? app.name : "another app"}'s server${app ? "" : ` (${owner || "unknown"})`}. Stop it there to run ${item.label} here.`,
      app && !STRIP_ROUTE ? btn(`Open ${app.name}`, { icon: "external", kind: "ghost", onClick: () => go("project", app.name) }) : null));
  }
  if (kind === "svc" && item.state === "crashed") N.append(notice("bad", "alert", "Exited unexpectedly. The output below shows why."));
}
function field(p, value, onInput) {
  const lab = el("label", "fld");
  lab.append(el("span", "fld-l", p.label + (p.required ? "" : " (optional)")));
  let inp;
  if (p.type === "select") {
    inp = el("select");
    p.options.forEach((o) => { const opt = el("option", null, o); opt.value = o; inp.append(opt); });
  } else {
    inp = el("input");
    inp.type = p.type === "number" ? "number" : "text";
    if (p.min != null) inp.min = p.min;
    if (p.max != null) inp.max = p.max;
    if (p.maxlen) inp.maxLength = p.maxlen;
    inp.autocomplete = "off"; inp.spellcheck = false;
    if (p.help) inp.placeholder = p.help;
  }
  inp.name = p.name;
  inp.value = value;
  inp.oninput = () => onInput(inp.value);
  lab.append(inp);
  if (p.help && p.type === "select") lab.append(el("span", "fld-h", p.help));
  return lab;
}
function buildForm(ctx, a) {
  const key = `act:${a.name}`;
  const vals = ctx.form[key] || (ctx.form[key] = {});
  const f = el("form", "dt-form");
  f.noValidate = true;
  const grid = el("div", "fgrid");
  const refreshRun = () => { const rb = ctx.el.head.querySelector(".run"); if (rb && !ctx.pending.has(key)) rb.disabled = !runnable(ctx, findItem(ctx, key)); };
  a.params.forEach((p) => {
    if (vals[p.name] === undefined && p.default != null) vals[p.name] = String(p.default);
    grid.append(field(p, vals[p.name] ?? "", (v) => { vals[p.name] = v; }));
  });
  if (a.confirm) {
    const lab = el("label", "fld confirm");
    lab.append(el("span", "fld-l", `Type ${a.confirm} to confirm`));
    const inp = el("input");
    inp.type = "text"; inp.autocomplete = "off"; inp.spellcheck = false; inp.dataset.confirm = "1";
    inp.value = vals.__confirm || "";
    inp.oninput = () => { vals.__confirm = inp.value.trim(); refreshRun(); };
    lab.append(inp);
    grid.append(lab);
  }
  f.append(grid);
  const submit = el("button"); submit.type = "submit"; submit.hidden = true;  // Enter runs it
  f.append(submit);
  f.onsubmit = (e) => { e.preventDefault(); runAction(ctx, findItem(ctx, key)); };
  return f;
}
function buildOutput(ctx) {
  const o = el("div", "out");
  const h = el("div", "out-h");
  h.append(icon("terminal", 15), el("span", "out-t", "Output"), el("span", "out-m"),
    btn("Copy output", { icon: "copy", kind: "ghost", iconOnly: true, onClick: (e) => copyText(e.currentTarget, o.querySelector("pre").textContent) }));
  o.append(h, el("pre", "out-b"));
  return o;
}
function updateOutput(ctx, kind, item) {
  const pre = ctx.el.out.querySelector("pre"), meta = ctx.el.out.querySelector(".out-m");
  const text = ctx.logText || "";
  const empty = kind === "svc"
    ? (item.state === "external" ? "Started in a terminal, so its output shows there. Restart it here to capture it." : "Start it to see its output here.")
    : "Run it to see the output here.";
  const show = text || empty;
  if (pre.textContent !== show) {
    const atBottom = pre.scrollTop + pre.clientHeight >= pre.scrollHeight - 8;
    pre.textContent = show;
    pre.classList.toggle("empty", !text);
    if (atBottom || !text) pre.scrollTop = pre.scrollHeight;
  }
  meta.textContent = kind === "act" && item.started
    ? [item.state === "running" ? "running" : item.exit_code != null ? `exit ${item.exit_code}` : "", duration(item)].filter(Boolean).join(" · ")
    : "";
}
function drawUsers(ctx) {
  const U = ctx.el.box;
  const tu = ctx.st.test_users || {};
  const sig = JSON.stringify([tu.users, tu.credentials]);
  if (U.dataset.sig === sig) return;
  U.dataset.sig = sig; U.innerHTML = "";
  const canPw = tu.credentials && tu.credentials.exists;
  (tu.users || []).forEach((u) => {
    const r = el("div", "urow2");
    const av = el("span", "avatar", (u.username || "?")[0].toUpperCase());
    av.style.background = projColor(u.username);
    const meta = el("div", "u-meta");
    meta.append(el("div", "u-name", "@" + u.username), el("div", "u-has", u.has || u.email));
    meta.title = [u.email, u.has, u.friends && `Friends: ${u.friends}`].filter(Boolean).join("\n");
    const acts = el("div", "u-acts");
    acts.append(btn("Copy email", { icon: "mail", kind: "ghost", iconOnly: ctx.compact, title: `Copy ${u.email}`, onClick: (e) => copyText(e.currentTarget, u.email) }));
    if (canPw) acts.append(btn("Copy password", { icon: "key", kind: "ghost", iconOnly: ctx.compact, onClick: async (e) => {
      const b = e.currentTarget;
      try { const pw = await testPassword(ctx, u.email); pw ? copyText(b, pw) : flash(b, "No password"); } catch { flash(b, "Failed"); }
    } }));
    r.append(av, meta, acts);
    U.append(r);
  });
  if (!(tu.users || []).length) U.append(el("p", "lnote", "No test users declared."));
}
function drawResources(ctx) {
  const U = ctx.el.box;
  if (U.dataset.sig === String(ctx.stAt)) return;
  U.dataset.sig = String(ctx.stAt); U.innerHTML = "";
  const byCat = {};
  for (const r of ctx.st.resources.resources) (byCat[r.category] ||= []).push(r);
  for (const cat of Object.keys(byCat).sort()) {
    const row = el("div", "res-row");
    row.append(el("span", "res-cat", cat.replace(/-/g, " ")));
    const names = el("div", "res-names");
    byCat[cat].forEach((r) => {
      const item = r.urls && r.urls.console ? el("a", "res-link", r.name) : el("span", "res-link", r.name);
      if (r.urls && r.urls.console) { item.href = r.urls.console; item.target = "_blank"; item.rel = "noopener"; }
      if (r.plan) item.title = r.plan;
      names.append(item);
    });
    row.append(names);
    U.append(row);
  }
}
function drawDetail(ctx) {
  const D = ctx.el.detail, key = ctx.sel;
  const kind = key.split(":")[0];
  const item = findItem(ctx, key);
  if (!item) return;
  if (D.dataset.key !== key) {
    D.dataset.key = key; D.innerHTML = "";
    ctx.el.head = el("div", "dt-head"); ctx.el.notes = el("div", "dt-notes");
    ctx.el.formBox = ctx.el.out = ctx.el.box = null;
    D.append(ctx.el.head, ctx.el.notes);
    if (kind === "act" && (item.params.length || item.confirm)) D.append(ctx.el.formBox = buildForm(ctx, item));
    if (kind === "users" || kind === "res") D.append(ctx.el.box = el("div", kind === "users" ? "users" : "res"));
    else D.append(ctx.el.out = buildOutput(ctx));
    ctx.headSig = null;
  }
  const headSig = JSON.stringify([item, ctx.pending.has(key), ctx.err[key], ctx.stAt, ctx.runner.services.map((s) => s.state)]);
  if (headSig !== ctx.headSig) { ctx.headSig = headSig; drawHead(ctx, kind, item); drawNotes(ctx, kind, item); }
  if (kind === "users") drawUsers(ctx);
  else if (kind === "res") drawResources(ctx);
  else updateOutput(ctx, kind, item);
}

// ── mount ─────────────────────────────────────────────────────────────────────
function mountApp(root, name, compact) {
  const win = winOf(root);
  root.innerHTML = "";
  root.className = "appv" + (compact ? " compact" : "");
  const bar = el("div", "appv-bar"), body = el("div", "appv-body");
  const list = el("nav", "appv-list"), detail = el("section", "appv-detail");
  list.setAttribute("aria-label", `${name} controls`);
  const toast = el("div", "appv-toast hidden");
  toast.setAttribute("role", "status");
  body.append(list, detail);
  root.append(bar, body, toast);
  detail.append(el("p", "empty", "loading…"));
  const ctx = { name, root, compact, el: { bar, list, detail }, sel: null, drilled: false, runner: null, st: null,
    stAt: 0, logText: "", creds: null, form: {}, pending: new Set(), err: {}, projects: null };
  try { ctx.sel = localStorage.getItem(`appsel:${name}`); } catch {}
  let toastTimer = null;
  ctx.toast = (msg) => {
    toast.textContent = msg; toast.classList.remove("hidden");
    win.clearTimeout(toastTimer); toastTimer = win.setTimeout(() => toast.classList.add("hidden"), 6000);
  };
  ctx.draw = (force) => {
    if (!ctx.runner || !ctx.st) return;
    root.classList.toggle("drilled", !!(compact && ctx.drilled));
    const s1 = JSON.stringify([ctx.stAt, ctx.projects && ctx.projects.length]);
    if (force || s1 !== ctx.sig1) { ctx.sig1 = s1; drawBar(ctx); }
    const s2 = JSON.stringify([ctx.runner, ctx.sel, [...ctx.pending], ctx.stAt]);
    if (force || s2 !== ctx.sig2) { ctx.sig2 = s2; drawList(ctx); }
    drawDetail(ctx);
  };
  let busy = false;
  ctx.refresh = async (full) => {
    if (busy) return;
    busy = true;
    try {
      const prev = ctx.runner;
      const [runner, st] = await Promise.all([
        api(`/api/devdash/${enc(name)}/runner`),
        full || !ctx.st ? api(`/api/devdash/${enc(name)}`) : null,
      ]);
      if (st) { ctx.st = st; ctx.stAt = Date.now(); }
      // a script just finished → git/tracker/test-user state may have changed, and any
      // cached test passwords are stale (e.g. after "Create or refresh")
      if (prev && prev.actions.some((a) => a.state === "running" && runner.actions.find((x) => x.name === a.name)?.state !== "running")) {
        ctx.st = await api(`/api/devdash/${enc(name)}`); ctx.stAt = Date.now(); ctx.creds = null;
      }
      ctx.runner = runner;
      if (!ctx.sel || !findItem(ctx, ctx.sel)) {
        ctx.sel = runner.services[0] ? `svc:${runner.services[0].name}` : runner.actions[0] ? `act:${runner.actions[0].name}` : "res";
      }
      const [k, ...rest] = ctx.sel.split(":");
      ctx.logText = k === "svc" || k === "act"
        ? (await api(`/api/devdash/${enc(name)}/log/${k === "svc" ? "services" : "actions"}/${enc(rest.join(":"))}?lines=300`)).log
        : "";
      if (compact && !ctx.projects) ctx.projects = await api("/api/projects");
      ctx.draw();
    } catch (e) {
      ctx.toast(e.message);
    } finally { busy = false; }
  };
  const t1 = win.setInterval(() => ctx.refresh(false), 2000);
  const t2 = win.setInterval(() => ctx.refresh(true), 30000);
  const stop = () => { win.clearInterval(t1); win.clearInterval(t2); };
  ctx.switchTo = (n) => { stop(); mountApp(root, n, compact); };  // the new mount re-registers root._stop
  root._stop = stop;
  ctx.refresh(true);
  return () => root._stop && root._stop();
}

RENDER.project = async (pane, name) => {
  pane.innerHTML = "";
  pane.classList.add("fill");
  const root = el("div");
  pane.append(root);
  stopActive = mountApp(root, name, false);
};

// Document Picture-in-Picture gives a real always-on-top window (Chrome/Edge/Arc). Elsewhere,
// fall back to a plain popup of the #/strip route (not always-on-top).
function copyStyles(doc) {
  for (const ss of document.styleSheets) {
    try {
      const s = doc.createElement("style");
      s.textContent = [...ss.cssRules].map((r) => r.cssText).join("\n");
      doc.head.append(s);
    } catch {
      if (ss.href) { const l = doc.createElement("link"); l.rel = "stylesheet"; l.href = ss.href; doc.head.append(l); }
    }
  }
}
async function popOut(name) {
  const popup = () => window.open(`/#/strip/${enc(name)}`, "hub-strip", "popup,width=400,height=780");
  if (!window.documentPictureInPicture) return popup();
  let pip;
  try {  // embedded browsers can expose the API yet refuse ("no window"), so fall back
    if (documentPictureInPicture.window) documentPictureInPicture.window.close();
    pip = await documentPictureInPicture.requestWindow({ width: 400, height: 780 });
  } catch { return popup(); }
  copyStyles(pip.document);
  pip.document.title = `${name} · Claude Hub`;
  pip.document.body.className = "strip-body";
  const root = el("div");
  const shell = el("div", "strip");
  shell.append(root);
  pip.document.body.append(shell);
  const stop = mountApp(root, name, true);
  pip.addEventListener("pagehide", stop);
}

// ── voice nucleus + dock ─────────────────────────────────────────────────────
function nucleus(kind) {
  const n = el("div", "nucleus " + kind); n.dataset.live = "false";
  n.innerHTML = `<div class="ring"></div><div class="ring b"></div><div class="halo"></div>
    <div class="membrane"></div><div class="swirl"></div>
    <div class="satw"><div class="sat"></div></div><div class="satw b"><div class="sat"></div></div>
    <div class="nw"><div class="core"></div></div><div class="nucl"></div>`;
  NUCLEI.push(n);
  return n;
}
const NUCLEI = [];
let dockEl = null, starfield = null, tickerEl = null, spokenWords = [];
let drawerEl = null, drawerOpen = false, drawerBtnEl = null;
let dictatedEl = null, hintEl = null, ccBodyEl = null, tPanelEl = null;
let dictated = [], ccLines = [];

function buildDrawer() {
  drawerEl = el("div", "drawer" + (drawerOpen ? "" : " closed"));
  // left: transcript
  tPanelEl = el("div", "tpanel"); tPanelEl.dataset.live = "false";
  const th = el("div", "th");
  th.append(el("span", "micd"), el("span", "lbl", "TRANSCRIPT"));
  const rs = el("span", "rs", "IDLE"); th.append(rs);
  const tb = el("div", "tb");
  dictatedEl = el("div", "dictated", "");
  hintEl = el("div", "hint", "Nothing captured yet…");
  tb.append(dictatedEl, hintEl);
  const tf = el("div", "tf");
  ["run the tests", "undo that", "open the board"].forEach((c) => tf.append(el("span", "ex", `"${c}"`)));
  tPanelEl.append(th, tb, tf);
  tPanelEl._rs = rs;
  // right: claude code
  const cc = el("div", "tpanel cc");
  const cth = el("div", "th");
  cth.append(el("span", "path", "~/Desktop/Code/brain"), el("span", "model", "sonnet"));
  ccBodyEl = el("div", "tb");
  cc.append(cth, ccBodyEl);
  drawerEl.append(tPanelEl, cc);
  return drawerEl;
}
function toggleDrawer() {
  drawerOpen = !drawerOpen;
  if (drawerEl) drawerEl.classList.toggle("closed", !drawerOpen);
  if (drawerBtnEl) drawerBtnEl.textContent = drawerOpen ? "HIDE ▾" : "TRANSCRIPT ▴";
}
function renderTranscript() {
  if (dictatedEl) dictatedEl.textContent = dictated.join(" ");
  if (hintEl) {
    hintEl.textContent = voiceState === "listening"
      ? "Listening…" : dictated.length ? `Sent · ${dictated.length} words` : "Nothing captured yet…";
  }
  if (tPanelEl) { tPanelEl.dataset.live = String(voiceState === "listening"); tPanelEl._rs.textContent = voiceState === "listening" ? "RECORDING" : "IDLE"; }
  if (ccBodyEl) {
    ccBodyEl.innerHTML = "";
    if (!ccLines.length) { ccBodyEl.append(el("div", "l-idle", "idle — waiting for Claude Code output")); }
    else ccLines.slice(-40).forEach((l) => ccBodyEl.append(el("div", "l-prose", l)));
    ccBodyEl.scrollTop = ccBodyEl.scrollHeight;
  }
}
function buildDock() {
  dockEl = el("div", "dock");
  const mic = nucleus("mic");
  mic.onclick = () => { if (voiceMode === "daemon") sendCmd("record_toggle"); };
  mic.title = "in Daemon mode: click to toggle recording, or hold Space on this view";
  starfield = el("div", "starfield");
  starfield.append(el("div", "axis"));
  for (let i = 0; i < 30; i++) {
    const d = el("i", "sdot"); d.style.left = `${(i / 29) * 100}%`; d.style.top = "50%"; d.style.width = "2px"; d.style.height = "2px"; d.style.opacity = "0.3";
    if (i % 5 === 0) d.style.background = "#D8CCFF";
    starfield.append(d);
  }
  tickerEl = el("div", "ticker", "hold Space (on Command) to talk");
  starfield.append(tickerEl);
  const rmeta = el("div", "rmeta");
  rmeta.append(el("div", "w", "LOCAL DAEMON · READY"), el("div", "h", "click or hold Space · Wispr Flow for typing"));
  const vtoggle = el("div", "vtoggle");
  [["wispr", "WISPR"], ["daemon", "DAEMON"]].forEach(([m, label]) => {
    const b = el("button", voiceMode === m ? "on" : "", label);
    b.dataset.mode = m; b.onclick = () => setVoiceMode(m);
    vtoggle.append(b);
  });
  const drawerBtn = el("button", "drawer-btn", drawerOpen ? "HIDE ▾" : "TRANSCRIPT ▴");
  drawerBtnEl = drawerBtn;
  drawerBtn.onclick = toggleDrawer;
  dockEl.append(mic, starfield, rmeta, daemonSwitch(), vtoggle, drawerBtn);
  dockEl._meta = rmeta;
  return dockEl;
}
// On/off for the voice daemon process itself — declared as brain's "voice" service, so it
// runs through the same runner as app servers. Off means no global hotkey is listening.
const DAEMON = { project: "brain", service: "voice" };
function daemonSwitch() {
  const wrap = el("div", "dsw");
  const sw = el("button", "sw"); sw.type = "button"; sw.setAttribute("role", "switch");
  sw.append(el("span", "sw-k"));
  wrap.append(sw, el("span", "dsw-l", "DAEMON"));
  let svc = null;
  const paint = (busy) => {
    const on = !!svc && LIVE.includes(svc.state);
    sw.className = "sw" + (on ? " on" : "") + (busy ? " busy" : "");
    sw.setAttribute("aria-checked", String(on));
    sw.setAttribute("aria-label", `Voice daemon ${on ? "on" : "off"}`);
    sw.disabled = busy || !svc || svc.state === "conflict";
    sw.title = !svc ? "Voice daemon isn't declared" : busy ? "Working…"
      : svc.state === "conflict" ? `Port ${svc.port} is held by another app`
      : on ? "Daemon on — click to stop it so Wispr goes straight to your focused window" : "Daemon off — click to start push-to-talk";
  };
  const refresh = async () => {
    try { svc = (await api(`/api/devdash/${enc(DAEMON.project)}/runner`)).services.find((s) => s.name === DAEMON.service) || null; }
    catch { svc = null; }
    paint(false);
  };
  sw.onclick = async () => {
    const on = LIVE.includes(svc.state), ext = svc.state === "external";
    if (ext && !confirm("The voice daemon was started in a terminal. Stop it?")) return;
    paint(true);
    try {
      await api(`/api/devdash/${enc(DAEMON.project)}/services/${DAEMON.service}/${on ? "stop" : "start"}`,
        { method: "POST", body: JSON.stringify({ external: ext }) });
      setVoiceMode(on ? "wispr" : "daemon");
    } catch (e) { alert(e.message); }
    await refresh();
  };
  paint(true); refresh();
  return wrap;
}
function wireDock() { setVoiceMode(voiceMode); setDockLive(voiceMode === "daemon" && voiceState === "listening"); }
function setDockLive(live) {
  NUCLEI.forEach((n) => (n.dataset.live = String(live)));
  if (!starfield) return;
  const dots = starfield.querySelectorAll(".sdot");
  dots.forEach((d, i) => {
    if (live) {
      const lvl = levels[i % levels.length] || 0.2;
      d.style.top = `${50 - (lvl - 0.5) * 78}%`;
      d.style.height = `${2.5 + lvl * 4.5}px`; d.style.width = d.style.height;
      d.style.opacity = `${0.45 + lvl * 0.55}`; d.style.filter = `blur(${3 + lvl * 7}px)`;
    } else {
      d.style.top = "50%"; d.style.height = "2px"; d.style.width = "2px"; d.style.opacity = "0.3"; d.style.filter = "none";
    }
  });
}

// ── voice websocket (state + rail dot + nucleus + ticker) ────────────────────
let voiceState = "idle";
let levels = Array(30).fill(0.2);
let voiceMode = "wispr";  // "wispr" | "daemon" — which voice source the dashboard drives
try { voiceMode = localStorage.getItem("voiceMode") || "wispr"; } catch {}

function setVoiceMode(mode) {
  voiceMode = mode;
  try { localStorage.setItem("voiceMode", mode); } catch {}
  if (dockEl) dockEl.querySelectorAll(".vtoggle button").forEach((b) => b.classList.toggle("on", b.dataset.mode === mode));
  const mic = dockEl && dockEl.querySelector(".nucleus.mic");
  if (mic) mic.style.cursor = mode === "daemon" ? "pointer" : "default";
  if (tickerEl) tickerEl.textContent = mode === "wispr"
    ? "Wispr Flow — hold Fn to dictate into the focused app"
    : "click the orb or hold Space (on Command) to talk to the local daemon";
  setVoice(voiceState);
}

function setVoice(state) {
  voiceState = state;
  const dot = $("#voice-dot"), lbl = $("#voice-lbl");
  const connected = state !== "offline";
  const wispr = voiceMode === "wispr";
  dot.style.background = wispr ? "var(--green)" : (connected ? "var(--green)" : "var(--faint)");
  lbl.textContent = wispr ? "Wispr Flow · dictation" : (connected ? `local daemon · ${state}` : "local daemon · off");
  NUCLEI.forEach((n) => (n.dataset.live = String(!wispr && state === "listening")));
  if (wispr || state !== "listening") { levels = levels.map(() => 0.2); setDockLive(false); }
  if (dockEl && dockEl._meta) {
    const w = dockEl._meta.querySelector(".w"), h = dockEl._meta.querySelector(".h");
    if (wispr) { w.textContent = "WISPR FLOW · DICTATION"; h.textContent = "hold Fn to dictate"; }
    else { w.textContent = connected ? `LOCAL DAEMON · ${state === "listening" ? "LISTENING" : "READY"}` : "LOCAL DAEMON · OFF"; h.textContent = "click or hold Space"; }
  }
  renderTranscript();
}
async function resolveWs() {
  try {
    const r = await fetch("/api/config", { cache: "no-store" });
    if (r.ok) { const c = await r.json(); return `ws://${location.host}/ws?token=${encodeURIComponent(c.token)}`; }
  } catch (_) {}
  return "ws://127.0.0.1:8765";
}
let voiceWs = null;
function sendCmd(action) {
  try { if (voiceWs && voiceWs.readyState === 1) voiceWs.send(JSON.stringify({ type: "cmd", action })); } catch {}
}
async function connect() {
  const ws = new WebSocket(await resolveWs());
  voiceWs = ws;
  ws.onopen = () => setVoice("ready");
  ws.onmessage = (m) => { try { onEvt(JSON.parse(m.data)); } catch {} };
  ws.onclose = () => { voiceWs = null; setVoice("offline"); setTimeout(connect, 1500); };
  ws.onerror = () => ws.close();
}
function onEvt(evt) {
  switch (evt.type) {
    case "hello": setVoice("ready"); break;
    case "state": setVoice(evt.value); break;
    case "level":
      levels.shift(); levels.push(Math.max(0, Math.min(1, Number(evt.value) || 0)));
      if (voiceMode === "daemon" && voiceState === "listening") setDockLive(true);
      break;
    case "transcript":
      if (evt.text) {
        if (evt.role === "assistant") ccLines.push(evt.text);
        else {
          dictated.push(evt.text);
          spokenWords = evt.text.split(/\s+/).slice(-9);
          if (tickerEl) tickerEl.textContent = spokenWords.join(" ");
        }
        renderTranscript();
      }
      break;
    default: break;
  }
}

// ── init ─────────────────────────────────────────────────────────────────────
async function refreshCounts() {
  try {
    const [projects, tasks, arts, live] = await Promise.all([api("/api/projects"), api("/api/tasks"),
      api("/api/artifacts").catch(() => ({ items: [] })), api("/api/apps").catch(() => [])]);
    if (projects.map((p) => p.name).join() !== APPS.map((a) => a.name).join()) { APPS = projects; buildNav(); }
    setNavMeta({ projects: projects.length, board: tasks.length, artifacts: (arts.items || []).length });
    // live indicator per app: green while any of its servers is up, spinning while a script runs
    for (const a of live) {
      const b = document.querySelector(`.nav .item[data-view="project"][data-arg="${CSS.escape(a.name)}"]`);
      if (!b) continue;
      b.querySelector(".live")?.remove();
      if (!a.servers_up && !a.scripts_running) continue;
      const m = el("span", "live" + (a.scripts_running ? " busy" : ""));
      m.title = [a.servers_up && `${a.servers_up} of ${a.servers_total} servers running`, a.scripts_running && `${a.scripts_running} script running`].filter(Boolean).join(" · ");
      b.append(m);
    }
    $("#ws-name").textContent = "brain workspace";
  } catch {}
}
$("#talk-btn").onclick = () => go("command");
let spaceHeld = false;
document.addEventListener("keydown", (e) => {
  if (e.code === "Space" && voiceMode === "daemon" && current === "command" && !/input|textarea/i.test(document.activeElement.tagName)) {
    e.preventDefault();
    if (!e.repeat && !spaceHeld) { spaceHeld = true; sendCmd("record_start"); }
  }
});
document.addEventListener("keyup", (e) => {
  if (e.code === "Space" && spaceHeld) { spaceHeld = false; sendCmd("record_stop"); }
});
if (STRIP_ROUTE) {
  // standalone control strip (popup fallback when Document PiP isn't available)
  document.body.innerHTML = "";
  document.body.className = "strip-body";
  const shell = el("div", "strip"), root = el("div");
  shell.append(root);
  document.body.append(shell);
  mountApp(root, decodeURIComponent(location.hash.slice("#/strip/".length)), true);
} else {
  buildNav();
  route();
  window.addEventListener("hashchange", route);
  connect();
  refreshCounts();
  setInterval(refreshCounts, 8000);
}
})();
