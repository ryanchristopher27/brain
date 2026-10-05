/* Dev dashboard — per-project "how is the app doing" view. Standalone page (not part of
   the hub.js SPA router); same auth pattern as hub.js (same-origin token bootstrap). */
(() => {
"use strict";

let TOKEN = null;
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
const $ = (s, r = document) => r.querySelector(s);
function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}
function qs(name) { return new URLSearchParams(location.search).get(name); }

function line(label, value) {
  const d = el("div", "dd-line");
  d.append(el("span", null, label), el("span", null, value ?? "—"));
  return d;
}

// ── cards ────────────────────────────────────────────────────────────────
function notConfiguredCard(title, status) {
  const c = el("div", "dd-card");
  c.append(el("h3", null, title));
  c.append(el("div", "dd-na", status.reason || "not configured"));
  if (status.setup) {
    const p = el("div", "dd-setup");
    // status.setup is a plain string with a bare URL in it — linkify it.
    const m = status.setup.match(/(https?:\/\/\S+)/);
    if (m) {
      const before = status.setup.slice(0, m.index);
      const after = status.setup.slice(m.index + m[0].length);
      p.append(document.createTextNode(before));
      const a = el("a", null, m[0]); a.href = m[0]; a.target = "_blank"; a.rel = "noopener";
      p.append(a, document.createTextNode(after));
    } else {
      p.textContent = status.setup;
    }
    c.append(p);
  }
  return c;
}

function hostingCard(vercel) {
  if (!vercel.configured) return notConfiguredCard("Hosting · Vercel", vercel);
  const c = el("div", "dd-card");
  c.append(el("h3", null, "Hosting · Vercel"));
  if (!vercel.ok) { c.append(el("div", "dd-na", vercel.error || "error fetching deployments")); return c; }
  const d = vercel.deployment;
  if (!d) { c.append(el("div", "dd-na", "no production deployments found")); return c; }
  c.append(line("State", d.state));
  c.append(line("Commit", d.commit));
  c.append(line("Deployed", d.created ? new Date(d.created).toLocaleString() : "—"));
  c.append(line("URL", d.url));
  return c;
}

function trafficCard(vercel) {
  const c = el("div", "dd-card");
  c.append(el("h3", null, "Traffic"));
  c.append(el("div", "dd-na",
    vercel.configured
      ? "Vercel Web Analytics isn't wired up yet — the free REST API doesn't expose visitor counts; add a paid Analytics API token to light this up."
      : "not configured — set VERCEL_TOKEN to enable the Hosting card first"));
  return c;
}

function databaseCard(supabase) {
  if (!supabase.configured) return notConfiguredCard("Database · Supabase", supabase);
  const c = el("div", "dd-card");
  c.append(el("h3", null, "Database · Supabase"));
  if (!supabase.ok) { c.append(el("div", "dd-na", supabase.error || "error")); return c; }
  c.append(line("Status", supabase.status));
  c.append(line("Region", supabase.region));
  c.append(line("Name", supabase.name));
  return c;
}

function repoCard(git) {
  const c = el("div", "dd-card");
  c.append(el("h3", null, "Repo"));
  if (!git.configured) { c.append(el("div", "dd-na", git.reason)); return c; }
  c.append(line("Branch", git.branch));
  c.append(line("Uncommitted", String(git.uncommitted)));
  c.append(line("Ahead / behind", git.has_upstream ? `${git.ahead} / ${git.behind}` : "no upstream"));
  if (git.commits && git.commits.length) {
    const ul = el("ul", "dd-list");
    git.commits.slice(0, 5).forEach((l) => ul.append(el("li", null, l)));
    c.append(ul);
  }
  return c;
}

function trackerCard(tr) {
  const inReview = tr.in_review || [];
  const c = el("div", "dd-card" + (inReview.length ? " highlight" : ""));
  c.append(el("h3", null, "Tracker"));
  if (!tr.configured) { c.append(el("div", "dd-na", "no tracker")); return c; }
  const order = ["backlog", "ready", "doing", "review", "done"];
  order.forEach((s) => c.append(line(s, String(tr.by_status[s] ?? 0))));
  if (inReview.length) {
    const ul = el("ul", "dd-list");
    inReview.forEach((t) => ul.append(el("li", null, `in review · ${t.title}`)));
    c.append(ul);
  }
  return c;
}

// ── resources table ─────────────────────────────────────────────────────
function resourcesSection(resDoc) {
  const wrap = el("div");
  wrap.append(el("div", "dd-section-title", `Resources (${resDoc.source === "none" ? "none declared" : resDoc.source})`));
  if (resDoc.problems && resDoc.problems.length) {
    const p = el("div", "dd-na", "schema problems: " + resDoc.problems.join("; "));
    wrap.append(p);
  }
  if (!resDoc.resources.length) {
    wrap.append(el("p", "empty", "No resources declared yet. Run `python -m dashboard.resources_cli seed --path .` in the project to propose a list."));
    return wrap;
  }
  const byCat = {};
  for (const r of resDoc.resources) (byCat[r.category] ||= []).push(r);
  for (const cat of Object.keys(byCat).sort()) {
    const g = el("div", "dd-res-group");
    g.append(el("h4", null, cat.replace(/-/g, " ")));
    const table = el("table", "dd-res");
    const thead = el("thead");
    const htr = el("tr");
    ["Name", "Purpose", "Plan / limits", "Env vars", "Links"].forEach((h) => htr.append(el("th", null, h)));
    thead.append(htr);
    table.append(thead);
    const tbody = el("tbody");
    byCat[cat].forEach((r) => {
      const tr = el("tr");
      const nameTd = el("td", null, r.name);
      nameTd.dataset.label = "Name";
      if (!r.verified) nameTd.append(el("span", "dd-unverified", "UNVERIFIED"));
      tr.append(nameTd);
      const purposeTd = el("td", null, r.purpose); purposeTd.dataset.label = "Purpose"; tr.append(purposeTd);
      const planTd = el("td", null, r.plan || "—"); planTd.dataset.label = "Plan / limits"; tr.append(planTd);
      const envTd = el("td", "dd-env", (r.env_vars || []).join(", ") || "—"); envTd.dataset.label = "Env vars"; tr.append(envTd);
      const linksTd = el("td"); linksTd.dataset.label = "Links";
      const urls = r.urls || {};
      Object.entries(urls).forEach(([k, v], i) => {
        if (i > 0) linksTd.append(document.createTextNode(" · "));
        const a = el("a", null, k); a.href = v; a.target = "_blank"; a.rel = "noopener";
        linksTd.append(a);
      });
      if (!Object.keys(urls).length) linksTd.textContent = "—";
      tr.append(linksTd);
      tbody.append(tr);
    });
    table.append(tbody);
    g.append(table);
    wrap.append(g);
  }
  return wrap;
}

// ── test accounts ────────────────────────────────────────────────────────
function copyBtn(text, label = "copy") {
  const b = el("button", "dd-copy", label);
  b.type = "button";
  b.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(text); b.textContent = "copied"; setTimeout(() => (b.textContent = label), 1200); } catch { b.textContent = "copy failed"; }
  });
  return b;
}

function testUsersSection(name, tu) {
  const wrap = el("div", "dd-tu");
  wrap.append(el("div", "dd-section-title", "Test accounts"));
  if (!tu || !tu.declared) {
    wrap.append(el("p", "empty", "None declared. Add .brain/test-users.json to the project to list test accounts here."));
    return wrap;
  }
  if (tu.summary) wrap.append(el("p", "dd-tu-summary", tu.summary));
  const c = tu.credentials || {};
  const state = el("div", "dd-tu-state");
  state.append(el("span", "g" + (c.exists ? " ok" : "")));
  state.append(document.createTextNode(c.exists
    ? `Seeded ${c.seeded_at ? new Date(c.seeded_at).toLocaleString() : ""} · passwords in ${c.file}`
    : "Not seeded on this machine yet — run the seed command below."));
  wrap.append(state);

  const table = el("table", "dd-res");
  const htr = el("tr");
  ["User", "Email", "Has", "Friends", "Password"].forEach((h) => htr.append(el("th", null, h)));
  const thead = el("thead"); thead.append(htr); table.append(thead);
  const tbody = el("tbody");
  const pwCells = new Map();
  for (const u of tu.users) {
    const tr = el("tr");
    const cells = [["User", "@" + u.username], ["Email", u.email], ["Has", u.has], ["Friends", u.friends]];
    cells.forEach(([label, v], i) => {
      const td = el("td", i < 2 ? "dd-env" : null, v || "—"); td.dataset.label = label;
      if (label === "Email" && v) td.append(copyBtn(v));
      tr.append(td);
    });
    const pw = el("td", "dd-env", c.exists ? "••••••" : "—"); pw.dataset.label = "Password";
    pwCells.set(u.email, pw);
    tr.append(pw);
    tbody.append(tr);
  }
  table.append(tbody);
  wrap.append(table);

  if (c.exists) {
    const reveal = el("button", "dd-copy dd-reveal", "Reveal passwords");
    reveal.type = "button";
    reveal.addEventListener("click", async () => {
      try {
        const { users } = await api(`/api/devdash/${encodeURIComponent(name)}/test-credentials`);
        for (const { email, password } of users) {
          const td = pwCells.get(email);
          if (!td) continue;
          td.textContent = password;
          td.append(copyBtn(password));
        }
        reveal.remove();
      } catch (e) { reveal.textContent = "couldn’t load: " + e.message; }
    });
    wrap.append(reveal);
  }

  const cmds = Object.entries(tu.commands || {});
  if (cmds.length) {
    const box = el("div", "dd-tu-cmds");
    for (const [k, v] of cmds) {
      const row = el("div", "dd-tu-cmd");
      row.append(el("span", "dd-tu-k", k), el("code", null, v), copyBtn(v));
      box.append(row);
    }
    wrap.append(box);
  }
  return wrap;
}

// ── header ───────────────────────────────────────────────────────────────
function headerBlock(name, project, uptime) {
  const h = el("div", "dd-header");
  h.append(el("h1", null, name));
  if (project.status) h.append(el("span", "pill " + project.status, project.status.toUpperCase()));
  const prodUrl = (project.resources.resources.find((r) => r.status_check?.config?.prod_url) || {}).status_check?.config?.prod_url;
  if (prodUrl) {
    const urlDiv = el("div", "dd-url");
    const a = el("a", null, prodUrl); a.href = prodUrl; a.target = "_blank"; a.rel = "noopener";
    urlDiv.append(a);
    h.append(urlDiv);
  }
  const up = el("div", "dd-uptime" + (uptime.configured ? (uptime.ok ? " ok" : " bad") : ""));
  up.append(el("span", "g"));
  up.append(document.createTextNode(
    uptime.configured ? `${uptime.ok ? "up" : "down"} · ${uptime.status_code ?? ""} · ${uptime.elapsed_ms}ms` : "uptime: not configured"));
  h.append(up);
  return h;
}

// ── page ─────────────────────────────────────────────────────────────────
async function renderProject(name) {
  const pane = $("#dd-pane");
  pane.innerHTML = "";
  pane.append(el("p", "empty", "loading…"));
  let d;
  try {
    d = await api(`/api/devdash/${encodeURIComponent(name)}`);
  } catch (e) {
    pane.innerHTML = "";
    pane.append(el("p", "empty", `failed to load ${name}: ${e.message}`));
    return;
  }
  pane.innerHTML = "";
  pane.append(headerBlock(name, { resources: d.resources, status: "" }, d.uptime));

  const grid = el("div", "dd-grid");
  grid.append(hostingCard(d.vercel));
  grid.append(trafficCard(d.vercel));
  grid.append(databaseCard(d.supabase));
  grid.append(repoCard(d.git));
  grid.append(trackerCard(d.tracker));
  pane.append(grid);

  pane.append(testUsersSection(name, d.test_users));
  pane.append(resourcesSection(d.resources));
}

async function init() {
  const select = $("#dd-project-select");
  let projects = [];
  try {
    projects = await api("/api/projects");
  } catch (e) {
    $("#dd-pane").innerHTML = "";
    $("#dd-pane").append(el("p", "empty", "failed to load project list — is the dashboard server running?"));
    return;
  }
  select.innerHTML = "";
  projects.forEach((p) => {
    const o = document.createElement("option");
    o.value = p.name; o.textContent = p.name;
    select.append(o);
  });
  const requested = qs("project");
  const initial = (requested && projects.some((p) => p.name === requested)) ? requested
    : (projects.find((p) => p.name === "trip-planner") || projects[0] || {}).name;
  if (!initial) {
    $("#dd-pane").innerHTML = "";
    $("#dd-pane").append(el("p", "empty", "no projects registered"));
    return;
  }
  select.value = initial;
  select.onchange = () => {
    const url = new URL(location.href);
    url.searchParams.set("project", select.value);
    history.replaceState(null, "", url);
    renderProject(select.value);
  };
  if (requested !== initial) {
    const url = new URL(location.href);
    url.searchParams.set("project", initial);
    history.replaceState(null, "", url);
  }
  renderProject(initial);
}

init();
})();
