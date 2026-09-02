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
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.status === 204 ? null : r.json();
}
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
  projects:   { label: "Projects",   sec: "WORKSPACE", title: "Projects", sub: "Everything you have going, across chat and Claude Code" },
  board:      { label: "Board",      sec: "WORKSPACE", title: "Board", sub: "Tasks across every project · drag to move, or say “move it to done”" },
  artifacts:  { label: "Artifacts",  sec: "WORKSPACE", title: "Artifacts" },
  command:    { label: "Command",    sec: "TOOLS", title: "Command", sub: "Orchestrator moving work through brainstorm, plan, build, review, ship · talk to it below" },
  connectors: { label: "Connectors", sec: "TOOLS", title: "Connectors", sub: "MCP servers and integrations available to every session" },
  usage:      { label: "Usage",      sec: "ACCOUNT", title: "Usage", sub: "Current billing period" },
};
let current = "overview";

function buildNav() {
  const nav = $("#nav"); nav.innerHTML = "";
  let sec = null;
  for (const [key, v] of Object.entries(VIEWS)) {
    if (v.sec !== sec) { sec = v.sec; nav.append(el("div", "sec", sec)); }
    const b = el("button", "item" + (key === current ? " on" : ""));
    b.append(el("span", "dot"), el("span", null, v.label));
    b.dataset.view = key;
    b.onclick = () => go(key);
    nav.append(b);
  }
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
async function go(key) {
  current = key;
  document.querySelectorAll(".nav .item").forEach((b) => b.classList.toggle("on", b.dataset.view === key));
  const v = VIEWS[key];
  $("#view-title").textContent = v.title;
  $("#view-sub").textContent = v.sub || "";
  const pane = $("#pane"); pane.innerHTML = "";
  pane.append(el("p", "empty", "loading…"));
  try { await RENDER[key](pane); } catch (e) { pane.innerHTML = ""; pane.append(el("p", "empty", "failed: " + e.message)); }
  pane.scrollTop = 0;
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
    const tr = el("tr");
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
RENDER.board = async (pane) => {
  const [tasks, projects] = await Promise.all([api("/api/tasks"), api("/api/projects")]);
  pane.innerHTML = "";
  const chips = el("div", "chips");
  const allc = el("span", "chip" + (boardFilter === "all" ? " on" : ""), "all projects");
  allc.onclick = () => { boardFilter = "all"; RENDER.board(pane); };
  chips.append(allc);
  projects.forEach((p) => {
    const ch = el("span", "chip" + (boardFilter === p.name ? " on" : ""));
    ch.append(pdot(p.name), el("span", null, p.name));
    ch.onclick = () => { boardFilter = p.name; RENDER.board(pane); };
    chips.append(ch);
  });
  const shown = boardFilter === "all" ? tasks : tasks.filter((t) => t.project === boardFilter);
  const blocked = shown.filter((t) => t.status === "review").length;
  const cnt = el("span", "note r mono", `${shown.length} TASKS · ${blocked} BLOCKED ON YOU`);
  chips.append(cnt);
  pane.append(chips);

  const COLS = [
    { key: "backlog", label: "BACKLOG", color: "#4A4258", statuses: ["backlog", "ready"] },
    { key: "doing", label: "IN PROGRESS", color: "var(--accent)", statuses: ["doing"] },
    { key: "review", label: "WAITING ON YOU", color: "#C4A05F", statuses: ["review"] },
    { key: "done", label: "DONE", color: "#6B9E72", statuses: ["done"] },
  ];
  const kb = el("div", "kanban");
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
  dockEl.append(mic, starfield, rmeta, vtoggle, drawerBtn);
  dockEl._meta = rmeta;
  return dockEl;
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
    const [projects, tasks, arts] = await Promise.all([api("/api/projects"), api("/api/tasks"), api("/api/artifacts").catch(() => ({ items: [] }))]);
    setNavMeta({ projects: projects.length, board: tasks.length, artifacts: (arts.items || []).length });
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
buildNav();
go("overview");
connect();
refreshCounts();
setInterval(refreshCounts, 8000);
})();
