import { NextRequest, NextResponse } from 'next/server'
import { createHmac, timingSafeEqual } from 'crypto'
import { createClient } from '@supabase/supabase-js'

export const dynamic = 'force-dynamic'

function adminClient() {
  return createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } },
  )
}

// Svix HMAC-SHA256 verification (Resend uses Svix under the hood)
function verifySignature(payload: string, headers: Headers): boolean {
  const msgId = headers.get('svix-id')
  const msgTimestamp = headers.get('svix-timestamp')
  const msgSignature = headers.get('svix-signature')

  if (!msgId || !msgTimestamp || !msgSignature) return false

  const secret = process.env.RESEND_WEBHOOK_SECRET ?? ''
  const secretBytes = Buffer.from(secret.replace(/^whsec_/, ''), 'base64')
  const toSign = `${msgId}.${msgTimestamp}.${payload}`
  const computed = createHmac('sha256', secretBytes).update(toSign).digest('base64')

  return msgSignature.split(' ').some((part) => {
    const sig = part.split(',')[1]
    if (!sig) return false
    try {
      return timingSafeEqual(Buffer.from(sig), Buffer.from(computed))
    } catch {
      return false
    }
  })
}

export async function POST(req: NextRequest) {
  const rawBody = await req.text()

  if (!verifySignature(rawBody, req.headers)) {
    console.error('[resend-webhook] signature verification failed')
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
  }

  let event: { type: string; data: Record<string, unknown> }
  try {
    event = JSON.parse(rawBody)
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  if (event.type === 'email.received') {
    const supabase = adminClient()
    const { error } = await supabase.from('inbound_emails').insert({
      from: event.data.from,
      to: event.data.to,
      subject: event.data.subject,
      text: event.data.text,
      html: event.data.html,
      headers: event.data.headers,
      received_at: new Date().toISOString(),
    })
    if (error) console.error('[resend-webhook] insert error:', error)
  }

  return NextResponse.json({ ok: true })
}
