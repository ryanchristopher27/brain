# MCPs

MCP (Model Context Protocol) server configurations for Claude Code and Cursor. Each MCP is one JSON file. No secrets are stored here — all sensitive values use environment variable references.

---

## Structure

```
mcps/
├── personal/     # Auth-required MCPs — your accounts, your tokens
│   └── .gitignore
├── shared/       # No-auth MCPs — usable by anyone, safe to share
└── _template/    # Copy these to create a new MCP
    ├── personal.json
    └── shared.json
```

---

## Security Rules

- **Never store API keys, tokens, or credentials** in any file in this directory
- Use environment variable references instead: `"${MY_API_KEY}"`
- Set actual values in your shell profile (`.bashrc`, `.zshrc`) or system env, not here
- `personal/` has an extra `.gitignore` as a safety net — but the no-secrets rule applies everywhere

---

## Adding a New MCP

### 1. Choose the right category
- **`personal/`** — requires your credentials (Gmail, Notion, Calendar, Drive, etc.)
- **`shared/`** — works without auth or uses only public APIs (filesystem, search, etc.)

### 2. Copy the template
```sh
cp mcps/_template/personal.json mcps/personal/<name>.json
# or
cp mcps/_template/shared.json mcps/shared/<name>.json
```

### 3. Fill in the config
Edit the file — replace placeholders with real values (except secrets — use env vars).

### 4. Set env vars
Add the required env vars to your shell profile:
```sh
export MY_SERVICE_API_KEY="your-actual-key-here"
```

### 5. Re-run install
```sh
bash install/install.sh
```
The install script merges all MCP files from both `personal/` and `shared/` into the global tool configs.

---

## How Install Wires MCPs

The install script merges MCP configs into:
- **Claude Code:** `~/.claude/settings.json` under `mcpServers`
- **Cursor:** `~/.cursor/mcp.json` under `mcpServers`

Both tools use the same `mcpServers` format, so one config file works for both.

---

## Existing MCPs

### Personal
| Name | Service | Status |
|------|---------|--------|
| *(none yet)* | — | — |

### Shared
| Name | Purpose | Status |
|------|---------|--------|
| *(none yet)* | — | — |
