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
    // User already exists — walk paginated list to find by email
    let found: string | undefined
    let page = 1
    while (true) {
      const { data: list, error: listErr } = await supabase.auth.admin.listUsers({ page, perPage: 1000 })
      if (listErr) throw new Error(`Failed to list users: ${listErr.message}`)
      const match = list.users.find((u) => u.email === email)
      if (match) { found = match.id; break }
      if (list.nextPage === null) break
      page++
    }
    if (!found) throw new Error('User not found after conflict')
    userId = found
  } else {
    userId = created.user.id
  }

  // Idempotency: one key per (user, tier) — also acts as rate-limit for free signups
  const { data: existingKey } = await supabase
    .from('api_keys')
    .select('id')
    .eq('user_id', userId)
    .eq('tier', tier)
    .maybeSingle()

  if (existingKey) {
    const err = new Error('KEY_EXISTS') as Error & { code: string }
    err.code = 'KEY_EXISTS'
    throw err
  }

  const rawKey = 'es_' + randomBytes(24).toString('hex')
  const keyHash = createHash('sha256').update(rawKey).digest('hex')

  const { error: insertErr } = await supabase
    .from('api_keys')
    .insert({ user_id: userId, key_hash: keyHash, tier })

  if (insertErr) throw new Error(`Failed to insert API key: ${insertErr.message}`)

  return rawKey
}
