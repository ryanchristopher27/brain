// Visualizer client — subscribes to the voice core's local event stream and reflects it.
// Read-only: it renders state, it never drives the agent.
// Scaffold: connects + maps events to the DOM. Orb animation polish → milestone C2.

const WS_URL = "ws://127.0.0.1:8765";

const el = {
  orb: document.getElementById("orb"),
  state: document.getElementById("state"),
  persona: document.getElementById("persona"),
  transcript: document.getElementById("transcript"),
};

function render(evt) {
  switch (evt.type) {
    case "hello":
      el.state.textContent = "ready";
      el.orb.dataset.state = "idle";
      break;
    case "state": // {type:"state", value:"listening|thinking|speaking|idle"}
      el.state.textContent = evt.value;
      el.orb.dataset.state = evt.value;
      break;
    case "persona": // {type:"persona", name:"scout"}
      el.persona.textContent = evt.name ? `persona: ${evt.name}` : "";
      break;
    case "transcript": // {type:"transcript", text:"...", final:bool}
      el.transcript.textContent = evt.text || "";
      break;
    default:
      // B4 will define the full event vocabulary.
      break;
  }
}

function connect() {
  const ws = new WebSocket(WS_URL);
  ws.onopen = () => (el.state.textContent = "connected");
  ws.onmessage = (m) => {
    try { render(JSON.parse(m.data)); } catch { /* ignore malformed */ }
  };
  ws.onclose = () => {
    el.state.textContent = "disconnected — retrying…";
    el.orb.dataset.state = "idle";
    setTimeout(connect, 1500);
  };
  ws.onerror = () => ws.close();
}

connect();
