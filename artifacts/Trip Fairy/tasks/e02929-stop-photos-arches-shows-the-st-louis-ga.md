---
id: e02929
source: review3:arches-photo
title: "Stop photos: Arches shows the St. Louis Gateway Arch; Zion shows an engraving"
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-10-26T01:43:35Z
updated: 2026-10-26T02:24:45Z
---

## Brief
Live review 2026-10-26: the Utah Mighty 5 'Arches' stop card shows the Gateway Arch (St. Louis) and Zion an old engraving. The city-photo lookup should prefer the national park for placeType park (e.g. 'Arches National Park') and skip non-photo images (engravings/illustrations).

## Acceptance

## Runs

## Updates
- 2026-10-26T01:43:35Z · created
- 2026-10-26T02:12:46Z · status: backlog → doing
- 2026-10-26T02:24:45Z · status: doing → review (Deployed cbf3a8b + verified live on the test account: Arches now Delicate Arch (was the St. Louis Gateway Arch), Zion now Angels Landing (was an engraving); every existing stop photo is re-checked once (v2) and kept if nothing better turns up. Unit 678, smoke 226.)
