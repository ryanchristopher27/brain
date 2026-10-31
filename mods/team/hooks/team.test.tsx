import { expect, mock, test } from 'claude-code/testing'

// A fake brain dashboard: answers the harness API the mod calls, and records what it was sent.
function dashboard(state: { agents: any[]; holds: any[]; messages: Record<string, any[]>; up?: boolean; updates?: any[] }) {
  const sent: { method: string; path: string; body: any }[] = []
  const answer = (status: number, body: unknown) =>
    ({ value: { status, ok: status < 400, headers: {}, text: JSON.stringify(body) } })
  const fetch = (_: unknown, e: { url: string; init?: { method?: string; body?: string } }) => {
    if (state.up === false) throw new Error('connection refused')
    const path = e.url.replace('http://127.0.0.1:8766', '')
    const method = e.init?.method || 'GET'
    sent.push({ method, path, body: e.init?.body ? JSON.parse(e.init.body) : undefined })
    if (path === '/api/config') return answer(200, { token: 't' })
    if (path === '/api/harness/agents') return answer(200, state.agents)
    if (path === '/api/harness/holds') return answer(200, state.holds)
    let m = path.match(/^\/api\/harness\/agents\/([^/]+)\/messages/)
    if (m) return answer(200, state.messages[decodeURIComponent(m[1] ?? '')] || [])
    m = path.match(/^\/api\/harness\/agents\/([^/]+)\/message$/)
    if (m) return answer(200, { id: 41, thread: 'th1', role: 'user', text: 'x' })
    if (/^\/api\/harness\/holds\/\d+\/(approve|deny)$/.test(path)) {
      state.holds = []
      return answer(200, { status: 'approved' })
    }
    if (path === '/api/harness/kill') return answer(200, { paused: state.agents.length })
    m = path.match(/^\/api\/harness\/updates\?after=(\d+)$/)
    if (m) {
      const after = Number(m[1])
      const all = state.updates || []
      return answer(200, { latest: Math.max(0, ...all.map((u) => u.id)), messages: all.filter((u) => u.id > after) })
    }
    if (path === '/api/harness/teams') return answer(200, [{ name: 'pipeline', label: 'Plan → build → review', inputs: ['scope', 'task'], description: 'd' }])
    if (path === '/api/harness/teams/pipeline/start') {
      return answer(200, { team: 'app:pipeline', agents: ['app-planner', 'app-builder'], lead: 'app-planner',
        kickoff: 'Take task #ab to review.', message: { id: 50, thread: 'tk' } })
    }
    return answer(404, { error: 'unknown' })
  }
  return { sent, fetch }
}

const AGENT = { name: 'brain-builder', persona: 'builder', state: 'waiting', model: { mode: 'pinned' },
  current_model: 'claude-sonnet-5-5', usage_today: 0.12, limits: { daily_usd: 2 }, team: 'brain:pipeline', queued: 0 }
const HOLD = { id: 7, agent: 'brain-builder', kind: 'command', tool: 'Bash', input: { command: 'npm test' }, reason: 'x' }
const PANE = { plugin: 'team', component: 'Pane', requestId: 'team',
  props: { title: 'Team', isFocused: false, bodyColumns: 60, placement: 'dock', scroll: { offset: 0, bodyRows: 30 }, view: {} } } as const

function engine(on: any, fetch: any, toasts: string[] = [], prompts: string[] = [], logs: string[] = []) {
  on('ui.log', (_: unknown, e: { text: string }) => { logs.push(e.text); return { value: undefined } })
  on('http.fetch', fetch)
  on('command.register', () => ({ value: { command: 'team' } }))
  on('tool.register', (_: unknown, e: { name: string }) => ({ value: { tool: `mcp__team__${e.name}` } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.toast', (_: unknown, e: { text: string }) => { toasts.push(e.text); return { value: undefined } })
  on('prompt.submit', (_: unknown, e: { text: string }) => { prompts.push(e.text); return { text: e.text } })
  on('session.start', (_: unknown, e: { cwd: string }) => ({ cwd: e.cwd }))
  return mock.clock(on) // the poll timer runs on it: a test advances it to deliver
}

test('the pane lists agents and approves a waiting command, on every surface', async ($, on) => {
  const dash = dashboard({ agents: [AGENT], holds: [HOLD], messages: {} })
  const toasts: string[] = []
  engine(on, dash.fetch, toasts)
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  expect(toasts).toEqual(['brain-builder wants to run a command: npm test'])

  for (const surface of ['terminal', 'desktop'] as const) {
    dash.sent.length = 0
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /npm test/ }))?.text).toBe('npm test')
    expect(await ui.find({ type: 'Text', text: /brain-builder/ })).toBeTruthy()
    if (surface === 'desktop') {
      await ui.press({ key: 'always-7' })
      expect(dash.sent.find((s) => s.method === 'POST')).toEqual(
        { method: 'POST', path: '/api/harness/holds/7/approve', body: { always: true } })
    }
    await ui.unmount()
  }
})

test('a message sent from this session gets its reply delivered back as a turn', async ($, on) => {
  const state = { agents: [{ ...AGENT, state: 'live' }], holds: [], messages: {} as Record<string, any[]> }
  const dash = dashboard(state)
  const prompts: string[] = []
  const clock = engine(on, dash.fetch, [], prompts)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const r = await $.tool.call({ tool: 'mcp__team__send', agent: 'brain-builder', text: 'run the tests' } as any)
  expect(JSON.stringify(r)).toContain('Sent to brain-builder')
  expect(dash.sent.find((s) => s.path.endsWith('/message'))?.body).toEqual({ text: 'run the tests' })

  state.messages['brain-builder'] = [
    { id: 41, thread: 'th1', role: 'user', text: 'run the tests' },
    { id: 42, thread: 'other', role: 'assistant', text: 'unrelated' },
    { id: 43, thread: 'th1', role: 'assistant', text: 'All 12 tests pass.' },
  ]
  await $.command.run({ command: 'team', args: '' } as any)
  expect(prompts).toEqual([]) // a command can't start a turn: delivery waits for the timer
  await clock.advance(4000)
  expect(prompts).toEqual(['Reply from team agent brain-builder:\n\nAll 12 tests pass.'])
  await clock.advance(4000)
  expect(prompts.length).toBe(1) // delivered once
})

test('the band shows the first waiting action and stays out of the way otherwise', async ($, on) => {
  const state = { agents: [AGENT], holds: [HOLD, { ...HOLD, id: 8 }], messages: {} }
  engine(on, dashboard(state).fetch)
  on('ui.render', ($: any, e: any) => { const { Text } = $.ui.resolve(e); return <Text>engine</Text> })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const band = await $.ui.mount({ plugin: 'team', component: 'AbovePrompt', surface: 'terminal', props: { hasSurvey: false } } as any)
  expect((await band.find({ type: 'Text', text: /npm test/ }))?.text).toContain('(+1 more in /team)')
  await band.unmount()
})

test('/team says how to start the dashboard when it is down', async ($, on) => {
  engine(on, dashboard({ agents: [], holds: [], messages: {}, up: false }).fetch)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const r = await $.command.run({ command: 'team', args: '' } as any)
  expect(JSON.stringify(r)).toContain("isn't reachable")
  const usage = await $.command.run({ command: 'team', args: 'dance' } as any)
  expect(JSON.stringify(usage)).toContain('Usage: /team')
})

test('a started team reports back: first reply as a turn, the final report quietly', async ($, on) => {
  const state = { agents: [], holds: [], messages: {} as Record<string, any[]> }
  const dash = dashboard(state)
  const prompts: string[] = [], logs: string[] = []
  const clock = engine(on, dash.fetch, [], prompts, logs)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const r = await $.tool.call({ tool: 'mcp__team__start_team', template: 'pipeline', project: 'app', task: 'ab' } as any)
  expect(JSON.stringify(r)).toContain('Started app:pipeline')
  expect(dash.sent.find((x) => x.path.endsWith('/start'))?.body).toEqual(
    { project: 'app', prefix: '', inputs: { task: 'ab' } })

  state.messages['app-planner'] = [{ id: 51, thread: 'tk', role: 'assistant', text: 'Dispatched to builder.' }]
  await clock.advance(4000)
  expect(prompts).toEqual(['Reply from team agent app-planner:\n\nDispatched to builder.'])

  state.messages['app-planner'].push({ id: 55, thread: 'tk', role: 'assistant', text: 'Task #ab is in review.' })
  await clock.advance(4000)
  expect(prompts.length).toBe(1) // no second turn
  expect(logs).toEqual(['Team · app-planner: Task #ab is in review.'])
})

test('/team follow forwards what agents tell you, quietly, skipping threads this session started', async ($, on) => {
  const state = { agents: [], holds: [], messages: {} as Record<string, any[]>,
    updates: [{ id: 5, agent: 'old', thread: 'x', text: 'before following' }] as any[] }
  const prompts: string[] = [], logs: string[] = []
  const clock = engine(on, dashboard(state).fetch, [], prompts, logs)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const on1 = await $.command.run({ command: 'team', args: 'follow' } as any)
  expect(JSON.stringify(on1)).toContain('Following the team')
  await $.tool.call({ tool: 'mcp__team__send', agent: 'expert', text: 'q' } as any) // own thread 'th1'
  state.updates.push({ id: 6, agent: 'lead', thread: 'y', text: 'Research done: use SQS.' },
    { id: 7, agent: 'expert', thread: 'th1', text: 'answer to my own question' })
  await clock.advance(4000)
  expect(logs).toEqual(['Team · lead: Research done: use SQS.']) // nothing old, nothing from my own thread
  expect(prompts).toEqual([])
  await clock.advance(4000)
  expect(logs.length).toBe(1) // each update once
  await $.command.run({ command: 'team', args: 'follow off' } as any)
  state.updates.push({ id: 8, agent: 'lead', thread: 'y', text: 'later' })
  await clock.advance(4000)
  expect(logs.length).toBe(1)
})
