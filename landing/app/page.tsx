import LiveDemo from './components/LiveDemo'
import FreeKeyForm from './components/FreeKeyForm'
import CheckoutButton from './components/CheckoutButton'
import Faq from './components/Faq'

// ─── Constants ───────────────────────────────────────────────────────────────

const SAMPLE_RESPONSE = `{
  "spread":     0.0283,
  "direction":  "buy",
  "edge_bps":   198,
  "confidence": 0.87,
  "ts":         "2026-05-20T14:32:01Z"
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

type PricingTier = {
  name: string
  price: string
  signals: string
  protocols: string[]
  extras: string[]
  highlight: boolean
  bestValue?: boolean
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
    bestValue: true,
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
        className="es-btn-accent"
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
          className="es-btn-accent"
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
          href="/docs"
          className="es-btn-outline"
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
          overflow: 'visible',
          marginTop: '1.75rem',
        }}
      >
        {TIERS.map((tier, idx) => (
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
              borderRadius: idx === 0 ? '5px 0 0 5px' : idx === TIERS.length - 1 ? '0 5px 5px 0' : undefined,
            }}
          >
            {tier.bestValue && (
              <div
                style={{
                  position: 'absolute',
                  top: '-1.75rem',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  height: '1.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: 'var(--accent)',
                  color: '#040a04',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '0.625rem',
                  fontWeight: 700,
                  letterSpacing: '0.14em',
                  textTransform: 'uppercase',
                  padding: '0 0.75rem',
                  whiteSpace: 'nowrap',
                  borderRadius: '3px 3px 0 0',
                }}
              >
                ★ Best Value
              </div>
            )}
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
        href="mailto:contact@mineexi.resend.app"
        style={{
          fontSize: '0.8125rem',
          color: 'var(--muted)',
          textDecoration: 'none',
          fontFamily: 'JetBrains Mono, monospace',
        }}
      >
        contact@mineexi.resend.app
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
