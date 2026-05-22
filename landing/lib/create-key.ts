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
    if (!createErr.message.toLowerCase().includes('already registered')) {
      throw new Error(`Failed to create user: ${createErr.message}`)
    }
    // User already exists — look up by email
    const { data: list, error: listErr } = await supabase.auth.admin.listUsers()
    if (listErr) throw new Error(`Failed to list users: ${listErr.message}`)
    const existing = list.users.find((u) => u.email === email)
    if (!existing) throw new Error('User not found after conflict')
    userId = existing.id
  } else {
    userId = created.user.id
  }

  const rawKey = 'es_' + randomBytes(24).toString('hex')
  const keyHash = createHash('sha256').update(rawKey).digest('hex')

  const { error: insertErr } = await supabase
    .from('api_keys')
    .insert({ user_id: userId, key_hash: keyHash, tier })

  if (insertErr) throw new Error(`Failed to insert API key: ${insertErr.message}`)

  return rawKey
}
