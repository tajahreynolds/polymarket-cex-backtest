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

type SpreadPoint = { t: number; spread: number }

export default function LiveDemo() {
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
