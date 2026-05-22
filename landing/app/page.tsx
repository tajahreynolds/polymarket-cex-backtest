'use client'

import { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

// ─── Types ───────────────────────────────────────────────────────────────────

type SpreadPoint = { t: number; spread: number }
type FaqItem = { q: string; a: string }

// ─── Constants ───────────────────────────────────────────────────────────────

const SAMPLE_RESPONSE = `{
  "contract": "BTC-25MAY2026-YES",
  "timestamp": "2026-05-20T14:32:01Z",
  "polymarket_prob": 0.6821,
  "binance_implied_prob": 0.7104,
  "spread_bps": 283,
  "edge_bps": 198,
  "direction": "LONG",
  "confidence": 0.87
}`

const FEATURES = [
  {
    title: 'CEX-Calibrated',
    body:
      'Every signal cross-references Polymarket implied probability against live Binance spot price. No guess-work means real price discovery anchors each edge estimate.',
  },
  {
    title: 'Sub-second latency',
    body:
      'WebSocket stream pushes signals within 300 ms of a Binance tick or Polymarket book change. Pro tier subscribers get the raw feed; Core gets SSE.',
  },
  {
    title: '98.5% gross margin infra',
    body:
      'We run the quant engine, the data pipeline, and the feed aggregation. You focus on the trade. No servers to babysit, no Binance API keys to manage.',
  },
]

const FAQ_ITEMS: FaqItem[] = [
  {
    q: 'How is this different from Prediction Hunt?',
    a: 'Prediction Hunt aggregates crowd sentiment. EdgeSignal cross-references live CEX price data (Binance spot) to derive an implied probability anchored to real-world derivatives markets. The spread between those two numbers is your edge.',
  },
  {
    q: 'What contracts do you cover?',
    a: 'Currently BTC up/down on Polymarket (the monthly settlement contracts). ETH and SOL coverage coming soon. Signal volume scales with Binance liquidity, so BTC is the natural starting point.',
  },
  {
    q: "What does 'edge_bps' mean?",
    a: "Basis points of expected profit after accounting for Polymarket taker fees (2%), estimated slippage on the exit leg, and our model's confidence discount. 100 bps = 1%. Anything above 150 bps is considered a high-conviction signal.",
  },
  {
    q: 'How do I authenticate?',
    a: 'Pass your API key as a Bearer token in the Authorization header: Authorization: Bearer <your_key>. Keys are issued immediately on signup. Free tier keys work on REST endpoints; Core and Pro unlock SSE and WebSocket.',
  },
  {
    q: 'Is there a free tier?',
    a: 'Yes. The Free tier gives you 100 signals per day via REST, no credit card required. It covers all current BTC up/down contracts on polymarket so you can validate the signal quality before upgrading.',
  },
  {
    q: "Can't I just build this myself?",
    a: "Yes, and you should! The core idea is a 40-line Go script. What takes months is the production infrastructure: reconnect logic for both WebSockets, a conversion model that handles low-liquidity Binance periods without blowing up, fee/slippage calibration that doesn't over-state edge, and keeping it running at 3am when Polymarket restarts its CLOB. Free tier exists so you can compare your build against ours before paying.",
  },
]

// ─── Sub-components ───────────────────────────────────────────────────────────

function Nav() {
  return (
    <nav
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 2rem',
        height: '56px',
        borderBottom: '1px solid #1f1f1f',
        background: 'var(--surface)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <span
        className="mono"
        style={{ fontWeight: 500, fontSize: '1rem', letterSpacing: '-0.01em' }}
      >
        EdgeSignal
      </span>
      <a
        href="#pricing"
        style={{
          background: 'var(--accent)',
          color: '#000',
          fontFamily: 'Inter, sans-serif',
          fontWeight: 600,
          fontSize: '0.8125rem',
          padding: '0.4rem 1rem',
          borderRadius: '4px',
          textDecoration: 'none',
          display: 'inline-block',
        }}
      >
        Get API Key
      </a>
    </nav>
  )
}

function Hero() {
  return (
    <section
      style={{
        maxWidth: '760px',
        margin: '0 auto',
        padding: '5rem 2rem 3rem',
      }}
    >
      <h1
        style={{
          fontWeight: 600,
          fontSize: 'clamp(1.75rem, 4vw, 2.5rem)',
          lineHeight: 1.2,
          letterSpacing: '-0.02em',
          marginBottom: '1.25rem',
        }}
      >
        Polymarket is mispriced right now. Binance knows by how much.
      </h1>
      <p
        style={{
          color: 'var(--muted)',
          fontSize: '1.0625rem',
          lineHeight: 1.65,
          maxWidth: '600px',
          marginBottom: '2rem',
        }}
      >
        Every Polymarket contract has a shadow price on Binance. EdgeSignal
        measures the gap in real time, telling you when it&apos;s big enough
        to trade.
      </p>

      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '3rem' }}>
        <a
          href="#pricing"
          style={{
            background: 'var(--accent)',
            color: '#000',
            fontWeight: 600,
            fontSize: '0.875rem',
            padding: '0.6rem 1.25rem',
            borderRadius: '4px',
            textDecoration: 'none',
          }}
        >
          Get Free API Key
        </a>
        <a
          href="#"
          style={{
            background: 'transparent',
            color: 'var(--text)',
            fontWeight: 600,
            fontSize: '0.875rem',
            padding: '0.6rem 1.25rem',
            borderRadius: '4px',
            border: '1px solid #2a2a2a',
            textDecoration: 'none',
          }}
        >
          View Docs
        </a>
      </div>

      {/* Terminal block */}
      <div
        style={{
          background: 'var(--surface-alt)',
          border: '1px solid #1f1f1f',
          borderRadius: '6px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            padding: '0.5rem 1rem',
            borderBottom: '1px solid #1f1f1f',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <span style={{ color: 'var(--muted)', fontSize: '0.75rem', fontFamily: 'JetBrains Mono, monospace' }}>
            GET /v1/signal/BTC-25MAY2026-YES
          </span>
        </div>
        <pre
          className="mono"
          style={{
            padding: '1.25rem 1.5rem',
            fontSize: '0.8125rem',
            lineHeight: 1.7,
            color: 'var(--text)',
            overflowX: 'auto',
          }}
        >
          {SAMPLE_RESPONSE}
        </pre>
      </div>
    </section>
  )
}

function LiveDemo() {
  const [data, setData] = useState<SpreadPoint[]>([])

  useEffect(() => {
    const points: SpreadPoint[] = Array.from({ length: 20 }, (_, i) => ({
      t: i,
      spread: Math.round(120 + (Math.random() - 0.4) * 240),
    }))
    setData(points)
  }, [])

  return (
    <section
      style={{
        maxWidth: '760px',
        margin: '0 auto',
        padding: '2rem 2rem 3rem',
      }}
    >
      <p
        style={{
          color: 'var(--muted)',
          fontSize: '0.75rem',
          fontFamily: 'JetBrains Mono, monospace',
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          marginBottom: '0.75rem',
        }}
      >
        Live Spread — BTC-Yes vs Binance Implied Prob
      </p>
      <div
        style={{
          background: 'var(--surface-alt)',
          border: '1px solid #1f1f1f',
          borderRadius: '6px',
          padding: '1.5rem 1rem 1rem',
          height: '220px',
        }}
      >
        {data.length > 0 && (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 4, right: 8, left: -24, bottom: 0 }}>
              <CartesianGrid stroke="#1a1a1a" strokeDasharray="3 3" />
              <XAxis dataKey="t" hide />
              <YAxis
                tick={{ fill: '#555555', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: 'var(--surface-raised)',
                  border: '1px solid #2a2a2a',
                  borderRadius: '4px',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '0.75rem',
                  color: 'var(--text)',
                }}
                labelFormatter={() => ''}
                formatter={(v: number) => [`${v} bps`, 'spread']}
              />
              <Line
                type="monotone"
                dataKey="spread"
                stroke="#22c55e"
                strokeWidth={1.5}
                dot={false}
                activeDot={{ r: 3, fill: '#22c55e' }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  )
}

function Features() {
  return (
    <section
      style={{
        maxWidth: '760px',
        margin: '0 auto',
        padding: '1rem 2rem 3rem',
      }}
    >
      <h2
        style={{
          fontWeight: 600,
          fontSize: '1.25rem',
          marginBottom: '1.5rem',
          letterSpacing: '-0.01em',
        }}
      >
        Why EdgeSignal
      </h2>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1px',
          background: '#1f1f1f',
          border: '1px solid #1f1f1f',
          borderRadius: '6px',
          overflow: 'hidden',
        }}
      >
        {FEATURES.map((f) => (
          <div
            key={f.title}
            style={{
              background: 'var(--surface-alt)',
              padding: '1.5rem',
            }}
          >
            <h3
              style={{
                fontWeight: 600,
                fontSize: '0.9375rem',
                marginBottom: '0.5rem',
                letterSpacing: '-0.01em',
              }}
            >
              {f.title}
            </h3>
            <p style={{ color: 'var(--muted)', fontSize: '0.875rem', lineHeight: 1.6 }}>
              {f.body}
            </p>
          </div>
        ))}
      </div>
    </section>
  )
}

type PricingTier = {
  name: string
  price: string
  signals: string
  protocols: string[]
  extras: string[]
  highlight: boolean
}

const TIERS: PricingTier[] = [
  {
    name: 'Free',
    price: '$0/mo',
    signals: '100 signals/day',
    protocols: ['REST'],
    extras: ['No credit card', 'All BTC-Yes contracts', 'Community support'],
    highlight: false,
  },
  {
    name: 'Core',
    price: '$49/mo',
    signals: '10K signals/day',
    protocols: ['REST', 'SSE'],
    extras: ['Historical data (7 days)', 'Email support', 'SLA 99.5%'],
    highlight: true,
  },
  {
    name: 'Pro',
    price: '$149/mo',
    signals: 'Unlimited',
    protocols: ['REST', 'SSE', 'WebSocket'],
    extras: ['Full history', 'Slack support', 'SLA 99.9%', 'Custom contract coverage'],
    highlight: false,
  },
]

type FormState = 'idle' | 'loading' | 'success' | 'error'

function FreeKeyForm() {
  const [email, setEmail] = useState('')
  const [state, setState] = useState<FormState>('idle')
  const [errMsg, setErrMsg] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setState('loading')
    try {
      const res = await fetch('/api/free-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.error ?? 'Something went wrong')
      }
      setState('success')
    } catch (err: unknown) {
      setErrMsg(err instanceof Error ? err.message : 'Something went wrong')
      setState('error')
    }
  }

  if (state === 'success') {
    return (
      <p style={{ color: 'var(--accent)', fontSize: '0.8125rem', fontFamily: 'JetBrains Mono, monospace' }}>
        Check your email ✓
      </p>
    )
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <input
        type="email"
        required
        placeholder="you@company.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        style={{
          background: 'var(--surface)',
          border: '1px solid #2a2a2a',
          borderRadius: '4px',
          color: 'var(--text)',
          fontFamily: 'Inter, sans-serif',
          fontSize: '0.8125rem',
          padding: '0.45rem 0.75rem',
          outline: 'none',
          width: '100%',
          boxSizing: 'border-box',
        }}
      />
      {state === 'error' && (
        <p style={{ color: '#ef4444', fontSize: '0.75rem', margin: 0 }}>{errMsg}</p>
      )}
      <button
        type="submit"
        disabled={state === 'loading'}
        style={{
          background: 'transparent',
          color: 'var(--muted)',
          fontWeight: 600,
          fontSize: '0.8125rem',
          padding: '0.55rem 0',
          borderRadius: '4px',
          border: '1px solid #1f1f1f',
          cursor: state === 'loading' ? 'not-allowed' : 'pointer',
          fontFamily: 'Inter, sans-serif',
        }}
      >
        {state === 'loading' ? 'Sending...' : 'Get Free Key'}
      </button>
    </form>
  )
}

function CheckoutButton({ tier, highlight }: { tier: 'core' | 'pro'; highlight: boolean }) {
  const [loading, setLoading] = useState(false)
  const label = tier === 'core' ? 'Subscribe — $49/mo' : 'Subscribe — $149/mo'

  async function handleClick() {
    setLoading(true)
    try {
      const res = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier }),
      })
      const data = await res.json()
      if (data.url) window.location.href = data.url
    } catch {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      style={{
        display: 'block',
        width: '100%',
        textAlign: 'center',
        background: highlight ? 'var(--accent)' : 'var(--surface-raised)',
        color: highlight ? '#000' : 'var(--text)',
        fontWeight: 600,
        fontSize: '0.8125rem',
        padding: '0.55rem 0',
        borderRadius: '4px',
        border: highlight ? 'none' : '1px solid #2a2a2a',
        cursor: loading ? 'not-allowed' : 'pointer',
        fontFamily: 'Inter, sans-serif',
        opacity: loading ? 0.7 : 1,
      }}
    >
      {loading ? 'Loading...' : label}
    </button>
  )
}

function Pricing() {
  return (
    <section
      id="pricing"
      style={{
        maxWidth: '760px',
        margin: '0 auto',
        padding: '1rem 2rem 3rem',
      }}
    >
      <h2
        style={{
          fontWeight: 600,
          fontSize: '1.25rem',
          marginBottom: '1.5rem',
          letterSpacing: '-0.01em',
        }}
      >
        Pricing
      </h2>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1px',
          background: '#1f1f1f',
          border: '1px solid #1f1f1f',
          borderRadius: '6px',
          overflow: 'hidden',
        }}
      >
        {TIERS.map((tier) => (
          <div
            key={tier.name}
            style={{
              background: 'var(--surface-alt)',
              padding: '1.5rem',
              outline: tier.highlight ? '1px solid #2a3a2a' : undefined,
              outlineOffset: tier.highlight ? '-1px' : undefined,
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {tier.highlight && (
              <span
                style={{
                  position: 'absolute',
                  top: '1rem',
                  right: '1rem',
                  fontSize: '0.6875rem',
                  fontFamily: 'JetBrains Mono, monospace',
                  color: 'var(--accent)',
                  letterSpacing: '0.06em',
                  textTransform: 'uppercase',
                }}
              >
                recommended
              </span>
            )}
            <div
              style={{
                fontWeight: 600,
                fontSize: '0.9375rem',
                marginBottom: '0.25rem',
                letterSpacing: '-0.01em',
              }}
            >
              {tier.name}
            </div>
            <div
              className="mono"
              style={{
                fontSize: '1.5rem',
                fontWeight: 500,
                marginBottom: '1rem',
                color: 'var(--text)',
              }}
            >
              {tier.price}
            </div>
            <ul style={{ listStyle: 'none', marginBottom: '1.25rem', flex: 1 }}>
              <li
                style={{
                  fontSize: '0.875rem',
                  color: 'var(--muted)',
                  marginBottom: '0.35rem',
                  paddingLeft: '1rem',
                  position: 'relative',
                }}
              >
                <span style={{ position: 'absolute', left: 0, color: 'var(--accent)' }}>›</span>
                {tier.signals}
              </li>
              {tier.protocols.map((p) => (
                <li
                  key={p}
                  style={{
                    fontSize: '0.875rem',
                    color: 'var(--muted)',
                    marginBottom: '0.35rem',
                    paddingLeft: '1rem',
                    position: 'relative',
                  }}
                >
                  <span style={{ position: 'absolute', left: 0, color: 'var(--accent)' }}>›</span>
                  {p}
                </li>
              ))}
              {tier.extras.map((e) => (
                <li
                  key={e}
                  style={{
                    fontSize: '0.875rem',
                    color: 'var(--muted)',
                    marginBottom: '0.35rem',
                    paddingLeft: '1rem',
                    position: 'relative',
                  }}
                >
                  <span style={{ position: 'absolute', left: 0, color: 'var(--muted)' }}>›</span>
                  {e}
                </li>
              ))}
            </ul>
            {tier.name === 'Free' ? (
              <FreeKeyForm />
            ) : (
              <CheckoutButton
                tier={tier.name.toLowerCase() as 'core' | 'pro'}
                highlight={tier.highlight}
              />
            )}
          </div>
        ))}
      </div>
    </section>
  )
}

function Faq() {
  const [open, setOpen] = useState<number | null>(null)

  return (
    <section
      style={{
        maxWidth: '760px',
        margin: '0 auto',
        padding: '1rem 2rem 4rem',
      }}
    >
      <h2
        style={{
          fontWeight: 600,
          fontSize: '1.25rem',
          marginBottom: '1.5rem',
          letterSpacing: '-0.01em',
        }}
      >
        FAQ
      </h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1px', background: '#1f1f1f', border: '1px solid #1f1f1f', borderRadius: '6px', overflow: 'hidden' }}>
        {FAQ_ITEMS.map((item, i) => (
          <div key={i} style={{ background: 'var(--surface-alt)' }}>
            <button
              onClick={() => setOpen(open === i ? null : i)}
              style={{
                width: '100%',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '1rem 1.25rem',
                background: 'transparent',
                border: 'none',
                color: 'var(--text)',
                fontFamily: 'Inter, sans-serif',
                fontWeight: 600,
                fontSize: '0.9rem',
                textAlign: 'left',
                cursor: 'pointer',
              }}
            >
              <span>{item.q}</span>
              <span
                className="mono"
                style={{
                  fontSize: '1rem',
                  color: 'var(--muted)',
                  marginLeft: '1rem',
                  flexShrink: 0,
                  userSelect: 'none',
                }}
              >
                {open === i ? '−' : '+'}
              </span>
            </button>
            {open === i && (
              <p
                style={{
                  padding: '0 1.25rem 1rem',
                  color: 'var(--muted)',
                  fontSize: '0.875rem',
                  lineHeight: 1.65,
                }}
              >
                {item.a}
              </p>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer
      style={{
        borderTop: '1px solid #1f1f1f',
        padding: '1.5rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '0.5rem',
        maxWidth: '760px',
        margin: '0 auto',
      }}
    >
      <span
        className="mono"
        style={{ fontSize: '0.8125rem', color: 'var(--muted)' }}
      >
        EdgeSignal &copy; 2026
      </span>
      <a
        href="mailto:contact@edgesignal.io"
        style={{
          fontSize: '0.8125rem',
          color: 'var(--muted)',
          textDecoration: 'none',
          fontFamily: 'JetBrains Mono, monospace',
        }}
      >
        contact@edgesignal.io
      </a>
    </footer>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Page() {
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <LiveDemo />
        <Features />
        <Pricing />
        <Faq />
      </main>
      <Footer />
    </>
  )
}
