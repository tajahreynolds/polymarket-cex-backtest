import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'EdgeSignal — CEX-Calibrated Prediction Market Signals',
  description: 'Real-time signals comparing Polymarket implied probability against Binance-derived real-world probability. Spread, direction, edge — one API call.',
  openGraph: {
    title: 'EdgeSignal',
    description: 'CEX-calibrated prediction market signal API',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'SoftwareApplication',
              name: 'EdgeSignal',
              description: 'CEX-calibrated prediction market signal API',
              applicationCategory: 'FinanceApplication',
              offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
              operatingSystem: 'Web',
            }),
          }}
        />
      </body>
    </html>
  )
}
