import { NextRequest, NextResponse } from 'next/server'
import Stripe from 'stripe'
import { createClient } from '@supabase/supabase-js'
import { Resend } from 'resend'
import { createApiKey } from '@/lib/create-key'

export const dynamic = 'force-dynamic'


function adminClient() {
  return createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } },
  )
}

export async function POST(req: NextRequest) {
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: '2026-04-22.dahlia' })
  const resend = new Resend(process.env.RESEND_API_KEY)
  const sig = req.headers.get('stripe-signature')
  const rawBody = await req.text()

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(rawBody, sig!, process.env.STRIPE_WEBHOOK_SECRET!)
  } catch (err) {
    console.error('[webhook] signature verification failed:', err)
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
  }

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object as Stripe.Checkout.Session
    const email = session.customer_details?.email
    const tier = (session.metadata?.tier ?? 'core') as 'core' | 'pro'
    const tierLabel = tier === 'core' ? 'Core ($49/mo)' : 'Pro ($149/mo)'

    if (!email) {
      console.error('[webhook] no email in session', session.id)
      return NextResponse.json({ ok: true })
    }

    let rawKey: string
    try {
      rawKey = await createApiKey(email, 'free')
    } catch (err: unknown) {
      if ((err as { code?: string }).code === 'KEY_EXISTS') {
        return NextResponse.json({ success: true })
      }
      console.error('[webhook] createApiKey error:', err)
      return NextResponse.json({ error: 'Key creation failed' }, { status: 500 })
    }

    // Record waitlist interest
    const supabase = adminClient()
    const { error: wlErr } = await supabase.from('waitlist').insert({ email, tier })
    if (wlErr) console.error('[webhook] waitlist insert error:', wlErr)

    // Record subscription
    await supabase
      .from('subscriptions')
      .upsert(
        {
          stripe_customer_id: session.customer as string,
          stripe_subscription_id: session.subscription as string,
          plan: 'free',
          status: 'active',
        },
        { onConflict: 'stripe_customer_id' },
      )
      .then(({ error }) => {
        if (error) console.error('[webhook] subscription upsert error:', error)
      })

    try {
      await resend.emails.send({
        from: 'EdgeSignal <onboarding@resend.dev>',
        to: email,
        subject: 'Welcome to EdgeSignal — your API key inside',
        html: `
          <p>Thanks for your interest in EdgeSignal ${tierLabel}.</p>
          <p><strong>Your card was not charged</strong> — we're in early access and not billing yet.</p>
          <p>Here's a free API key so you can start testing right now:</p>
          <pre style="background:#111;color:#e5e5e5;padding:1rem;border-radius:4px;font-family:monospace">${rawKey}</pre>
          <p>Test it:</p>
          <pre style="background:#111;color:#e5e5e5;padding:1rem;border-radius:4px;font-family:monospace">curl -H "Authorization: Bearer ${rawKey}" \\
  https://micro-arb-production.up.railway.app/v1/signals/latest</pre>
          <p>We'll reach out when ${tierLabel} goes live with billing.</p>
          <p style="color:#888;font-size:0.875rem">Questions? contact@mineexi.resend.app</p>
        `,
      })
    } catch (err) {
      console.error('[webhook] Resend error:', err)
    }
  }

  return NextResponse.json({ ok: true })
}
