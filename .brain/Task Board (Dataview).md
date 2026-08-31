# Task Board — Dataview

> Fallback view. Only renders if the **Dataview** community plugin is installed
> (Settings → Community plugins → Browse → "Dataview" → Install → Enable).
> If you're on current Obsidian, prefer **Task Board.base** — it needs no plugin.

## 🔸 Doing
```dataview
TABLE WITHOUT ID file.link AS Task, type AS Type, assignee AS Who, source AS Source, updated AS Updated
FROM "tasks"
WHERE status = "doing"
SORT updated DESC
```

## 👀 Review
```dataview
TABLE WITHOUT ID file.link AS Task, type AS Type, assignee AS Who, source AS Source, updated AS Updated
FROM "tasks"
WHERE status = "review"
SORT updated DESC
```

## 📋 Backlog
```dataview
TABLE WITHOUT ID file.link AS Task, type AS Type, source AS Source, created AS Created
FROM "tasks"
WHERE status = "backlog"
SORT created ASC
```

## ✅ Done
```dataview
TABLE WITHOUT ID file.link AS Task, type AS Type, source AS Source, updated AS Updated
FROM "tasks"
WHERE status = "done"
SORT updated DESC
```

## Counts by status
```dataview
TABLE WITHOUT ID key AS Status, length(rows) AS Count
FROM "tasks"
WHERE type = "task" OR type = "issue"
GROUP BY status
SORT key ASC
```
