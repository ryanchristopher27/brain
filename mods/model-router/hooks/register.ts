import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Mode, Route, Tier } from '../types'
import { CLASSIFIER_RUBRIC, decide } from './classify'

const mode = atom({ plugin: 'model-router', key: 'mode' } as const, 'auto' as Mode)
const last = atom({ plugin: 'model-router', key: 'last' } as const, null as Route | null)
const MODES: readonly Mode[] = ['auto', 'off', 'light', 'standard', 'deep']

/** "claude-haiku-5-5" → "Haiku 5.5"; anything else as given. */
function short(model: string | undefined): string {
  const m = model?.match(/claude-([a-z]+)-(\d+)-(\d+)/)
  if (!m) return model ?? 'session model'
  const [, family = '', major = '', minor = ''] = m
  return `${family.charAt(0).toUpperCase()}${family.slice(1)} ${major}.${minor}`
}

/** The status line entry: which model is answering and why. */
function show($: EngineInterface, r: Route | null, extra = '') {
  $.ui.status(r ? `${short(r.model)} · ${r.tier} (${r.why})${extra ? ` · ${extra}` : ''}` : undefined)
}

export const register: Register = (on, options) => {
  const cfg = {
    light: String(options.lightModel || 'claude-haiku-5-5'),
    deep: String(options.deepModel || 'claude-opus-5-5'),
    standard: String(options.standardModel || ''),  // "" = whatever /model is set to
    deepEffort: String(options.deepEffort || 'high'),
    classifier: options.classifier !== false,
    // Prompt caching is per model: on a long conversation, uncached input on the cheap
    // model can cost more than cached input on the session's. Past this, don't downshift.
    maxLightMessages: Number(options.maxLightMessages) || 80,
    // A light turn still working after this many requests has hit something harder.
    escalateAfterSteps: Number(options.escalateAfterSteps) || 12,
  }
  const routeFor = (tier: Tier, why: string): Route =>
    tier === 'light' ? { tier, why, model: cfg.light, effort: 'low' }
      : tier === 'deep' ? { tier, why, model: cfg.deep, effort: cfg.deepEffort }
        : { tier, why, model: cfg.standard || undefined }

  let current: Route | null = null
  let previous: Tier = 'standard'
  let note = ''  // why a light turn went back up, shown once per turn


  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'route', description: 'Model routing: /route [auto|off|light|standard|deep]' })
    return next(e)
  })

  on('prompt.submit', async ($, e, next) => {
    if (e.turnId) return next(e)  // typed into a running turn: that turn keeps its route
    const m = await read($, mode)
    const d = decide(e.text, previous)
    let tier: Tier, why: string
    if (m === 'off') { tier = 'standard'; why = 'routing off' }
    else if (m !== 'auto') { tier = m; why = `/route ${m}` }
    else if (d.tier) { tier = d.tier; why = d.why }
    else if (cfg.classifier) {
      // One tiny completion on the light model; any failure just means "standard".
      const res = await $.model.complete({ model: cfg.light, system: CLASSIFIER_RUBRIC, prompt: e.text.slice(0, 4000),
        maxTokens: 5, timeoutMs: 5000 }).catch(() => null)
      const label = res && res.isAnswered ? res.text.toLowerCase().match(/\b(light|standard|deep)\b/)?.[1] as Tier | undefined : undefined
      tier = label ?? 'standard'
      why = label ? 'classified' : 'default'
    } else { tier = 'standard'; why = 'default' }

    previous = tier
    current = m === 'off' ? null : routeFor(tier, why)
    note = ''
    await update($, last, () => current)
    show($, current)
    return next(d.text !== undefined ? { ...e, text: d.text } : e)
  })

  // Every request of the main loop's turn goes to the turn's model. Subagents keep theirs.
  on('turn.step', async function* ($, e, next) {
    const r = current
    if (e.agentId || !r || !r.model) return yield* next(e)
    if (r.tier === 'light') {
      const reason = e.messageCount > cfg.maxLightMessages ? 'long conversation, kept on session model'
        : e.index >= cfg.escalateAfterSteps ? `escalated after ${cfg.escalateAfterSteps} steps` : ''
      if (reason) {
        if (note !== reason) { note = reason; show($, { ...r, model: cfg.standard || undefined }, reason) }
        return yield* next(cfg.standard ? { ...e, model: cfg.standard } : e)
      }
    }
    return yield* next({ ...e, model: r.model, ...(r.effort ? { effort: r.effort as typeof e.effort } : {}) })
  })

  on('command.run', { command: 'route' }, async ($, e) => {
    const arg = e.args.trim().toLowerCase()
    if (arg) {
      if (!MODES.includes(arg as Mode)) return { text: `Unknown mode "${arg}". Use one of: ${MODES.join(', ')}.` }
      await update($, mode, () => arg as Mode)
      if (arg === 'off') { current = null; await update($, last, () => null); show($, null) }
    }
    const m = await read($, mode)
    const r = await read($, last)
    return {
      text: [
        `Routing: ${m}${m === 'auto' ? ' (rules first, classifier when unsure)' : ''}`,
        `light → ${short(cfg.light)} · deep → ${short(cfg.deep)} at ${cfg.deepEffort} effort · standard → ${cfg.standard ? short(cfg.standard) : 'your /model'}`,
        r ? `Last prompt: ${r.tier} (${r.why}) → ${short(r.model)}` : 'No prompt routed yet.',
        'One prompt: start it with !light or !deep. Whole session: /route light|standard|deep, /route auto to go back.',
      ].join('\n'),
    }
  })
}
