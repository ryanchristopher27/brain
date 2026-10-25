import { expect, test } from 'claude-code/testing'
import type { TurnStepInput } from 'claude-code'

import { decide } from './classify'

// ── the rules ──────────────────────────────────────────────────────────────────
test('mechanical requests are light', () => {
  for (const p of ['commit and push both', 'push it', 'git pull', 'run the tests', 'rename the trip planner project to Trip Fairy',
    'restart the server', 'bump the version', 'fix the typo in the README', 'change the button color to red'])
    expect(decide(p, 'standard').tier).toBe('light')
})

test('open-ended thinking is deep', () => {
  for (const p of ['plan the migration to the new API', 'brainstorm names for the app', 'I want you to think about the design of the hub',
    'what is the best way to cache this?', 'should we split the service?', '/plan', '/brainstorm a pricing page'])
    expect(decide(p, 'standard').tier).toBe('deep')
})

test('a long request mentioning commit is not assumed mechanical', () => {
  const p = 'Add a settings page with a theme picker and a language picker, persist both, wire them into the header and the footer, write tests, then commit'
  expect(decide(p, 'standard').tier).toBe(null)
})

test('plan.md is a file name, not planning', () => {
  expect(decide('add a line to plan.md saying the tests pass', 'standard').tier).not.toBe('deep')
})

test('a continuation keeps the previous tier', () => {
  expect(decide('yes, go ahead', 'deep').tier).toBe('deep')
  expect(decide('do it', 'light').tier).toBe('light')
})

test('an override prefix wins and is stripped from the prompt', () => {
  const d = decide('!deep commit this carefully', 'standard')
  expect(d.tier).toBe('deep')
  expect(d.text).toBe('commit this carefully')
  expect(decide('!light design tokens rename', 'standard').tier).toBe('light')
})

// ── end to end: the prompt decides, every main-loop request of the turn follows ──
async function step($: any, input: Partial<TurnStepInput>) {
  const s = $.turn.step({ turnId: 't1', index: 0, model: 'claude-sonnet-5-5', messageCount: 4, ...input })
  for await (const _ of s) { /* drain */ }
  return s.result
}

function bottoms(on: any, seen: { model: string; effort?: unknown }[], classified = 'standard') {
  on('prompt.submit', (_$: unknown, e: { text: string }) => ({ text: e.text }))
  // the router's classifier is one model.complete call: answer with the label as the reply
  on('model.complete', () => ({ value: { isAnswered: true, text: classified,
    usage: { input_tokens: 0, output_tokens: 1, cache_read_input_tokens: 0, cache_creation_input_tokens: 0 } } }))
  on('turn.step', async function* (_$: unknown, e: TurnStepInput) {
    seen.push({ model: e.model, effort: e.effort })
    return { turnId: e.turnId, index: e.index, answer: '', toolUses: [] }
  })
}

const submit = ($: any, text: string) => $.prompt.submit({ text, wait: false, origin: { kind: 'composer' } })

test('a commit goes to the light model at low effort', async ($, on) => {
  const seen: { model: string; effort?: unknown }[] = []
  bottoms(on, seen)
  await submit($, 'commit and push it')
  await step($, {})
  expect(seen[0]).toEqual({ model: 'claude-haiku-5-5', effort: 'low' })
})

test('design work goes to the deep model at high effort, every step of the turn', async ($, on) => {
  const seen: { model: string; effort?: unknown }[] = []
  bottoms(on, seen)
  await submit($, 'think about the design of the dashboard')
  await step($, { index: 0 })
  await step($, { index: 5 })
  expect(seen).toEqual([{ model: 'claude-opus-5-5', effort: 'high' }, { model: 'claude-opus-5-5', effort: 'high' }])
})

test('undecided prompts ask the classifier', async ($, on) => {
  const seen: { model: string; effort?: unknown }[] = []
  bottoms(on, seen, 'deep')
  await submit($, 'the export sometimes drops rows, look into it')
  await step($, {})
  expect(seen[0].model).toBe('claude-opus-5-5')
})

test('standard leaves the session model alone', async ($, on) => {
  const seen: { model: string; effort?: unknown }[] = []
  bottoms(on, seen, 'standard')
  await submit($, 'add a loading spinner to the save button and a toast when it finishes')
  await step($, {})
  expect(seen[0].model).toBe('claude-sonnet-5-5')
})

test('a light turn escalates after too many steps, and long chats stay put', async ($, on) => {
  const seen: { model: string; effort?: unknown }[] = []
  bottoms(on, seen)
  await submit($, 'push it')
  await step($, { index: 11 })
  await step($, { index: 12 })
  await submit($, 'push it')
  await step($, { index: 0, messageCount: 200 })
  expect(seen.map(s => s.model)).toEqual(['claude-haiku-5-5', 'claude-sonnet-5-5', 'claude-sonnet-5-5'])
})

test('subagent requests are not rerouted', async ($, on) => {
  const seen: { model: string; effort?: unknown }[] = []
  bottoms(on, seen)
  await submit($, 'think about the architecture')
  await step($, { agentId: 'a1', model: 'claude-haiku-5-5' })
  expect(seen[0].model).toBe('claude-haiku-5-5')
})

