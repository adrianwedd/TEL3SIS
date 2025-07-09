# TEL3SIS API Usage

This document describes the HTTP endpoints under `/v1` exposed by the TEL3SIS server. All requests require an `X-API-Key` header unless otherwise noted.

## Authentication

Generate an API key using `tel3sis-manage generate-api-key <owner>` and include it in the `X-API-Key` header:

```bash
X-API-Key: YOUR_API_KEY
```

## Endpoints

### `GET /v1/login`
Display the login form for the web dashboard.

### `POST /v1/login`
Submit form credentials to log in. Example request using `curl`:

```bash
curl -X POST https://example.com/v1/login \
  -F 'username=admin' \
  -F 'password=secret'
```

Returns a redirect to the dashboard on success or the login form with an error message.

### `GET /v1/logout`
Invalidate the current session and redirect to the login form.

### `GET /v1/login/oauth`
Begin an OAuth login flow. Redirects the user to the provider.

### `GET /v1/oauth/callback`
Handle the OAuth callback. On success, the user session is created and the browser is redirected to `/v1/dashboard`.

### `GET /v1/dashboard`
List recent calls in HTML. Requires authentication via cookie session.

### `GET /v1/dashboard/<call_id>`
Display transcript and audio for a single call in HTML.

### `GET /v1/calls`
Return a JSON array of call records. Example:

```bash
curl -H "X-API-Key: $KEY" https://example.com/v1/calls
```

Example response:

```json
[
  {
    "id": 1,
    "call_sid": "CA123...",
    "from_number": "+15551234567",
    "to_number": "+15557654321",
    "transcript_path": "/recordings/transcripts/call1.txt",
    "summary": "Short summary",
    "self_critique": null,
    "created_at": "2024-01-01T12:00:00"
  }
]
```

### `GET /v1/oauth/start`
Generate a provider authorization URL for tools like Google Calendar. Optional query parameter `user_id` identifies the requesting user. Example:

```bash
curl -H "X-API-Key: $KEY" 'https://example.com/v1/oauth/start?user_id=123'
```

Redirects the browser to the provider authorization page.

### `POST /v1/inbound_call`
Twilio webhook that starts a conversation. Example request:

```bash
curl -X POST https://example.com/v1/inbound_call \
  -H "X-API-Key: $KEY" \
  -F 'CallSid=CA0000000000' \
  -F 'From=+15551234567' \
  -F 'To=+15557654321'
```

Returns TwiML XML that instructs Twilio to stream audio to the agent.

### `POST /v1/recording_status`
Twilio callback when a recording is ready. Example request:

```bash
curl -X POST https://example.com/v1/recording_status \
  -H "X-API-Key: $KEY" \
  -F 'CallSid=CA0000000000' \
  -F 'RecordingSid=RS0000000' \
  -F 'RecordingUrl=https://api.twilio.com/recordings/RS0000000'
```

Returns `204 No Content` on success.

### `GET /v1/health`
Return service status information. Example response:

```json
{
  "redis": "ok",
  "database": "ok",
  "chromadb": "ok"
}
```

### `GET /v1/metrics`
Prometheus metrics endpoint. Returns text data in the Prometheus exposition format.

