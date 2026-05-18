# /review

You are entering **Review Mode** — a full-spectrum audit covering plan adherence, code quality, and security.

## First: Read Context

1. `docs/plan.md` — what was supposed to be built
2. `docs/brainstorm.md` — original intent
3. `docs/review.md` — prior findings (check if previously flagged issues were resolved)
4. `CLAUDE.md` — project conventions (don't flag intentional design choices)

## Determine Scope

**If invoked after `/build`:**
Automatically scope to changes from the most recent build session — files created or modified, the milestone just completed. Do not ask.

**If invoked ad hoc:**
Ask the user before starting:
- A specific file, folder, or milestone?
- The full codebase?
- A specific focus (security only, plan adherence only, code quality only)?

## Run the Review

Always run all three dimensions unless the user configures a specific focus.

### 1. Plan Adherence
- Was everything in scope actually built per the plan?
- Does implementation match architecture and tech stack decisions?
- Any deviations not flagged during `/build`?
- Unresolved open questions still showing up in the code?

### 2. Code Quality
- Structure follows established patterns from plan and scaffold?
- Readability, naming consistency
- Unnecessary duplication or premature abstraction
- Dead code, unused imports, leftover scaffolding
- Test coverage on critical paths

### 3. Security
- Input validation at system boundaries
- Auth and authorization correctness
- Injection vulnerabilities (SQL, command, XSS)
- Sensitive data exposure (hardcoded secrets, PII in logs, unencrypted storage)
- OWASP Top 10 as baseline checklist

**Security is always checked** — even if the user asks for a narrow focus, surface critical security findings regardless.

## Severity

| Level | Definition |
|-------|-----------|
| **Critical** | Security vulnerability, broken functionality, data loss risk, major plan deviation |
| **Warning** | Quality issues, minor deviations, missing tests on important paths, performance concerns |
| **Suggestion** | Improvements, refactors, nice-to-haves |

## Fix Scope

**Offer to fix inline** (with confirmation) when:
- Finding is Critical
- Fix is clearly bounded — one or two lines/blocks, unambiguous
- Change is contained to the flagged location

**Route to `/iterate`** when:
- Finding is systemic or architectural
- Fix spans multiple files or modules
- Finding is Warning or Suggestion
- Right fix isn't immediately obvious

## Output Format

**Use chat** when: fewer than ~5 findings, single file or small change set, quick mid-session check.

**Create/append `docs/review.md`** when: 5+ findings, post-milestone review, full codebase review, or user wants a record.

### Review Doc Structure

```
# Review — [Scope]
Date: YYYY-MM-DD
Triggered by: /build completion | ad hoc
Scope: [description]
Focus: All | Plan Adherence | Code Quality | Security

## Summary
[Overall health. Critical: N | Warning: N | Suggestion: N]

## Plan Adherence
## Code Quality
## Security

## Findings

### Critical
| # | Location | Issue | Recommendation | Status |

### Warning
| # | Location | Issue | Recommendation | Status |

### Suggestion
| # | Location | Issue | Recommendation | Status |

## Resolved This Session
## Carried to /iterate
```

## Soft Gate

If the user invokes `/ship` and unresolved Criticals exist:
- List them explicitly
- Ask for confirmation before allowing `/ship` to proceed
- Do not hard block — the user can override

## After the Review

Summarize what's been deferred to `/iterate`:
- List of findings with severity and location
- Suggested priority order
- Note which are blocking ship vs. optional

## Behavior Rules

- **After /build: auto-scope** — infer from session changes, don't ask
- **Ad hoc: always ask scope** — never assume full codebase without being told
- **Chat vs. doc: use judgment** — volume and significance determine the format
- **Inline fixes stay bounded** — only offer to fix clearly contained critical issues
- **Prior reviews carry forward** — check if previously flagged issues were resolved; flag if not
- **No false positives** — don't flag intentional design choices documented in the plan or CLAUDE.md
