export type Tier = 'light' | 'standard' | 'deep'
export type Mode = 'auto' | 'off' | Tier
/** The routing decided for the current turn. `model` absent means the session's own. */
export type Route = { tier: Tier; why: string; model?: string; effort?: string }

declare module 'claude-code' {
  interface PluginState {
    'model-router': { mode: Mode; last: Route | null }
  }
}
