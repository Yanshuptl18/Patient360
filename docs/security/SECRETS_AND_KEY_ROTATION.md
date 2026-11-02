# Patient360 — Secrets & Cryptographic Key Rotation Protocol

## 1. Overview
This specification describes the secret management architecture, cryptographic key requirements, and zero-downtime key rotation protocol for Patient360.

---

## 2. Cryptographic Key Requirements

All production secrets must adhere to the following standards:
1. **Minimum Entropy**: Secrets must have at least 256 bits of cryptographic entropy (minimum 32 bytes / 64 hex characters).
2. **Prohibited Values**: Insecure defaults containing `insecure`, `development`, `default`, `test`, or `patient360_development` are blocked by Pydantic model validation at application startup when `ENVIRONMENT=production`.
3. **Storage Security**: Secrets must never be committed to source control or embedded into Docker images.

### Key Generation Command
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Or via OpenSSL:
```bash
openssl rand -hex 32
```

---

## 3. Zero-Downtime JWT Secret Rotation Protocol

To rotate the JWT signing key without terminating active clinician sessions:

### Step 1: Pre-Rotation Window (Dual-Key Support)
1. Generate a new secret: `NEW_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")`.
2. Configure the application with:
   - `SECRET_KEY`: `<NEW_SECRET_KEY>` (used for issuing new tokens).
   - `JWT_PREVIOUS_SECRET_KEY`: `<OLD_SECRET_KEY>` (used to accept existing valid tokens during the 30-minute transition window).
3. Deploy the application service.

### Step 2: Post-Rotation Cleanup
1. Allow at least `ACCESS_TOKEN_EXPIRE_MINUTES` (30 minutes) for all old access tokens to naturally expire.
2. Remove `JWT_PREVIOUS_SECRET_KEY` from environment variables.
3. Redeploy the application. All sessions are now signed with and verified by the new key.

---

## 4. Cloud Secret Provider Integration

### Google Cloud Secret Manager (GCP)
When running in GCP Cloud Run, Patient360 automatically delegates secret resolution to `google-cloud-secret-manager` via `backend.core.secrets.get_secret()`:
- `projects/{PROJECT_ID}/secrets/PATIENT360_JWT_SECRET/versions/latest`
- `projects/{PROJECT_ID}/secrets/PATIENT360_DATABASE_URL/versions/latest`
- `projects/{PROJECT_ID}/secrets/GEMINI_API_KEY/versions/latest`

### Render / Vercel
On cloud platforms such as Render and Vercel:
- Set `SECRET_KEY` directly in the Dashboard Environment Variables.
- Enable Environment Variable encryption.
- Ensure `ENVIRONMENT=production`.
