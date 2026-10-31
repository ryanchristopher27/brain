import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Agent, Ask, Follow, Hold } from '../types'

// The brain dashboard (dashboard/server.py) hosts the agent harness on localhost. Its token comes
// from /api/config, which only same-machine callers can reach.
const BASE = 'http://127.0.0.1:8766'
const HUB = 'http://localhost:8766/#/team' // the desktop app links only https: and http://localhost
const PANE = 'team'
const POLL_MS = 4000
const ASK_TTL_MS = 2 * 60 * 60 * 1000 // since the thread's last activity

const agentsAtom = atom({ plugin: 'team', key: 'agents' } as const, [])
const holdsAtom = atom({ plugin: 'team', key: 'holds' } as const, [])
const onlineAtom = atom({ plugin: 'team', key: 'online' } as const, false)
const asksAtom = atom({ plugin: 'team', key: 'asks' } as const, [])
const followAtom = atom({ plugin: 'team', key: 'follow' } as const, { on: false, after: 0 })

const KIND: Record<string, string> = {
  'outside-scope write': 'write outside its folder',
  command: 'run a command',
  'destructive command': 'run a destructive command',
  'git push': 'push to the remote',
  tool: 'use a tool',
}

let token: string | null = null
const seenHolds = new Set<number>()

async function api($: EngineInterface, path: string, method = 'GET', body?: unknown): Promise<any> {
  if (!token) {
    const r = await $.http.fetch(`${BASE}/api/config`)
    token = JSON.parse(r.text).token as string
  }
  const r = await $.http.fetch(`${BASE}${path}`, {
    method,
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (r.status === 401) token = null // the dashboard issued a new token; fetch it next time
  const data = r.text ? JSON.parse(r.text) : null
  if (!r.ok) throw new Error((data && data.error) || `dashboard answered ${r.status}`)
  return data
}

function toAgent(a: any): Agent {
  return {
    name: a.name,
    persona: a.persona,
    state: a.state,
    model: a.model?.mode === 'auto' ? 'auto' : String(a.current_model || '').replace(/^claude-/, ''),
    usage: a.usage_today || 0,
    cap: a.limits?.daily_usd ?? 2,
    team: a.team ?? null,
    queued: a.queued || 0,
  }
}

function toHold(raw: any): Hold {
  const what = raw.input?.command || raw.input?.file_path || raw.input?.notebook_path || raw.tool
  return { id: raw.id, agent: raw.agent, kind: raw.kind, what: String(what).slice(0, 200), reason: raw.reason }
}

// Polling writes only real changes, so the pane and band don't redraw every few seconds.
const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b)

// Status for the pane and band: safe from any hook.
async function poll($: EngineInterface): Promise<void> {
  let agents: Agent[], holds: Hold[]
  try {
    agents = (await api($, '/api/harness/agents')).map(toAgent)
    holds = (await api($, '/api/harness/holds')).map(toHold)
  } catch {
    if (await read($, onlineAtom)) await update($, onlineAtom, () => false)
    return
  }
  if (!(await read($, onlineAtom))) await update($, onlineAtom, () => true)
  if (!same(await read($, agentsAtom), agents)) await update($, agentsAtom, () => agents)
  if (!same(await read($, holdsAtom), holds)) await update($, holdsAtom, () => holds)
  for (const hold of holds) {
    if (seenHolds.has(hold.id)) continue
    seenHolds.add(hold.id)
    $.ui.toast(`${hold.agent} wants to ${KIND[hold.kind] || hold.kind}: ${hold.what}`)
  }
}

// The background timer: status plus delivery. Delivery runs only here, because a turn can't be
// started from a command or tool hook (it would wait on the turn that hook is holding).
async function tick($: EngineInterface): Promise<void> {
  await poll($)
  if (!(await read($, onlineAtom))) return
  await deliverReplies($)
  await forwardUpdates($)
}

// A quiet update: a dim line for the person, background for the model's next turn, no turn now.
async function quiet($: EngineInterface, agent: string, body: string): Promise<void> {
  try { // best effort: if the engine refuses the row, the person still sees the line and the toast
    await $.session.append({
      message: { type: 'user', content: [{ type: 'text', text: `[Team update from ${agent}; background, no reply needed]\n${body}` }] },
    })
  } catch {}
  $.ui.log(`Team · ${agent}: ${body}`)
  $.ui.toast(`${agent}: ${body.split('\n')[0]?.slice(0, 120) ?? ''}`)
}

// `/team follow`: what agents told the user (in threads this session didn't start) arrives quietly.
async function forwardUpdates($: EngineInterface): Promise<void> {
  const follow = await read($, followAtom)
  if (!follow.on) return
  let feed: { latest: number; messages: any[] }
  try {
    feed = await api($, `/api/harness/updates?after=${follow.after}`)
  } catch {
    return
  }
  const own = new Set((await read($, asksAtom)).map((a) => a.thread))
  let after = feed.messages.length ? follow.after : feed.latest
  for (const m of feed.messages) {
    try {
      if (!own.has(m.thread)) await quiet($, m.agent, m.text)
    } catch {
      break // stop here; the next tick resumes from the last one delivered
    }
    after = m.id
  }
  if (after !== follow.after) await update($, followAtom, (f) => ({ ...f, after }))
}

async function setFollow($: EngineInterface, on: boolean): Promise<string> {
  const after = on ? (await api($, '/api/harness/updates?after=0')).latest : 0
  await update($, followAtom, () => ({ on, after }))
  return on
    ? 'Following the team: what agents report to you will appear here quietly (no turn, a dim line and a toast). /team follow off to stop.'
    : 'Stopped following the team. Replies to messages you send from here still arrive.'
}

// Replies to messages this session sent: the first starts a turn here (someone is waiting on it), so
// nothing has to wait or poll; later ones in the thread (a lead's final report) arrive quietly.
async function deliverReplies($: EngineInterface): Promise<void> {
  const asks = await read($, asksAtom)
  if (!asks.length) return
  const now = await $.clock.now()
  const keep: Ask[] = []
  for (const ask of asks) {
    let msgs: any[] = []
    try {
      msgs = await api($, `/api/harness/agents/${encodeURIComponent(ask.agent)}/messages?limit=60`)
    } catch {
      if (now - ask.at < ASK_TTL_MS) keep.push(ask)
      continue
    }
    const fresh = msgs.filter((m) => m.id > ask.after && m.thread === ask.thread && m.role === 'assistant')
    if (!fresh.length) {
      if (now - ask.at < ASK_TTL_MS) keep.push(ask)
      continue
    }
    let done = ask
    try { // a failed delivery keeps the ask as it was, so the next tick retries it
      if (!ask.replied) {
        await $.prompt.submit({ text: `Reply from team agent ${ask.agent}:\n\n${fresh.map((m) => m.text).join('\n\n')}` })
        done = { ...ask, replied: true, after: fresh[fresh.length - 1].id, at: now }
      } else {
        for (const m of fresh) {
          await quiet($, ask.agent, m.text)
          done = { ...done, after: m.id, at: now }
        }
      }
    } catch {}
    keep.push(done)
  }
  if (!same(asks, keep)) await update($, asksAtom, () => keep)
}

async function track($: EngineInterface, agent: string, msg: { id: number; thread: string }): Promise<void> {
  const ask: Ask = { agent, id: msg.id, thread: msg.thread, at: await $.clock.now(), replied: false, after: msg.id }
  await update($, asksAtom, (list) => [...list, ask])
}

async function send($: EngineInterface, agent: string, text: string): Promise<string> {
  const rec = await api($, `/api/harness/agents/${encodeURIComponent(agent)}/message`, 'POST', { text })
  await track($, agent, rec)
  return `Sent to ${agent}. Their reply will arrive in this conversation on its own when it's ready.`
}

type StartArgs = { template?: string; project?: string; prefix?: string; scope?: string;
  test_command?: string; task?: string; question?: string }

async function startTeam($: EngineInterface, a: StartArgs): Promise<string> {
  const r = await api($, `/api/harness/teams/${encodeURIComponent(String(a.template || ''))}/start`, 'POST', {
    project: a.project || '', prefix: a.prefix || '',
    inputs: { scope: a.scope, test_command: a.test_command, task: a.task, question: a.question },
  })
  if (r.message) await track($, r.lead, r.message)
  await poll($)
  return `Started ${r.team}: ${r.agents.join(', ')}. ` + (r.kickoff
    ? `${r.lead} is working on it; its first reply will arrive here, and later reports quietly.`
    : `Nothing was sent yet; message ${r.lead} to give it work.`)
}

async function templateList($: EngineInterface): Promise<string> {
  try {
    const ts: any[] = await api($, '/api/harness/teams')
    return ts.map((t) => `${t.name} (${t.label}; inputs: ${t.inputs.join(', ') || 'none'}): ${t.description}`).join(' | ')
  } catch {
    return 'pipeline, project-team, research, debate'
  }
}

async function decide($: EngineInterface, hold: Hold, approve: boolean, always = false): Promise<void> {
  try {
    await api($, `/api/harness/holds/${hold.id}/${approve ? 'approve' : 'deny'}`, 'POST', { always })
  } catch (err) {
    $.ui.toast(`Couldn't ${approve ? 'allow' : 'deny'}: ${(err as Error).message}`)
  }
  await poll($)
}

async function stopAll($: EngineInterface): Promise<string> {
  const r = await api($, '/api/harness/kill', 'POST')
  await poll($)
  return `Stopped everything: denied what was waiting and paused ${r.paused} agents.`
}

function summary(agents: Agent[], holds: Hold[]): string {
  const working = agents.filter((a) => a.state === 'busy').length
  const used = agents.reduce((n, a) => n + a.usage, 0)
  return `${agents.length} agents · ${working} working · $${used.toFixed(2)} today` +
    (holds.length ? ` · ${holds.length} waiting on you` : '')
}

function stateColor(state: string): 'success' | 'warning' | 'subtle' {
  return state === 'busy' || state === 'live' ? 'success' : state === 'waiting' ? 'warning' : 'subtle'
}

function text(result: string) {
  return { result }
}

export const register: Register = (on) => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'team',
      description: 'Your brain agent team: open the pane, message an agent, or stop everything',
      argumentHint: '[send <agent> <message> | follow [on|off] | stop | hub]',
    })
    await $.tool.register({
      name: 'start_team',
      description: "Start a team of brain agents from a template on one of the user's projects. Templates: "
        + (await templateList($)) + '. The lead\'s first reply is delivered back here automatically; do not wait or poll.',
      inputSchema: {
        type: 'object',
        properties: {
          template: { type: 'string' },
          project: { type: 'string', description: 'registered project name, e.g. "Trip Fairy"' },
          prefix: { type: 'string', description: 'agent name prefix; defaults to the project name' },
          scope: { type: 'string', description: "builder's folder(s), relative to the project" },
          test_command: { type: 'string', description: 'pre-approved for builder and reviewer, e.g. "npm test"' },
          task: { type: 'string', description: 'tracker task id for the lead to start on' },
          question: { type: 'string', description: 'for research and debate' },
        },
        required: ['template', 'project'],
      },
      isDeferred: false,
    })
    await $.tool.register({
      name: 'agents',
      description: "List the user's brain team: long-lived Claude Code agents the brain dashboard runs. "
        + 'Shows each agent\'s name, persona, state, model and usage, plus actions waiting on the user.',
      isDeferred: false,
    })
    await $.tool.register({
      name: 'send',
      description: 'Send a message to one agent on the user\'s brain team (see mcp__team__agents). '
        + 'The reply is delivered back into this conversation automatically when it is ready: do not wait or poll for it.',
      inputSchema: {
        type: 'object',
        properties: { agent: { type: 'string' }, text: { type: 'string' } },
        required: ['agent', 'text'],
      },
      isDeferred: false,
    })
    await $.tool.register({
      name: 'read',
      description: "Read an agent's recent conversation on the user's brain team (messages, tool calls, replies).",
      inputSchema: {
        type: 'object',
        properties: { agent: { type: 'string' }, limit: { type: 'number', description: 'messages, default 20' } },
        required: ['agent'],
      },
    })
    await poll($) // a local request: answers or fails at once, so the first draw has data
    $.clock.every(POLL_MS, () => tick($))

    return next(e)
  })

  on('command.run', { command: 'team' }, async ($, e) => {
    const args = e.args.trim()
    try {
      if (!args) {
        await $.ui.open({ id: PANE, title: 'Team' })
        await poll($)
        return {
          text: (await read($, onlineAtom))
            ? summary(await read($, agentsAtom), await read($, holdsAtom))
            : `The brain dashboard isn't reachable at ${BASE}. Start it with ./voice/.venv/bin/python -m dashboard.server`,
        }
      }
      const m = args.match(/^send\s+(\S+)\s+([\s\S]+)$/)
      if (m) return { text: await send($, m[1] ?? '', m[2] ?? '') }
      if (args === 'stop') return { text: await stopAll($) }
      const f = args.match(/^follow(?:\s+(on|off))?$/)
      if (f) return { text: await setFollow($, f[1] !== 'off') }
      if (args === 'hub') return { text: `Team view: ${HUB}` }
      return { text: 'Usage: /team · /team send <agent> <message> · /team follow [on|off] · /team stop · /team hub' }
    } catch (err) {
      return { text: `Team: ${(err as Error).message}` }
    }
  })

  on('tool.call', { tool: 'mcp__team__agents' }, async ($) => {
    try {
      await poll($)
      const agents = await read($, agentsAtom)
      const holds = await read($, holdsAtom)
      if (!(await read($, onlineAtom))) return text(`The brain dashboard isn't running (${BASE}).`)
      const rows = agents.map((a) => `- ${a.name} (${a.persona}, ${a.state}, ${a.model}${a.team ? `, team ${a.team}` : ''})`)
      const waiting = holds.map((hold) => `- ${hold.agent} wants to ${KIND[hold.kind] || hold.kind}: ${hold.what}`)
      return text([summary(agents, holds), ...rows, ...(waiting.length ? ['Waiting on the user:', ...waiting] : [])].join('\n'))
    } catch (err) {
      return { deny: (err as Error).message }
    }
  })

  on('tool.call', { tool: 'mcp__team__send' }, async ($, e) => {
    const input = e as unknown as { agent?: string; text?: string } // a tool's arguments sit on the event
    try {
      return text(await send($, String(input.agent || ''), String(input.text || '')))
    } catch (err) {
      return { deny: (err as Error).message }
    }
  })

  on('tool.call', { tool: 'mcp__team__start_team' }, async ($, e) => {
    try {
      return text(await startTeam($, e as unknown as StartArgs))
    } catch (err) {
      return { deny: (err as Error).message }
    }
  })

  on('tool.call', { tool: 'mcp__team__read' }, async ($, e) => {
    const input = e as unknown as { agent?: string; limit?: number }
    const limit = Math.max(1, Math.min(Number(input.limit) || 20, 100))
    try {
      const msgs: any[] = await api($, `/api/harness/agents/${encodeURIComponent(String(input.agent || ''))}/messages?limit=${limit}`)
      return text(msgs.map((m) => `[${m.role}${m.sender && m.role === 'user' ? ` from ${m.sender}` : ''}] ${m.text}`).join('\n\n') || 'No messages yet.')
    } catch (err) {
      return { deny: (err as Error).message }
    }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Button, Text, Link } = $.ui.resolve(e)
    const online = await read($, onlineAtom)
    const agents = await read($, agentsAtom)
    const holds = await read($, holdsAtom)
    if (!online) {
      return (
        <Box flexDirection="column" gap={1}>
          <Text color="warning">The brain dashboard isn't reachable at {BASE}.</Text>
          <Text dimColor>Start it with ./voice/.venv/bin/python -m dashboard.server</Text>
        </Box>
      )
    }

    return (
      <Box flexDirection="column" gap={1}>
        <Text dimColor>{summary(agents, holds)}{(await read($, followAtom)).on ? ' · following' : ''}</Text>
        {holds.map((hold) => (
          <Box flexDirection="column">
            <Text color={/destructive|push/.test(hold.kind) ? 'error' : 'warning'}>
              {hold.agent} wants to {KIND[hold.kind] || hold.kind}
            </Text>
            <Text bold>{hold.what}</Text>
            <Box flexDirection="row" gap={1}>
              <Button key={`allow-${hold.id}`} label="Allow" onPress={() => decide($, hold, true)} />
              {hold.kind === 'command' && (
                <Button key={`always-${hold.id}`} label="Always" onPress={() => decide($, hold, true, true)} />
              )}
              <Button key={`deny-${hold.id}`} label="Deny" onPress={() => decide($, hold, false)} />
            </Box>
          </Box>
        ))}
        <Box flexDirection="column">
          {agents.length === 0 && <Text dimColor>No agents yet. Start a team in the Hub.</Text>}
          {agents.map((a) => (
            <Text>
              <Text color={stateColor(a.state)}>● </Text>
              {a.name} <Text dimColor>{a.state} · {a.model} · ${a.usage.toFixed(2)} of ${a.cap}{a.queued ? ` · ${a.queued} queued` : ''}</Text>
            </Text>
          ))}
        </Box>
        <Box flexDirection="row" gap={1}>
          <Button key="stop" label="Stop everything" onPress={() => stopAll($)} />
          <Link href={HUB} label="Open the Hub" />
        </Box>
      </Box>
    )
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const holds = await read($, holdsAtom)
    const first = holds[0]
    if (e.props.hasSurvey || !first) return next(e)
    const { Box, Button, Text } = $.ui.resolve(e)

    return (
      <Box flexDirection="row" gap={1}>
        <Text color="warning">
          {first.agent} wants to {KIND[first.kind] || first.kind}: {first.what}
          {holds.length > 1 ? ` (+${holds.length - 1} more in /team)` : ''}
        </Text>
        <Button key={`band-allow-${first.id}`} label="Allow" onPress={() => decide($, first, true)} />
        <Button key={`band-deny-${first.id}`} label="Deny" onPress={() => decide($, first, false)} />
      </Box>
    )
  })
}
