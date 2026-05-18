# Phase: Review

## Overview
A full-spectrum audit of what was built — covering plan adherence, code quality, and security. Scope is automatically determined when invoked after `/build` (changes from that session), or set by the user when invoked ad hoc. Findings are presented in chat for smaller reviews or written to `docs/review.md` for larger ones. Critical, clearly-bounded issues can be fixed inline. Everything else is routed to `/iterate`.

---

## Trigger
User invokes `/review` manually. `/build` suggests it at milestone completions — always a suggestion, never forced.

---

## Input

**Primary:** Code in scope (see Scope below)

**Also reads:**
- `docs/plan.md` — for plan adherence checks
- `docs/brainstorm.md` — for intent validation
- Prior `docs/review.md` — to track whether previously flagged issues were resolved
- `CLAUDE.md` — for project-specific conventions and rules

---

## Scope Determination

### After `/build`
Automatically scopes to the changes made during the most recent build session:
- Files created or modified during the session
- The milestone or task that was just completed
- Does not re-review already-reviewed code unless it was touched

### Ad Hoc
Ask the user before starting:
- A specific file or folder?
- A specific milestone from the plan?
- The full codebase?
- A specific concern (security only, plan adherence only, etc.)?

---

## Review Dimensions

All three are always run unless the user configures otherwise.

### 1. Plan Adherence
- Was everything in the targeted milestone/task actually built?
- Does the implementation match the architecture and tech stack decisions from the plan?
- Were any deviations introduced that weren't flagged during `/build`?
- Are open questions from the plan still unresolved in the code?

### 2. Code Quality
- Structure and organization — does the code follow the patterns established in the plan and scaffold?
- Readability and clarity
- Duplication and abstraction — unnecessary repetition, premature abstraction
- Naming consistency
- Dead code, unused imports, leftover scaffolding
- Test coverage — are critical paths tested?

### 3. Security
- Input validation at system boundaries
- Authentication and authorization correctness
- Injection vulnerabilities (SQL, command, XSS, etc.)
- Sensitive data exposure (hardcoded secrets, logging PII, unencrypted storage)
- Dependency vulnerabilities (if manifest is in scope)
- OWASP Top 10 as a checklist baseline

---

## Severity Levels

| Level | Definition |
|-------|-----------|
| **Critical** | Security vulnerability, broken functionality, data loss risk, or major plan deviation. Blocks `/ship`. |
| **Warning** | Code quality issues, minor plan deviations, performance concerns, missing tests on important paths. Should be addressed before ship. |
| **Suggestion** | Improvements, refactors, nice-to-haves. Address in `/iterate` if desired. |

---

## Fix Scope

**Fix inline (with confirmation):**
- Critical findings that are clearly bounded — a missing validation, a hardcoded secret, a broken null check, a missing auth guard
- Small enough that the fix is unambiguous and contained to one or two lines/blocks
- Always confirm before applying

**Route to `/iterate`:**
- Anything systemic or architectural
- Anything requiring changes across multiple files or modules
- Warnings and suggestions
- Anything where the right fix isn't immediately obvious

---

## Output Format

### Chat (Small Reviews)
Use when:
- Fewer than ~5 findings total
- Scope is a single file or small set of changes
- Review was triggered mid-session for a quick check

Format: severity-ranked list in chat with file references and line numbers.

### Review Doc (Larger Reviews)
Use when:
- 5+ findings, or significant scope
- Post-milestone review
- Full codebase review
- User wants a persistent record

Save to `docs/review.md`. If one already exists, append a new dated section.

```
# Review — [Scope Description]
Date: YYYY-MM-DD
Triggered by: /build completion | ad hoc
Scope: [files, milestone, or description]
Focus: All | Plan Adherence | Code Quality | Security

## Summary
[1-2 sentences on overall health. Finding counts by severity.]
Critical: N | Warning: N | Suggestion: N

## Plan Adherence
[Findings or "No issues found"]

## Code Quality
[Findings or "No issues found"]

## Security
[Findings or "No issues found"]

## Findings

### Critical
| # | Location | Issue | Recommendation | Status |
|---|----------|-------|---------------|--------|

### Warning
| # | Location | Issue | Recommendation | Status |
|---|----------|-------|---------------|--------|

### Suggestion
| # | Location | Issue | Recommendation | Status |
|---|----------|-------|---------------|--------|

## Resolved This Session
[Fixes applied inline during this review]

## Carried to /iterate
[Findings deferred for the next iteration cycle]
```

---

## Soft Gate on `/ship`

If unresolved Critical findings exist when `/ship` is invoked:
- Warn the user explicitly — list the unresolved criticals
- Ask for confirmation before allowing `/ship` to proceed
- Do not hard block — the user can override with intent

---

## Handoff to `/iterate`

After the review, produce a summary of what's been deferred:
- List of findings routed to `/iterate` with severity and location
- Suggested priority order for addressing them
- Note which findings are blocking ship vs. optional

---

## Behavior Notes

- **Scope is automatic after `/build`** — don't ask; infer from the session's changes
- **Scope is always asked ad hoc** — never assume the full codebase without being told
- **Chat vs. doc is dynamic** — use judgment on volume and significance
- **Inline fixes are bounded** — only offer to fix what is clearly contained; anything systemic goes to `/iterate`
- **Security is always checked** — even if the user asks for code quality only, flag critical security issues
- **Prior reviews inform this one** — check if previously flagged issues were resolved; note if they weren't
- **No false positives** — do not flag things that are intentional design choices documented in the plan or `CLAUDE.md`
