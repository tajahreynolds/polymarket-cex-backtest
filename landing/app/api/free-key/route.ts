import { NextRequest, NextResponse } from 'next/server'
import { Resend } from 'resend'
import { createApiKey } from '@/lib/create-key'

export async function POST(req: NextRequest) {
  const resend = new Resend(process.env.RESEND_API_KEY)
  let email: string
  try {
    const body = await req.json()
    email = (body.email ?? '').trim().toLowerCase()
  } catch {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  }

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json({ error: 'Valid email required' }, { status: 400 })
  }

  let rawKey: string
  try {
    rawKey = await createApiKey(email, 'free')
  } catch (err: unknown) {
    if ((err as { code?: string }).code === 'KEY_EXISTS') {
      return NextResponse.json({ success: true })
    }
    console.error('[free-key] createApiKey error:', err)
    return NextResponse.json({ error: 'Failed to create key' }, { status: 500 })
  }

  try {
    await resend.emails.send({
      from: 'EdgeSignal <onboarding@resend.dev>',
      to: email,
      subject: 'Your EdgeSignal API Key',
      html: `
        <p>Here's your EdgeSignal free API key:</p>
        <pre style="background:#111;color:#e5e5e5;padding:1rem;border-radius:4px;font-family:monospace">${rawKey}</pre>
        <p>Test it now:</p>
        <pre style="background:#111;color:#e5e5e5;padding:1rem;border-radius:4px;font-family:monospace">curl -H "Authorization: Bearer ${rawKey}" \\
  https://micro-arb-production.up.railway.app/v1/signals/latest</pre>
        <p style="color:#888;font-size:0.875rem">Free tier: 100 signals/day via REST. Questions? contact@mineexi.resend.app</p>
      `,
    })
  } catch (err) {
    console.error('[free-key] Resend error:', err)
    // Key created — don't fail the request over email
  }

  return NextResponse.json({ success: true })
}
