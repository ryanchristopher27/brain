/** One harness agent, as the pane and band draw it. */
export type Agent = {
  name: string
  persona: string
  state: string
  model: string
  usage: number
  cap: number
  team: string | null
  queued: number
}

/** A tool call an agent is waiting on the user to allow or deny. */
export type Hold = { id: number; agent: string; kind: string; what: string; reason: string }

/**
 * A message this session sent to an agent. Its first reply starts a turn here; later messages from
 * that agent in the thread (a team lead's final report) arrive quietly. `after` is the last id
 * delivered, `at` the last activity (asks expire a while after it).
 */
export type Ask = { agent: string; id: number; thread: string; at: number; replied: boolean; after: number }

/** `/team follow`: forward what any agent tells the user into this session, from message `after` on. */
export type Follow = { on: boolean; after: number }

declare module 'claude-code' {
  interface PluginState {
    team: { agents: Agent[]; holds: Hold[]; online: boolean; asks: Ask[]; follow: Follow }
  }
}
