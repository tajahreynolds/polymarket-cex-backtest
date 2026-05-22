'use client'

import { useState } from 'react'

export default function CheckoutButton({ tier, highlight }: { tier: 'core' | 'pro'; highlight: boolean }) {
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
      if (data.url) {
        window.location.href = data.url
      } else {
        setLoading(false)
      }
    } catch {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className={loading ? undefined : highlight ? 'es-btn-accent' : 'es-btn-outline'}
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
