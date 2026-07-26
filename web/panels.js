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

// ── work pipeline (Kanban) ───────────────────────────────────────────────────
function renderPipeline(p) {
  fill($("pipeline"), p.columns.map((col) => {
    const column = el("div", "col");
    column.append(el("div", "col-head", col));
    const cards = p.projects.filter((pr) => pr.phase === col);
    cards.forEach((pr) => {
      const c = el("div", "proj");
      c.dataset.persona = ""; // reserved for future agent linkage
      c.append(el("span", "proj-name", pr.name));
      const badges = el("div", "badges");
      p.columns.forEach((ph) => {
        const b = el("span", "badge" + (pr.detected.includes(ph) ? " on" : ""));
        b.title = ph;
        badges.append(b);
      });
      c.append(badges);
      if (pr.iterating) c.append(el("span", "tag", "iterating"));
      if (pr.override) c.append(el("span", "tag", "pinned"));
      column.append(c);
    });
    return column;
  }));
}

// ── agent runs (D5): controls · approvals · live activity ────────────────────
const personaRO = {};
let controlsReady = false;

async function apiPost(path, body) {
  const t = await token();
  const r = await fetch(path, {
    method: "POST",
    headers: { Authorization: `Bearer ${t}`, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return { ok: r.ok, status: r.status, data: await r.json().catch(() => ({})) };
}

function initControls(agents) {
  if (controlsReady) return;
  const sel = $("run-persona");
  agents.forEach((a) => {
    personaRO[a.name] = a.read_only;
    const o = el("option", null, a.read_only ? a.name : `${a.name} · writes`);
    o.value = a.name;
    sel.append(o);
  });
  $("run-go").addEventListener("click", onRun);
  controlsReady = true;
}

async function onRun() {
  const persona = $("run-persona").value;
  const task = $("run-task").value.trim();
  const dir = $("run-dir").value.trim();
  const msg = $("run-msg");
  if (!task) { msg.textContent = "enter a task"; return; }
  const writer = personaRO[persona] === false;
  const res = await apiPost(writer ? "/api/runs/propose" : "/api/runs/spawn",
    writer ? { persona, task, add_dir: dir } : { persona, task });
  if (res.ok) {
    msg.textContent = writer ? "proposed — awaiting approval" : "spawned";
    $("run-task").value = "";
    poll();
  } else {
    msg.textContent = res.data.error || `error ${res.status}`;
  }
}

async function act(path) { await apiPost(path); poll(); }

function renderRuns(d) {
  const t = d.totals || { runs: 0, cost_usd: 0 };
  $("runs-totals").textContent = `(${t.runs} runs · $${(t.cost_usd || 0).toFixed(2)})`;

  const q = (d.queued || []).map((item) => {
    const chip = el("div", "qitem");
    chip.append(el("span", "qtxt", `${item.persona}: ${item.task.slice(0, 46)}`));
    const x = el("button", "btn no", "remove");
    x.onclick = () => act(`/api/queue/${item.id}/remove`);
    chip.append(x);
    return chip;
  });
  $("queued").replaceChildren(...q);

  const pend = (d.pending || []).map((p) => {
    const card = el("div", "pend");
    const head = el("div", "row-head");
    head.append(el("span", "chip " + (p.writer ? "writer" : "posture"), p.writer ? "write" : "read"),
      el("span", "row-title", p.persona), el("span", "row-meta", p.add_dir || ""));
    const btns = el("div", "btns");
    const ok = el("button", "btn ok", "approve"); ok.onclick = () => act(`/api/runs/${p.run_id}/approve`);
    const no = el("button", "btn no", "deny"); no.onclick = () => act(`/api/runs/${p.run_id}/deny`);
    btns.append(ok, no);
    card.append(head, el("p", "row-sub", p.task), btns);
    return card;
  });
  $("pending").replaceChildren(...pend);

  const active = new Set(d.active || []);
  fill($("runs"), (d.runs || []).slice(0, 8).map((r) => {
    const row = el("div", "row");
    const head = el("div", "row-head");
    head.append(el("span", `dot ${r.status}`), el("span", "row-title", r.persona),
      el("span", "chip", r.source),
      el("span", "row-meta", r.cost_usd ? `$${r.cost_usd.toFixed(3)}` : ""));
    row.append(head, el("p", "row-sub", (r.task || "").slice(0, 90)));
    if (active.has(r.id)) {
      const stop = el("button", "btn no", "stop");
      stop.onclick = () => act(`/api/runs/${r.id}/stop`);
      row.append(stop);
    }
    return row;
  }));
}

const runPersona = {};
function addActivity(text) {
  const a = $("activity");
  const empty = a.querySelector(".empty");
  if (empty) a.replaceChildren();
  a.prepend(el("p", "act-line", text));
  while (a.childElementCount > 14) a.removeChild(a.lastChild);
}
window.addEventListener("brain-run", (e) => {
  const m = e.detail;
  if (m.type === "run_started") { runPersona[m.run_id] = m.persona; addActivity(`${m.persona} started`); poll(); }
  else if (m.type === "run_event") addActivity(`${runPersona[m.run_id] || "agent"} · ${m.name} ${JSON.stringify(m.input || {}).slice(0, 42)}`);
  else if (m.type === "run_finished") { addActivity(`finished · ${m.status}`); poll(); }
  else if (m.type === "run_pending" || m.type === "run_denied") poll();
});

// ── task board (T3) ──────────────────────────────────────────────────────────
const TASK_STATUSES = ["backlog", "ready", "doing", "review", "done"];
let taskFilter = "";
let selectedTask = null;
let taskCtrlReady = false;

function initTaskControls(projects) {
  if (taskCtrlReady) return;
  const filt = $("task-filter"), ntp = $("nt-project");
  projects.forEach((p) => {
    const o1 = el("option", null, `${p.name} (${p.tasks})`); o1.value = p.name; filt.append(o1);
    const o2 = el("option", null, p.name); o2.value = p.name; ntp.append(o2);
  });
  filt.addEventListener("change", () => { taskFilter = filt.value; poll(); });
  $("task-new-btn").addEventListener("click", () => {
    const f = $("task-new-form"); f.hidden = !f.hidden;
  });
  $("task-new-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = $("nt-title").value.trim();
    if (!title) { $("nt-msg").textContent = "title required"; return; }
    const r = await apiPost("/api/tasks", {
      project: $("nt-project").value, title, type: $("nt-type").value,
      brief: $("nt-brief").value.trim(), scoped_dir: $("nt-dir").value.trim() || ".",
    });
    if (r.ok) {
      $("nt-title").value = ""; $("nt-brief").value = ""; $("nt-msg").textContent = "";
      $("task-new-form").hidden = true; poll();
    } else $("nt-msg").textContent = r.data.error || `error ${r.status}`;
  });
  taskCtrlReady = true;
}

function renderTasks(tasks) {
  const shown = taskFilter ? tasks.filter((t) => t.project === taskFilter) : tasks;
  $("tasks-count").textContent = shown.length ? `(${shown.length})` : "";
  fill($("task-board"), TASK_STATUSES.map((st) => {
    const col = el("div", "col");
    const items = shown.filter((t) => t.status === st);
    col.append(el("div", "col-head", items.length ? `${st} · ${items.length}` : st));
    items.forEach((t) => {
      const c = el("div", "proj task-card");
      c.append(el("span", "proj-name", t.title));
      const meta = el("div", "task-meta");
      meta.append(el("span", "chip cat", t.type));
      if (t.assignee) meta.append(el("span", "chip", t.assignee));
      meta.append(el("span", "task-proj", t.project));
      c.append(meta);
      c.onclick = () => { selectedTask = { project: t.project, id: t.id }; renderDetail(t); };
      col.append(c);
    });
    return col;
  }));
  if (selectedTask) {
    const t = shown.find((x) => x.id === selectedTask.id && x.project === selectedTask.project);
    if (t) renderDetail(t); else { selectedTask = null; $("task-detail").hidden = true; }
  }
}

function renderDetail(t) {
  const d = $("task-detail"); d.hidden = false; d.replaceChildren();
  const head = el("div", "detail-head");
  head.append(el("span", "detail-title", t.title), el("span", "chip cat", t.type),
    el("span", "row-meta", `#${t.id} · ${t.project}`));
  const close = el("button", "btn", "close");
  close.onclick = () => { selectedTask = null; d.hidden = true; };
  head.append(close);
  d.append(head);
  if (t.brief) d.append(el("p", "detail-brief", t.brief));
  if (t.acceptance && t.acceptance.length) {
    d.append(el("div", "sub", "acceptance"));
    const ul = el("ul", "detail-accept");
    t.acceptance.forEach((a) => ul.append(el("li", null, a)));
    d.append(ul);
  }
  const controls = el("div", "detail-controls");
  const sel = el("select", "detail-status");
  TASK_STATUSES.forEach((s) => {
    const o = el("option", null, s); o.value = s; if (s === t.status) o.selected = true; sel.append(o);
  });
  const smsg = el("span", "run-msg");
  sel.onchange = async () => {
    const r = await apiPost(`/api/tasks/${t.project}/${t.id}/status`, { status: sel.value });
    if (!r.ok) { sel.value = t.status; smsg.textContent = r.data.error || "invalid transition"; }
    else poll();
  };
  controls.append(el("span", "sub", "status"), sel);
  if (t.assignee) {
    const wb = el("button", "btn ok", `work · ${t.assignee}`);
    wb.onclick = async () => {
      const r = await apiPost(`/api/tasks/${t.project}/${t.id}/work`, {});
      smsg.textContent = r.ok ? "dispatched" : (r.data.error || "error");
      if (r.ok) poll();
    };
    controls.append(wb);
  }
  controls.append(smsg);
  d.append(controls);
  const cbox = el("div", "detail-comment");
  const ci = el("input", "comment-input"); ci.type = "text"; ci.placeholder = "add a comment…";
  const cb = el("button", "btn", "add");
  cb.onclick = async () => {
    if (!ci.value.trim()) return;
    await apiPost(`/api/tasks/${t.project}/${t.id}/update`, { detail: ci.value.trim() });
    ci.value = ""; poll();
  };
  cbox.append(ci, cb); d.append(cbox);
  if (t.runs && t.runs.length) {
    d.append(el("div", "sub", "runs"));
    const rl = el("div", "chips"); t.runs.forEach((r) => rl.append(el("span", "chip tool", r)));
    d.append(rl);
  }
  d.append(el("div", "sub", "updates"));
  const log = el("div", "detail-updates");
  (t.updates || []).slice().reverse().forEach((u) => log.append(el("p", "act-line", u)));
  d.append(log);
}

async function poll() {
  if (!dashboardMode) return;
  try {
    const [agents, jobs, schedule, health, pipeline, runs, tasks, projects] = await Promise.all([
      api("/api/agents"), api("/api/jobs"), api("/api/schedule"),
      api("/api/health"), api("/api/pipeline"), api("/api/runs"),
      api("/api/tasks"), api("/api/projects"),
    ]);
    initControls(agents);
    initTaskControls(projects);
    renderAgents(agents);
    renderJobs(jobs);
    renderSchedule(schedule);
    renderHealth(health);
    renderPipeline(pipeline);
    renderRuns(runs);
    renderTasks(tasks);
  } catch (_) {
    dashboardMode = false; // standalone voice, no dashboard API
  }
}

poll();
setInterval(poll, POLL_MS);
})();
