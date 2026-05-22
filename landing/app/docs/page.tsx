import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Docs — EdgeSignal',
  description: 'EdgeSignal API reference: authentication, endpoints, response schema, rate limits.',
}

const BASE_URL = 'https://micro-arb-production.up.railway.app'

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} style={{ marginBottom: '3rem' }}>
      <h2
        style={{
          fontWeight: 600,
          fontSize: '1.125rem',
          letterSpacing: '-0.01em',
          marginBottom: '1rem',
          paddingBottom: '0.5rem',
          borderBottom: '1px solid #1f1f1f',
        }}
      >
        {title}
      </h2>
      {children}
    </section>
  )
}

const TIER_STYLES: Record<string, { bg: string; color: string; border: string }> = {
  'Core+': { bg: '#0e2a1a', color: '#4ade80', border: '#1a4a2a' },
  'Pro':   { bg: '#1a1a2e', color: '#818cf8', border: '#2a2a4a' },
}

function TierTag({ tier }: { tier: 'Core+' | 'Pro' }) {
  const s = TIER_STYLES[tier]
  return (
    <span
      style={{
        display: 'inline-block',
        background: s.bg,
        color: s.color,
        border: `1px solid ${s.border}`,
        borderRadius: '3px',
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: '0.625rem',
        fontWeight: 700,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        padding: '0.15em 0.5em',
        verticalAlign: 'middle',
        marginLeft: '0.5rem',
        lineHeight: 1.6,
      }}
    >
      {tier}
    </span>
  )
}

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code
      style={{
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: '0.8125rem',
        background: '#1a1a1a',
        border: '1px solid #2a2a2a',
        borderRadius: '3px',
        padding: '0.1em 0.4em',
        color: 'var(--text)',
      }}
    >
      {children}
    </code>
  )
}

function Block({ label, children }: { label?: string; children: string }) {
  return (
    <div
      style={{
        background: 'var(--surface-alt)',
        border: '1px solid #1f1f1f',
        borderRadius: '6px',
        overflow: 'hidden',
        marginBottom: '1rem',
      }}
    >
      {label && (
        <div
          style={{
            padding: '0.4rem 1rem',
            borderBottom: '1px solid #1f1f1f',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '0.75rem',
            color: 'var(--muted)',
          }}
        >
          {label}
        </div>
      )}
      <pre
        style={{
          margin: 0,
          padding: '1rem 1.25rem',
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: '0.8125rem',
          lineHeight: 1.7,
          color: 'var(--text)',
          overflowX: 'auto',
        }}
      >
        {children}
      </pre>
    </div>
  )
}

function TableRow({ cells, header }: { cells: string[]; header?: boolean }) {
  const Tag = header ? 'th' : 'td'
  return (
    <tr>
      {cells.map((c, i) => (
        <Tag
          key={i}
          style={{
            padding: '0.6rem 1rem',
            textAlign: 'left',
            fontSize: '0.875rem',
            color: header ? 'var(--muted)' : 'var(--text)',
            fontWeight: header ? 600 : 400,
            borderBottom: '1px solid #1f1f1f',
            fontFamily: i === 0 ? 'JetBrains Mono, monospace' : 'Inter, sans-serif',
            whiteSpace: i === 0 ? 'nowrap' : undefined,
          }}
        >
          {c}
        </Tag>
      ))}
    </tr>
  )
}

function Table({ headers, rows }: { headers: string[]; rows: string[][] }) {
  return (
    <div style={{ border: '1px solid #1f1f1f', borderRadius: '6px', overflow: 'hidden', marginBottom: '1rem' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead style={{ background: 'var(--surface-alt)' }}>
          <TableRow cells={headers} header />
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <TableRow key={i} cells={r} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function DocsPage() {
  return (
    <>
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
        <Link
          href="/"
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontWeight: 500,
            fontSize: '1rem',
            letterSpacing: '-0.01em',
            textDecoration: 'none',
            color: 'var(--text)',
          }}
        >
          EdgeSignal
        </Link>
        <Link
          href="/#pricing"
          style={{
            background: 'var(--accent)',
            color: '#000',
            fontFamily: 'Inter, sans-serif',
            fontWeight: 600,
            fontSize: '0.8125rem',
            padding: '0.4rem 1rem',
            borderRadius: '4px',
            textDecoration: 'none',
          }}
        >
          Get API Key
        </Link>
      </nav>

      <main style={{ maxWidth: '760px', margin: '0 auto', padding: '3rem 2rem 5rem' }}>
        <h1
          style={{
            fontWeight: 600,
            fontSize: '1.75rem',
            letterSpacing: '-0.02em',
            marginBottom: '0.5rem',
          }}
        >
          API Reference
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: '0.9375rem', lineHeight: 1.6, marginBottom: '3rem' }}>
          Base URL: <Code>{BASE_URL}</Code>
        </p>

        <Section id="authentication" title="Authentication">
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem', lineHeight: 1.65, marginBottom: '1rem' }}>
            Pass your API key as a Bearer token on every request.
          </p>
          <Block label="HTTP header">
            {`Authorization: Bearer <your_api_key>`}
          </Block>
          <p style={{ color: 'var(--muted)', fontSize: '0.875rem', lineHeight: 1.65 }}>
            Keys are issued immediately on signup — no OAuth, no dashboard. Free tier keys work on REST endpoints only.
            Core and Pro unlock SSE and WebSocket.
          </p>
        </Section>

        <Section id="endpoints" title="Endpoints">
          <p style={{ color: 'var(--muted)', fontSize: '0.875rem', marginBottom: '1.25rem', lineHeight: 1.65 }}>
            All endpoints return JSON. Timestamps are ISO 8601 UTC.
          </p>

          <h3 style={{ fontWeight: 600, fontSize: '0.9375rem', marginBottom: '0.5rem' }}>
            GET /v1/signals/latest
          </h3>
          <p style={{ color: 'var(--muted)', fontSize: '0.875rem', lineHeight: 1.65, marginBottom: '0.75rem' }}>
            Returns the most recent signal emitted by the engine.
          </p>
          <Block label="curl">
            {`curl -H "Authorization: Bearer <key>" \\
  ${BASE_URL}/v1/signals/latest`}
          </Block>

          <h3 style={{ fontWeight: 600, fontSize: '0.9375rem', marginBottom: '0.5rem', marginTop: '1.5rem' }}>
            GET /v1/signals/stream <TierTag tier="Core+" />
          </h3>
          <p style={{ color: 'var(--muted)', fontSize: '0.875rem', lineHeight: 1.65, marginBottom: '0.75rem' }}>
            Server-Sent Events stream. Pushes a signal object each time the engine emits a new signal.
          </p>
          <Block label="curl">
            {`curl -H "Authorization: Bearer <key>" \\
  -H "Accept: text/event-stream" \\
  ${BASE_URL}/v1/signals/stream`}
          </Block>

          <h3 style={{ fontWeight: 600, fontSize: '0.9375rem', marginBottom: '0.5rem', marginTop: '1.5rem' }}>
            WebSocket <TierTag tier="Pro" />
          </h3>
          <p style={{ color: 'var(--muted)', fontSize: '0.875rem', lineHeight: 1.65, marginBottom: '0.75rem' }}>
            Full-duplex broadcast. Pushes every signal as it is emitted — no per-contract filtering.
          </p>
          <Block label="wscat">
            {`wscat -H "Authorization: Bearer <key>" \\
  -c wss://micro-arb-production.up.railway.app/v1/ws`}
          </Block>
        </Section>

        <Section id="response" title="Response Schema">
          <Block label="example response">
            {`{
  "spread":     0.0283,
  "direction":  "buy",
  "edge_bps":   198,
  "confidence": 0.87,
  "ts":         "2026-05-20T14:32:01Z"
}`}
          </Block>
          <Table
            headers={['Field', 'Type', 'Description']}
            rows={[
              ['spread', 'number', 'Raw probability difference: Polymarket price minus Binance-implied prob. Negative = SHORT signal.'],
              ['direction', 'string', '"buy" = buy Yes on Polymarket, "sell" = sell Yes'],
              ['edge_bps', 'number', 'Expected profit in basis points after fees, slippage, and confidence discount'],
              ['confidence', 'number', 'Model confidence score (0–1). Low-confidence signals are filtered by the engine before reaching the API'],
              ['ts', 'string', 'ISO 8601 UTC — timestamp of the Binance tick that triggered the signal'],
            ]}
          />
        </Section>

        <Section id="rate-limits" title="Rate Limits">
          <Table
            headers={['Tier', 'Signals/day', 'Protocols', 'History']}
            rows={[
              ['Free', '100', 'REST', '—'],
              ['Core — $49/mo', '10,000', 'REST, SSE', '7 days'],
              ['Pro — $149/mo', 'Unlimited', 'REST, SSE, WebSocket', 'Full'],
            ]}
          />
          <p style={{ color: 'var(--muted)', fontSize: '0.875rem', lineHeight: 1.65 }}>
            Every response includes <Code>X-RateLimit-Limit</Code>, <Code>X-RateLimit-Remaining</Code>, and <Code>X-RateLimit-Reset</Code> (Unix epoch, midnight UTC).
            Exceeding the limit returns <Code>429 Too Many Requests</Code>.
          </p>
        </Section>

        <Section id="errors" title="Errors">
          <Table
            headers={['Status', 'error value', 'Meaning']}
            rows={[
              ['401', 'missing api key', 'No Authorization header'],
              ['401', 'invalid api key', 'Key not found or revoked'],
              ['403', 'SSE requires Core or Pro tier', 'Free key on /v1/signals/stream'],
              ['403', 'WebSocket requires Pro tier', 'Non-Pro key on /v1/ws'],
              ['429', 'rate limit exceeded', 'Daily signal quota exhausted'],
              ['500', '—', 'Internal error — retry with exponential backoff'],
            ]}
          />
          <Block label="error response shape">
            {`{ "error": "rate limit exceeded" }`}
          </Block>
        </Section>

        <Section id="changelog" title="Changelog">
          <p style={{ color: 'var(--muted)', fontSize: '0.875rem', lineHeight: 1.65 }}>
            <strong style={{ color: 'var(--text)' }}>2026-05-21</strong> — Initial API release. BTC up/down contracts on Polymarket. REST, SSE, WebSocket.
          </p>
        </Section>
      </main>
    </>
  )
}
