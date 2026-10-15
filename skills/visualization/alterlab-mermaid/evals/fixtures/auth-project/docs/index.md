# Lab Data Portal — Developer Documentation

Internal documentation for the (fictional) lab data portal: a browser client, an auth service,
and a PostgreSQL database.

## Components

| Component | Code | Notes |
|-----------|------|-------|
| Web client | `client/` | Single-page app; stores the access token in memory only |
| Auth service | `services/auth/` | Sign-in, token refresh, sign-out (see `handlers.py`) |
| Database | PostgreSQL 16 | `users`, `refresh_tokens` tables |

## Running locally

```bash
docker compose up auth db
```

## API call sequence

TODO: add a diagram of how the client, auth service and database interact during sign-in,
token refresh and sign-out.

## Error codes

| Status | Meaning |
|--------|---------|
| 401 | Wrong credentials or invalid refresh token |
| 423 | Account locked after repeated failed sign-ins |
