# TEL3SIS User Guide

This guide walks through basic setup for non-technical users. It explains how to connect a phone number, grant calendar access, and fix common issues.

## Getting Started

1. Create a Twilio account and purchase a phone number.
2. Copy `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and your new number into the `.env` file.
3. Run `docker compose up` to start TEL3SIS.
4. Expose the app with `ngrok http 3000` and paste the forwarding URL into the Twilio Voice webhook for your number.

## Connecting Google Calendar

TEL3SIS can schedule meetings for you using Google Calendar.

1. While the server is running, visit `/auth/google` in your browser.
2. Approve the consent screen so TEL3SIS can read and create events.
3. The encrypted OAuth token is stored automatically. Revoke it any time from your Google security settings.

## Troubleshooting

- **Calls fail to connect** — confirm your Twilio credentials and webhook URL match the ngrok address.
- **Calendar events not appearing** — double‑check that you completed the OAuth flow and that the token exists in the database.
- **Server won’t start** — run `docker compose pull` to ensure images are up to date and that all required environment variables are set.

_For advanced options, see the other guides in this directory._
