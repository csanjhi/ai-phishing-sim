# Wiring Gophish to the AI service (one-time setup)

Gophish itself doesn't know about departments/AI templates — it just needs a
**Sending Profile (SMTP)**, a **Landing Page**, and a **Group** per department.
Create these once via the Gophish admin UI (`https://localhost:3333`) or its API:

1. **Sending Profile** — your real/test SMTP relay (e.g. a Mailtrap/Mailhog
   sandbox for testing). Name it e.g. `internal-smtp`.

2. **Landing Page** — a simple redirect page whose "Redirect to" URL points at
   the ai-service feedback endpoint pattern:
   `http://localhost:8000/feedback/trigger-redirect?campaign_id={{.CampaignID}}&email={{.Email}}`
   (Gophish's "capture submitted data" can stay OFF for a pure awareness
   exercise — the point is education, not data collection.)

3. **Groups** — one per department (`Finance`, `Engineering`, `Sales`, ...),
   each containing the target employees who've consented to the exercise.

4. **Webhook (optional, Gophish Enterprise/Pro-style setups or a small relay
   script)** — forward Gophish's `email_opened` / `clicked_link` /
   `submitted_data` events to:
   `POST http://localhost:8000/analytics/events`
   with body `{"campaign_id": "...", "target_email": "...", "department": "...", "event_type": "opened|clicked|submitted_data"}`

   If you're on open-source Gophish (no native webhooks), poll
   `GET /api/campaigns/{id}/results` on a timer and translate each result's
   status into a call to `/analytics/events` — a ~20-line cron script does this.

Once those exist, the ai-service's `push_to_gophish=true` flag on
`/templates/generate` will create the Gophish email template automatically,
and `/campaigns` + `/campaigns/{id}/approve` + `/campaigns/{id}/launch` in the
ai-service drive the human-approved workflow around it.
