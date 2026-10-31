// Routing rules shared by this mod (classify.ts) and the agent harness (dashboard/harness/routing.py).
// Keep the object after `export default` strict JSON (double quotes, no comments or trailing commas):
// the harness reads it with a JSON parser. Regex sources must work in both JS and Python.
export default {
  "override": {
    "source": "^\\s*!(light|fast|cheap|standard|normal|deep|think|opus)\\b[:\\s]*",
    "flags": "i"
  },
  "override_tier": {
    "light": "light",
    "fast": "light",
    "cheap": "light",
    "standard": "standard",
    "normal": "standard",
    "deep": "deep",
    "think": "deep",
    "opus": "deep"
  },
  "deep_command": {
    "source": "^\\s*\\/(plan|brainstorm|design|review|reflect|scaffold)\\b",
    "flags": "i"
  },
  "light_command": {
    "source": "^\\s*\\/(sync|status)\\b",
    "flags": "i"
  },
  "deep": {
    "source": "\\b(plan(ning)?(?!\\.md)|brainstorm\\w*|architect\\w*|re-?design\\w*|design(ing)?|strateg\\w*|trade-?offs?|approach(es)?|think (about|through|carefully|hard)|figure out (how|why|whether)|should (we|i)|what('s| is) the best way|pros and cons|from scratch|root cause|investigate|proposal|review (the|this|my|our)|deep dive)\\b",
    "flags": "i"
  },
  "light": [
    {
      "source": "^\\s*(please\\s+)?(git\\s+)?(commit|push|pull|merge|rebase|stash|tag|cherry-pick)\\b",
      "flags": "i",
      "why": "git"
    },
    {
      "source": "\\b(commit|push)\\s+(it|this|that|these|both|everything|them|the changes)\\b",
      "flags": "i",
      "why": "git"
    },
    {
      "source": "\\bcommit (and|&) push\\b",
      "flags": "i",
      "why": "git"
    },
    {
      "source": "^\\s*(re)?run\\s+(the\\s+)?(unit\\s+)?(tests?|lint\\w*|build|format\\w*|smoke|type-?check)\\b",
      "flags": "i",
      "why": "run"
    },
    {
      "source": "\\b(re)?start (the )?(dev )?server\\b|\\bkill (the )?(process|server)\\b",
      "flags": "i",
      "why": "server"
    },
    {
      "source": "^\\s*rename\\b|\\brename (it|this|the)\\b",
      "flags": "i",
      "why": "rename"
    },
    {
      "source": "\\bbump (the )?version\\b",
      "flags": "i",
      "why": "version"
    },
    {
      "source": "\\bfix (the |a |this )?typos?\\b",
      "flags": "i",
      "why": "typo"
    },
    {
      "source": "^\\s*(change|replace|swap|update) .{1,80} (to|with) .{1,80}$",
      "flags": "i",
      "why": "defined edit"
    },
    {
      "source": "\\badd .{1,60} to \\.?gitignore\\b",
      "flags": "i",
      "why": "gitignore"
    }
  ],
  "light_max_chars": 220,
  "continue": {
    "source": "^\\s*((yes|yep|yeah|ok(ay)?|sure|go ahead|do it|do that|sounds good|looks good|lgtm|continue|proceed|please do|go for it|perfect|great|thanks?|keep going)\\b[\\s.!,]*)+$",
    "flags": "i"
  }
}
