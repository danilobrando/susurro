# Susurro Pro — production setup checklist

Steps to take the API from "deployed" to "billing real customers". Order matters.

## 1. Add Postgres on Railway

The CLI's `railway add -d postgres` returns 401 due to a known bug in 4.36.1.
Use the dashboard instead:

1. Open https://railway.com/project/864b7791-e16a-4bf3-85be-56018df3a86b
2. Click **+ Create** → **Database** → **Add PostgreSQL**
3. Railway provisions Postgres and automatically injects `DATABASE_URL` into every service in the project — no manual var setting needed.
4. The `susurro-api` service will redeploy with the new URL. SQLModel auto-creates tables on startup.

Verify:
```bash
railway logs --service susurro-api --deployment | grep "Susurro API up"
# should print: free_quota=2000, pro_quota=100000
```

## 2. Resend (transactional email for magic links)

1. Sign up at https://resend.com
2. Add `susurro.live` as a domain → it'll show DNS records to add at Namecheap:
   - `MX`, `TXT (SPF)`, `TXT (DKIM)`, `TXT (DMARC)`
3. Add those records in **Namecheap → susurro.live → Advanced DNS**.
4. Wait until Resend shows the domain as **Verified** (usually < 15 min).
5. Create an API key. Set it on Railway:

   ```bash
   cd ~/proyectos/susurro/api
   railway variables --set "RESEND_API_KEY=re_..."
   ```

Without a verified domain, Resend will reject sends from `hi@susurro.live`. As a fallback, the API logs the magic-link URL to its logs when `RESEND_API_KEY` is empty — useful for local testing only.

## 3. Stripe (subscription billing)

1. Create a Stripe account at https://stripe.com
2. Create a **Product** → name: "Susurro Pro" → **Recurring price** $16.00 USD / month → save → copy the `price_xxx` ID.
3. Get your **Secret key** (`sk_test_...` for test mode, `sk_live_...` for production) from Developers → API keys.
4. Set on Railway:

   ```bash
   cd ~/proyectos/susurro/api
   railway variables \
     --set "STRIPE_SECRET_KEY=sk_..." \
     --set "STRIPE_PRICE_ID_PRO=price_..."
   ```

5. **Webhook**: Stripe → Developers → Webhooks → **Add endpoint**
   - URL: `https://api.susurro.live/billing/webhook` (or the railway.app URL while DNS is pending)
   - Events to send:
     - `checkout.session.completed`
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
   - After saving, Stripe shows a **signing secret** `whsec_...` — copy it:

   ```bash
   railway variables --set "STRIPE_WEBHOOK_SECRET=whsec_..."
   ```

6. **Customer Portal** (one-click cancel for users): Settings → Billing → Customer Portal → enable + save defaults.

Test the flow in **test mode** first with Stripe's `4242 4242 4242 4242` card.

## 4. Groq key

The API uses **our** Groq key to transcribe on behalf of users — don't reuse a personal key in production. Get a dedicated one:

1. https://console.groq.com/keys → **Create API Key** → label it "susurro-pro-prod"
2. Set on Railway:

   ```bash
   railway variables --set "GROQ_API_KEY=gsk_..."
   ```

## 5. Custom domain `api.susurro.live`

Add in the Railway dashboard (CLI's `railway domain <name>` has the same 401 bug):

1. Open the `susurro-api` service in the dashboard.
2. **Settings → Networking → Custom Domain** → add `api.susurro.live`.
3. Railway shows a CNAME target.
4. In Namecheap → susurro.live → Advanced DNS → add CNAME:
   - Type: `CNAME`
   - Host: `api`
   - Value: the Railway target (something like `susurro-api-production.up.railway.app`)
   - TTL: Automatic
5. Wait 5–15 min for DNS to propagate. Railway issues a TLS cert via Let's Encrypt automatically once the CNAME resolves.

## 6. Verify end-to-end

```bash
# magic link signup
open https://api.susurro.live/signin
# enter your email → check inbox → click link → land on /dashboard

# desktop pairing
open https://api.susurro.live/auth/desktop
# enter email → click link → copy token → paste into Susurro menu → "Sign in to Susurro Pro…"

# hold ⌥ and dictate. Word counter on /dashboard should increment.

# upgrade
# click "Upgrade to Pro" on /dashboard → Stripe Checkout (use test card) → returns to /dashboard
# /dashboard now says "Plan: Pro", quota becomes 100,000

# usage exceeded
# (only testable by spamming or temporarily lowering PRO_HARD_CAP)
```

## 7. (Optional) email forwarding for `hi@susurro.live`

Resend handles outbound; inbound is separate. Use Namecheap's free email forwarding:

1. Namecheap → susurro.live → Domain → Redirect Email → Add Alias
2. `hi@susurro.live` → forward to `dannybravo@gmail.com` (or whichever inbox)

This catches replies to magic-link emails + support requests from the landing footer.

## Env var summary

Required to be a functioning service:

| Variable | Why |
|---|---|
| `DATABASE_URL` | Auto-injected by Railway Postgres |
| `SESSION_SECRET` | Already set (random 64-byte token) |
| `API_URL` | `https://api.susurro.live` — set |
| `WEB_URL` | `https://susurro.live` — set |
| `EMAIL_FROM` | `Susurro <hi@susurro.live>` — set |
| `RESEND_API_KEY` | **Pending** — step 2 |
| `STRIPE_SECRET_KEY` | **Pending** — step 3 |
| `STRIPE_WEBHOOK_SECRET` | **Pending** — step 3 |
| `STRIPE_PRICE_ID_PRO` | **Pending** — step 3 |
| `GROQ_API_KEY` | **Pending** — step 4 |
| `FREE_WORD_QUOTA` | 2000 — set |
| `PRO_WORD_QUOTA` | 100000 — set |
| `PRO_HARD_CAP` | 110000 — set |
