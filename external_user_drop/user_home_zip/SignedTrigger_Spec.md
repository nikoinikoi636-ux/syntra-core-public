# Signed Trigger Protocol (JWS-Detached)

**Updated:** 2025-08-27T05:31:36Z

## Purpose
Replace plain keyword triggers with signed control messages to prevent spoofing.

## Message fields
- `kid` — key id (e.g., K1-DEMO)
- `ts` — timestamp (UTC, ISO 8601)
- `nonce` — random 128-bit hex to prevent replay
- `cmd` — one of: RESET, OVERRIDE_CHECK, STRESS, COOLDOWN
- `sig` — JWS (detached payload) over `{kid,ts,nonce,cmd}`

## Verification
1. Check clock skew ≤ 120s.
2. Verify signature with Ed25519 public key matching `kid`.
3. Ensure `nonce` not seen before (nonce store TTL ≥ 24h).
4. Execute mapped action only if policy allows and cooldown isn't active.

## Keys
Store public keys in `policy.triggers_signed.public_keys`. Rotate quarterly.
