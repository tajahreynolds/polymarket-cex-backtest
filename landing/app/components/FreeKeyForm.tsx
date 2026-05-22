'use client'

import { useState } from 'react'

type FormState = 'idle' | 'loading' | 'success' | 'error'

export default function FreeKeyForm() {
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
        className={state === 'loading' ? undefined : 'es-btn-ghost'}
        style={{
          background: 'transparent',
          color: 'var(--text)',
          fontWeight: 600,
          fontSize: '0.8125rem',
          padding: '0.55rem 0',
          borderRadius: '4px',
          border: '1px solid #2a2a2a',
          cursor: state === 'loading' ? 'not-allowed' : 'pointer',
          fontFamily: 'Inter, sans-serif',
          opacity: state === 'loading' ? 0.5 : 1,
        }}
      >
        {state === 'loading' ? 'Sending...' : 'Get Free Key'}
      </button>
    </form>
  )
}
