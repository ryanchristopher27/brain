// Visualizer client — subscribes to the voice core's local event stream and reflects it.
// Read-only: it renders state, it never drives the agent.
// Event vocabulary (emitted by voice/daemon.py):
//   {type:"hello"}
//   {type:"state",   value:"idle|listening|thinking|speaking"}
//   {type:"persona", name:"scout"}
//   {type:"transcript", text:"…", role:"user|assistant", final:true}
//   {type:"level",   value:0..1}   // live mic loudness while listening

const VOICE_FALLBACK = "ws://127.0.0.1:8765"; // standalone voice, no dashboard
const MAX_LINES = 12;

const el = {
  orb: document.getElementById("orb"),
  state: document.getElementById("state"),
  persona: document.getElementById("persona"),
  log: document.getElementById("log"),
  conn: document.getElementById("conn"),
};

let currentPersona = "";

function setState(value) {
  el.state.textContent = value;
  el.orb.dataset.state = value;
  if (value !== "listening") el.orb.style.setProperty("--level", "0");
}

function setLevel(v) {
  const level = Math.max(0, Math.min(1, Number(v) || 0));
  el.orb.style.setProperty("--level", String(level));
}

function addLine(role, text) {
  if (!text) return;
  const who = role === "assistant" ? (currentPersona || "agent") : "you";
  const line = document.createElement("p");
  line.className = `line ${role === "assistant" ? "bot" : "you"}`;
  line.innerHTML = `<span class="who">${who}</span><span class="msg"></span>`;
  line.querySelector(".msg").textContent = text; // textContent = XSS-safe
  el.log.appendChild(line);
  while (el.log.childElementCount > MAX_LINES) el.log.removeChild(el.log.firstChild);
  el.log.scrollTop = el.log.scrollHeight;
}

function render(evt) {
  switch (evt.type) {
    case "hello":
      setState("ready");
      break;
    case "state":
      setState(evt.value);
      break;
    case "persona":
      currentPersona = evt.name || "";
      el.persona.textContent = currentPersona ? `persona · ${currentPersona}` : "";
      document.body.dataset.persona = currentPersona;
      break;
    case "transcript":
      addLine(evt.role, evt.text);
      break;
    case "level":
      setLevel(evt.value);
      break;
    default:
      // Forward run lifecycle events to the runs panel (panels.js listens).
      if (typeof evt.type === "string" && evt.type.startsWith("run")) {
        window.dispatchEvent(new CustomEvent("brain-run", { detail: evt }));
      }
      break;
  }
}

function setConn(ok, label) {
  el.conn.dataset.ok = String(ok);
  el.conn.textContent = label;
}

// If served by the dashboard, use its authenticated hub; else fall back to voice directly.
async function resolveWsUrl() {
  try {
    const r = await fetch("/api/config", { cache: "no-store" });
    if (r.ok) {
      const c = await r.json();
      return `ws://${location.host}/ws?token=${encodeURIComponent(c.token)}`;
    }
  } catch (_) { /* not served by the dashboard */ }
  return VOICE_FALLBACK;
}

async function connect() {
  const url = await resolveWsUrl();
  const ws = new WebSocket(url);
  ws.onopen = () => setConn(true, "online");
  ws.onmessage = (m) => {
    try { render(JSON.parse(m.data)); } catch { /* ignore malformed */ }
  };
  ws.onclose = () => {
    setConn(false, "reconnecting…");
    setState("idle");
    setTimeout(connect, 1500);
  };
  ws.onerror = () => ws.close();
}

connect();
