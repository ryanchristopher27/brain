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

/** A message this session sent to an agent, whose reply is delivered back here. */
export type Ask = { agent: string; id: number; thread: string; at: number }

declare module 'claude-code' {
  interface PluginState {
    team: { agents: Agent[]; holds: Hold[]; online: boolean; asks: Ask[] }
  }
}
