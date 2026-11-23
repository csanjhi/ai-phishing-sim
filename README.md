# AI-Enhanced Phishing Simulation Platform

An internal security-awareness training tool that extends the open-source
[Gophish](https://getgophish.com/) phishing-simulation framework with an AI
layer: it generates realistic, role-aware phishing templates, tracks
engagement analytics by department, and delivers a personalized "here's what
you missed" micro-lesson the moment someone clicks.

> ⚠️ **Ethical use only.** This is built for **authorized, consented internal
> security-awareness testing** run by an organization's own security team.
> Every campaign requires an explicit human sign-off (`approved_by`) before it
> can launch, every generated template links only to the configured Gophish
> landing page, and no real credential harvesting or external links are ever
> produced. Do not point this at anyone without documented authorization.

## Architecture

```
┌─────────────┐        ┌──────────────────────────────────────┐
│   Gophish   │◄──────►│              ai-service               │
│ (send email,│  REST  │  FastAPI app, SQLite/Postgres          │
│  track opens│  API   │  ┌────────────┐ ┌──────────────────┐  │
│  & clicks,  │        │  │  Module 1  │ │     Module 2      │  │
│  landing    │        │  │  AI Template│ │    Analytics      │  │
│  pages)     │        │  │  Generator │ │  (click-rate by    │  │
│             │        │  └────────────┘ │  dept/insights)    │  │
│             │        │  ┌────────────┐ └──────────────────┘  │
│             │ webhook│  │  Module 3  │ ┌──────────────────┐  │
│             │───────►│  │  Feedback  │ │     Module 4      │  │
│             │        │  │  Engine    │ │   Dashboard (UI)   │  │
│             │        │  └────────────┘ └──────────────────┘  │
└─────────────┘        └──────────────────────────────────────┘
                                    │
                             ┌──────▼──────┐
                             │  LLM API    │
                             │ OpenAI /    │
                             │ Anthropic / │
                             │ mock (demo) │
                             └─────────────┘
```

## Quick start (demo mode, no API keys, no Gophish needed)

```bash
cd ai-service
pip install -r requirements.txt
cp ../.env.example ../.env     # LLM_PROVIDER=mock works out of the box
uvicorn app.main:app --reload
```

Open **http://localhost:8000** — the dashboard loads with 3 seeded
departments, AI-generated (mock) templates, and demo click-rate data. Visit
**http://localhost:8000/analytics-view** for the analytics/insights view, or
**http://localhost:8000/docs** for the interactive Swagger API.

## Full stack with Gophish (Docker)

```bash
cp .env.example .env
# fill in OPENAI_API_KEY or ANTHROPIC_API_KEY and set LLM_PROVIDER accordingly
# fill in GOPHISH_API_KEY after Gophish's first run (see below)
docker compose up --build
```

1. First boot: open `https://localhost:3333`, log in with the admin password
   printed in `docker compose logs gophish`, grab your API key from
   **Settings**, put it in `.env` as `GOPHISH_API_KEY`, then
   `docker compose restart ai-service`.
2. Follow `gophish-config/seed_campaign_setup.md` to create a Sending
   Profile, Landing Page, and Groups in Gophish (one-time).
3. Use the ai-service dashboard (`http://localhost:8000`) to generate
   templates (tick "Push to Gophish"), create a campaign, get it
   **approved**, then **launch** it.

## Module reference

| Module | Endpoint(s) | What it does |
|---|---|---|
| 1. AI Template Generator | `POST /templates/generate`, `GET /templates` | Generates a role/department/difficulty-aware phishing email via the LLM; optionally pushes it into Gophish as a template. |
| 1b. Campaign workflow | `POST /campaigns`, `POST /campaigns/{id}/approve`, `POST /campaigns/{id}/launch` | Human-in-the-loop: a campaign can't launch without an `approved_by` sign-off. |
| 2. Analytics | `POST /analytics/events`, `GET /analytics/summary`, `GET /analytics/insights`, `GET /analytics/export` | Ingests sent/opened/clicked/submitted_data events, aggregates click-rate by department, surfaces automated insights, exports CSV. |
| 3. Feedback Engine | `POST /feedback/trigger`, `GET /feedback/page/{token}` | Generates a personalized micro-lesson explaining the specific red flags in the email that fooled this person, served as the landing-page redirect target. |
| 4. Dashboard | `GET /`, `GET /analytics-view` | Minimal internal UI wrapping all of the above — generate templates, manage campaigns, view analytics, simulate events for demo purposes. |

## Tests

```bash
cd ai-service
pytest tests/ -v
```

Tests run fully offline against `LLM_PROVIDER=mock` and a throwaway SQLite
file — no API keys or Gophish instance required.

## Project layout

```
ai-phishing-sim/
├── docker-compose.yml
├── .env.example
├── gophish-config/
│   ├── config.json
│   └── seed_campaign_setup.md
└── ai-service/
    ├── Dockerfile
    ├── requirements.txt
    ├── app/
    │   ├── main.py              # FastAPI entrypoint, wires everything together
    │   ├── db.py / models.py / schemas.py
    │   ├── seed.py               # demo data
    │   ├── gophish_client.py     # Gophish REST wrapper (fails soft if unconfigured)
    │   ├── llm/                  # provider-agnostic LLM client + prompts
    │   ├── templates_api/        # Module 1 + campaign workflow
    │   ├── analytics/            # Module 2
    │   ├── feedback/             # Module 3
    │   └── dashboard/            # Module 4 (Jinja2 + vanilla JS)
    └── tests/
```
