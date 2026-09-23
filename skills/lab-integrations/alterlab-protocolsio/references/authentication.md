# protocols.io Authentication

Source: https://apidoc.protocols.io/ (checked 2026-09-23).

## Access token types

| Token | How to get it | Access |
|-------|---------------|--------|
| `CLIENT_ACCESS_TOKEN` | Sign in and open https://www.protocols.io/developers | All public content plus the private content of the user who created the client |
| `OAUTH_ACCESS_TOKEN` | OAuth 2.0 authorization-code flow (below) | All public content plus the private content of the user who authorized your app |

Use the client token for scripts that act on your own account. Use OAuth when an application acts on behalf of other users.

Every API call sends the token as a Bearer header:

```
Authorization: Bearer <ACCESS_TOKEN>
```

Keep tokens in environment variables or a secrets manager; never commit them or paste them into shared notebooks.

## OAuth 2.0 flow

### 1. Register the client

On https://www.protocols.io/developers, copy your `client_id` and `client_secret` and enter your redirect URL under **private access**.

### 2. Send the user to the authorization link

```
https://www.protocols.io/api/v3/oauth/authorize?client_id=<client_id>&redirect_url=<redirect_url>&response_type=code&scope=readwrite&state=<random_state>
```

The parameter is `redirect_url` (not `redirect_uri`), and the documented scope is `readwrite`. Generate a random `state`, store it, and reject callbacks whose `state` does not match; this blocks cross-site request forgery.

After the user signs in and approves, protocols.io redirects to `<redirect_url>?code=<code>&state=<state>`.

### 3. Exchange the code for tokens

```bash
curl https://www.protocols.io/api/v3/oauth/token \
  -d client_id=<client_id> \
  -d client_secret=<client_secret> \
  -d grant_type=authorization_code \
  -d code=<code>
```

The exchange takes only these four form fields (no redirect parameter). The response:

```json
{
  "access_token": "<access_token>",
  "token_type": "bearer",
  "expires_in": "30681976",
  "scope": "readwrite",
  "refresh_token": "<refresh_token>",
  "refresh_expires_in": "62217976",
  "user": {"name": "...", "username": "...", "affiliation": null},
  "status_code": 0
}
```

`expires_in` and `refresh_expires_in` are seconds (the access token lasts about a year). Store both tokens.

### 4. Refresh before expiry

About a month before the access token expires, API responses include a warning:

```json
{"status_code": 0, "warning_code": 1, "warning_message": "Your access token expires in 24 days"}
```

After expiry, calls fail with HTTP 400 and `{"status_code": 1219, "error_message": "token is expired"}`. Refresh with:

```bash
curl https://www.protocols.io/api/v3/oauth/token \
  -d client_id=<client_id> \
  -d client_secret=<client_secret> \
  -d grant_type=refresh_token \
  -d refresh_token=<refresh_token>
```

The old access and refresh tokens stop working as soon as the refresh succeeds, so save the new pair atomically before discarding the old one.

### Client details

`GET https://www.protocols.io/api/v3/oauth/clients/<client_id>` (with the client access token) returns the client's `client_id`, `client_secret`, `grant_type`, `scope`, `redirect_url`, and `token`.

## MCP server

protocols.io runs an official remote MCP server:

| Field | Value |
|-------|-------|
| URL | `https://www.protocols.io/mcp` |
| Transport | Streamable HTTP |
| Auth | OAuth 2.0 sign-in (recommended), or `Authorization: Bearer <CLIENT_ACCESS_TOKEN>` |

With OAuth the MCP client runs the flow above for you; the connection can read all public content plus the signed-in user's private content. In Claude, add "protocols.io" from the connector directory, or add the URL as a custom remote MCP server. A generic client configuration:

```json
{"mcpServers": {"protocols.io": {"url": "https://www.protocols.io/mcp"}}}
```

An unauthenticated request to the endpoint returns HTTP 401 with a `WWW-Authenticate` header that points to the OAuth protected-resource metadata, which is what MCP clients use to start sign-in.

## Errors and limits

| Situation | Response |
|-----------|----------|
| Missing or malformed token | HTTP 400, `status_code` 1218 ("Authorization token is not correct") |
| Expired OAuth token | HTTP 400, `status_code` 1219 |
| Other failures | HTTP 400 or 500 with `status_code` plus `error_message` (v3) or `status_text` (v4) |
| More than 100 requests per minute per user | HTTP 429 |
| `/view/<uri>.pdf` above 5 requests per minute (signed in) or 3 per minute (signed out, per IP) | HTTP 429 |

Check the JSON `status_code` (0 means success) on every response rather than relying on the HTTP status alone.

On macOS, add `--compressed` to `curl` commands if the output looks like binary data.
