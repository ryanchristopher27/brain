import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Agent, Ask, Hold } from '../types'

// The brain dashboard (dashboard/server.py) hosts the agent harness on localhost. Its token comes
// from /api/config, which only same-machine callers can reach.
const BASE = 'http://127.0.0.1:8766'
const HUB = 'http://localhost:8766/#/team' // the desktop app links only https: and http://localhost
const PANE = 'team'
const POLL_MS = 4000
const ASK_TTL_MS = 30 * 60 * 1000

const agentsAtom = atom({ plugin: 'team', key: 'agents' } as const, [])
const holdsAtom = atom({ plugin: 'team', key: 'holds' } as const, [])
const onlineAtom = atom({ plugin: 'team', key: 'online' } as const, false)
const asksAtom = atom({ plugin: 'team', key: 'asks' } as const, [])

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
  await deliverReplies($)
}

// Replies to messages this session sent arrive as a new turn here, so nothing waits on them.
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
    const reply = msgs.find((m) => m.id > ask.id && m.thread === ask.thread && m.role === 'assistant')
    if (reply) {
      await $.prompt.submit({ text: `Reply from team agent ${ask.agent}:\n\n${reply.text}` })
    } else if (now - ask.at < ASK_TTL_MS) keep.push(ask)
  }
  if (!same(asks, keep)) await update($, asksAtom, () => keep)
}

async function send($: EngineInterface, agent: string, text: string): Promise<string> {
  const rec = await api($, `/api/harness/agents/${encodeURIComponent(agent)}/message`, 'POST', { text })
  const ask: Ask = { agent, id: rec.id, thread: rec.thread, at: await $.clock.now() }
  await update($, asksAtom, (list) => [...list, ask])
  return `Sent to ${agent}. Their reply will arrive in this conversation on its own when it's ready.`
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
      argumentHint: '[send <agent> <message> | stop | hub]',
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
    $.clock.every(POLL_MS, () => poll($))

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
      if (args === 'hub') return { text: `Team view: ${HUB}` }
      return { text: 'Usage: /team · /team send <agent> <message> · /team stop · /team hub' }
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
        <Text dimColor>{summary(agents, holds)}</Text>
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
