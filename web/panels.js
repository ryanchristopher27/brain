// Dashboard panels (D3) — read-only fetch + render over the secured /api.
// Polls every few seconds. If not served by the dashboard (standalone voice), the /api
// calls fail and the panels quietly stay idle.

// Wrapped in an IIFE so its top-level names (el, api, fill, …) can't collide with app.js
// in the shared global scope of classic scripts.
(() => {
const POLL_MS = 5000;
let TOKEN = null;
let dashboardMode = true;

async function token() {
  if (TOKEN) return TOKEN;
  const r = await fetch("/api/config", { cache: "no-store" });
  TOKEN = (await r.json()).token;
  return TOKEN;
}

async function api(path) {
  const t = await token();
  const r = await fetch(path, { headers: { Authorization: `Bearer ${t}` }, cache: "no-store" });
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
}

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
};
function fill(node, children) {
  node.replaceChildren(...(children.length ? children : [el("p", "empty", "none")]));
}

// ── agents ──────────────────────────────────────────────────────────────────
function renderAgents(list) {
  $("agents-count").textContent = list.length ? `(${list.length})` : "";
  fill($("agents"), list.map((a) => {
    const card = el("div", `card${a.read_only ? "" : " writer"}`);
    card.dataset.persona = a.name;
    const head = el("div", "card-head");
    head.append(el("span", "card-name", a.name), el("span", "chip posture", a.read_only ? "read-only" : "writes"));
    const cat = el("span", "chip cat", a.category);
    card.append(head, el("p", "card-desc", a.description));
    const tools = el("div", "chips");
    a.tools.forEach((t) => tools.append(el("span", "chip tool", t)));
    card.append(cat, tools);
    return card;
  }));
}

// ── jobs ────────────────────────────────────────────────────────────────────
function fmtTs(ts) {
  const m = /^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})$/.exec(ts || "");
  return m ? `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]}` : (ts || "");
}
function renderJobs(list) {
  fill($("jobs"), list.map((j) => {
    const row = el("div", "row job");
    const head = el("div", "row-head");
    head.append(
      el("span", `dot ${j.status}`),
      el("span", "row-title", j.label),
      el("span", "row-meta", fmtTs(j.timestamp)),
    );
    row.append(head, el("p", "row-sub", j.report_preview.split("\n")[0].slice(0, 120)));
    return row;
  }));
}

// ── schedule ────────────────────────────────────────────────────────────────
function renderSchedule(s) {
  const rows = [];
  (s.loaded || []).forEach((j) =>
    rows.push(rowLine("dot done", j.label, `pid ${j.pid}`)));
  (s.installable || []).forEach((t) =>
    rows.push(rowLine("dot idle", t.replace(/\.plist\.example$/, ""), "installable")));
  fill($("schedule"), rows);
}

// ── health ──────────────────────────────────────────────────────────────────
function renderHealth(h) {
  const rows = [rowLine(`dot ${h.voice_connected ? "done" : "idle"}`, "voice daemon",
    h.voice_connected ? "connected" : "offline")];
  (h.mcps || []).forEach((m) => {
    const ok = !m.needs_token || m.token_set;
    rows.push(rowLine(`dot ${ok ? "done" : "failed"}`, `mcp · ${m.name}`,
      !m.needs_token ? "no auth" : (m.token_set ? "token set" : "token missing")));
  });
  fill($("health"), rows);
}

function rowLine(dotCls, title, meta) {
  const row = el("div", "row");
  const head = el("div", "row-head");
  head.append(el("span", dotCls), el("span", "row-title", title), el("span", "row-meta", meta));
  row.append(head);
  return row;
}

async function poll() {
  if (!dashboardMode) return;
  try {
    const [agents, jobs, schedule, health] = await Promise.all([
      api("/api/agents"), api("/api/jobs"), api("/api/schedule"), api("/api/health"),
    ]);
    renderAgents(agents);
    renderJobs(jobs);
    renderSchedule(schedule);
    renderHealth(health);
  } catch (_) {
    dashboardMode = false; // standalone voice, no dashboard API
  }
}

poll();
setInterval(poll, POLL_MS);
})();
