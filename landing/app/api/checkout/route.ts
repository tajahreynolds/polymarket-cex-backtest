import { NextRequest, NextResponse } from 'next/server'
import Stripe from 'stripe'

export async function POST(req: NextRequest) {
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: '2026-04-22.dahlia' })
  let tier: string
  try {
    const body = await req.json()
    tier = body.tier
  } catch {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  }

  if (tier !== 'core' && tier !== 'pro') {
    return NextResponse.json({ error: 'Invalid tier' }, { status: 400 })
  }

  const priceId =
    tier === 'core'
      ? process.env.STRIPE_PRICE_CORE
      : process.env.STRIPE_PRICE_PRO

  if (!priceId) {
    return NextResponse.json({ error: 'Price not configured' }, { status: 500 })
  }

  const origin = (process.env.NEXT_PUBLIC_BASE_URL ?? 'https://edgesignal.io').replace(/\/$/, '')

  const session = await stripe.checkout.sessions.create({
    mode: 'subscription',
    payment_method_types: ['card'],
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: `${origin}/success`,
    cancel_url: `${origin}/#pricing`,
    metadata: { tier },
  })

  return NextResponse.json({ url: session.url })
}
