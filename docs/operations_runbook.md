# Operations runbook

This runbook covers the single-instance portfolio deployment. It is not authorization to process
protected health information or real customer data.

## Runtime contract

| Endpoint | Authentication | Purpose |
|---|---|---|
| `GET /livez` | Public | Confirms the process can serve HTTP |
| `GET /readyz` | Public | Confirms SQLite is reachable and required application data loaded |
| `GET /metrics` | Bearer key in production | Prometheus-format operational metrics |
| `POST /v1/chat` | Bearer key in production | Concierge request API |

The container intentionally runs one Uvicorn process. SQLite and in-process Prometheus metrics are
not a horizontal-scaling design. Migrate both before running multiple replicas.

## Prepare configuration

Generate a long random API key in a secret manager. Configure only its SHA-256 digest:

```powershell
$key = "replace-with-a-long-random-secret"
$bytes = [Text.Encoding]::UTF8.GetBytes($key)
$hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLower()
$env:API_KEY_HASHES = $hash
$env:ALLOWED_HOSTS = "localhost,127.0.0.1,api.example.com"
```

Keep the raw key out of `.env`, shell history, source control, logs, and support messages. Multiple
comma-separated hashes support a rotation window. Remove the old hash after clients move to the new
key.

## Deploy

```powershell
docker compose build --pull
docker compose up -d
docker compose ps
```

The published port binds to loopback by default. Put an authenticated TLS reverse proxy or managed
ingress in front of it for any remote environment.

## Verify

```powershell
Invoke-RestMethod http://127.0.0.1:8000/livez
Invoke-RestMethod http://127.0.0.1:8000/readyz

$headers = @{ Authorization = "Bearer $key"; "X-Request-ID" = "deploy_smoke_001" }
Invoke-RestMethod http://127.0.0.1:8000/metrics -Headers $headers

$body = @{
  session_id = "deploy-smoke-001"
  message = "I want to book a consultation"
  consent_to_store = $false
} | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/v1/chat -Method Post -Headers $headers `
  -ContentType "application/json" -Body $body
```

Also verify that `/v1/chat` returns 401 without the bearer key and that every response contains an
`X-Request-ID` header.

## Observe

Stream JSON logs:

```powershell
docker compose logs --follow --tail 100 api
```

Logs contain request IDs, route templates, status, and duration. They intentionally exclude visitor
messages, session IDs, authorization values, and request bodies.

Recommended initial alerts for the deterministic configuration:

- readiness fails twice consecutively;
- HTTP 5xx responses exceed 2% for five minutes;
- p95 request duration exceeds one second for ten minutes;
- storage failure counter increases;
- repeated 401 responses indicate a client configuration problem or credential probing.

Ollama latency must be baselined separately before enabling model rewriting. The deterministic
fallback remains available when Ollama is unavailable.

## Backup and restore

Stop writes before copying the SQLite database volume. Retain backups according to an approved data
retention policy. Test restoration into a separate volume and require `/readyz` plus an authenticated
chat smoke before returning it to service.

## Rollback triggers

Rollback when any of the following occurs after a release:

- `/readyz` fails twice;
- authenticated chat requests fail or return an incorrect safety action;
- 5xx responses exceed 2% for five minutes;
- p95 deterministic latency exceeds one second for ten minutes;
- logs or metrics expose message, session, or credential data; or
- the storage failure counter increases after a routine request.

## Rollback procedure

1. Capture the failing image tag, request IDs, metrics, and bounded logs without customer content.
2. Stop the new container.
3. Start the last verified immutable image with the same volume and secret configuration.
4. Verify liveness, readiness, authentication rejection, authenticated chat, metrics, and safety cases.
5. Record the incident and root cause before attempting another release.

Database schema changes require a separate backup and migration rollback plan. Version 0.3.0 does
not change the existing event table schema.
