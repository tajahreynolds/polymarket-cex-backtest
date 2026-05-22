export default function SuccessPage() {
  return (
    <main
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
      }}
    >
      <div style={{ maxWidth: '480px', textAlign: 'center' }}>
        <div
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '2rem',
            marginBottom: '1.5rem',
            color: 'var(--accent)',
          }}
        >
          ✓
        </div>
        <h1
          style={{
            fontWeight: 600,
            fontSize: '1.5rem',
            letterSpacing: '-0.02em',
            marginBottom: '1rem',
          }}
        >
          You&apos;re in.
        </h1>
        <p
          style={{
            color: 'var(--muted)',
            fontSize: '0.9375rem',
            lineHeight: 1.65,
            marginBottom: '2rem',
          }}
        >
          Your API key is on its way. Check your email — if you don&apos;t see it
          within 5 minutes, check spam or reach out at{' '}
          <a
            href="mailto:contact@edgesignal.io"
            style={{ color: 'var(--text)', textDecoration: 'underline' }}
          >
            contact@edgesignal.io
          </a>
        </p>
        <a
          href="/#pricing"
          style={{
            display: 'inline-block',
            color: 'var(--muted)',
            fontSize: '0.8125rem',
            fontFamily: 'JetBrains Mono, monospace',
            textDecoration: 'none',
            borderBottom: '1px solid #2a2a2a',
          }}
        >
          ← back to pricing
        </a>
      </div>
    </main>
  )
}
