import { createClient } from '@supabase/supabase-js'
import { createHash, randomBytes } from 'crypto'

function adminClient() {
  const url = process.env.SUPABASE_URL
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY
  if (!url || !key) throw new Error('Missing Supabase env vars')
  return createClient(url, key, { auth: { autoRefreshToken: false, persistSession: false } })
}

export async function createApiKey(
  email: string,
  tier: 'free' | 'core' | 'pro',
): Promise<string> {
  const supabase = adminClient()

  let userId: string

  const { data: created, error: createErr } = await supabase.auth.admin.createUser({
    email,
    email_confirm: true,
  })

  if (createErr) {
    if (!createErr.message.toLowerCase().includes('already')) {
      throw new Error(`Failed to create user: ${createErr.message}`)
    }
    // User already exists — fetch by email via admin REST (O(1), no full scan)
    const url = process.env.SUPABASE_URL!
    const key = process.env.SUPABASE_SERVICE_ROLE_KEY!
    const res = await fetch(
      `${url}/auth/v1/admin/users?email=${encodeURIComponent(email)}`,
      { headers: { Authorization: `Bearer ${key}`, apikey: key } },
    )
    const body = await res.json() as { users?: { id: string }[] }
    const found = body.users?.[0]?.id
    if (!found) throw new Error('User not found after conflict')
    userId = found
  } else {
    userId = created.user.id
  }

  const rawKey = 'es_' + randomBytes(24).toString('hex')
  const keyHash = createHash('sha256').update(rawKey).digest('hex')

  const { error: insertErr } = await supabase
    .from('api_keys')
    .insert({ user_id: userId, key_hash: keyHash, tier })

  if (insertErr) {
    if (insertErr.code === '23505') {
      const err = new Error('KEY_EXISTS') as Error & { code: string }
      err.code = 'KEY_EXISTS'
      throw err
    }
    throw new Error(`Failed to insert API key: ${insertErr.message}`)
  }

  return rawKey
}
