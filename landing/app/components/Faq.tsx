'use client'

import { useState } from 'react'

type FaqItem = { q: string; a: string }

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
    a: "Basis points of expected profit after accounting for Polymarket taker fees (2%), estimated slippage on the exit leg, and our model's confidence discount. 100 bps = 1%.",
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

export default function Faq() {
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
