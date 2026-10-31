---
id: 6a6f2d
source: reflect:ryans-boomin-beats:golden-query-test
title: Golden-query regression test for type-ahead search
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-26T23:11:12Z
updated: 2026-10-29T03:49:07Z
---

## Brief
Six reported queries (Money Trees, september, kendrick lamar money, Tadow, Come and Get Your Love, mid-word) plus controls; mocked Last.fm/Deezer fixtures

## Acceptance

## Runs

## Updates
- 2026-10-26T23:11:12Z · created
- 2026-10-26T23:18:58Z · status: backlog → doing (building)
- 2026-10-26T23:18:58Z · status: doing → review (built + verified)
- 2026-10-26T23:18:58Z · comment: 13 golden queries replayed from recorded Last.fm/Deezer answers (tests/test_search_golden.py, golden/record.py). Caught and fixed: dancing queen, redbone slowed, come and get your love lost their real results to the named-artist rule. Known gap kept as expectedFailure: 'money tre' lacks Kendrick's original.
- 2026-10-29T03:49:07Z · status: review → done (reflected: complete)
