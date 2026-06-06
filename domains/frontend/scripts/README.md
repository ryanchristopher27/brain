# Frontend Scripts

Bundled tooling for the frontend domain. Referenced by absolute brain-repo path from
`commands/design.md` — `install.sh` does **not** copy these into `~/.claude`, so they run from
here. Both toolchains are dependency-light and the commands degrade to markdown guidance when the
runtime is missing.

> **Status:** search scripts ported (M2 complete); detector pending (M3). See `docs/plan.md`.

## Contents

### Knowledge-base search (Python, stdlib only) — M2 ✅
From ui-ux-pro-max. No pip install required. Verified on Python 3.10:
`search.py --domain <d>`, `--stack <s>`, and `--design-system` all run from the brain path.
- `core.py` — BM25 engine + CSV config (reads `../data/`).
- `search.py` — CLI entry: `python3 search.py "<query>" --domain <d> [--stack <s>]`.
- `design_system.py` — design-system generation (`--design-system [--persist]`).

### Anti-pattern detector (Node) — M3 ✅
From impeccable. Self-contained — only `node:` builtins, no npm install. Verified on node v18:
- `detect.mjs` — CLI entry; loads the bundled `detector/` engine (`detectCli`).
- `detector/` — the full engine closure (cli, engines/{regex,static-html,browser,visual},
  registry, rules, shared, findings, profile, node). Deterministic rules; no LLM, no API key.
- Invoke as: `node domains/frontend/scripts/detect.mjs [--json] <files-or-dirs...>`.
  - `.html` → static HTML/CSS analysis; other files (`.css/.jsx/.tsx/…`) → regex matching.
  - URL mode (Puppeteer) and the visual contrast engine are present but unused by `audit`
    (they belong to the excluded live browser loop and need a browser at runtime).
