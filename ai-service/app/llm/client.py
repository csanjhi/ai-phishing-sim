"""
Provider-agnostic LLM client.

LLM_PROVIDER=mock      -> no API key needed, deterministic templated output.
                           Used for seed data / CI / offline demo.
LLM_PROVIDER=openai    -> calls OpenAI chat completions.
LLM_PROVIDER=anthropic -> calls Anthropic messages API.

Both real providers are called with httpx directly (no SDK dependency) so the
service stays lightweight; swap in the official SDKs if you prefer.
"""
import json
import os
import httpx

from app.llm.prompts import (
    TEMPLATE_SYSTEM_PROMPT,
    TEMPLATE_USER_PROMPT,
    FEEDBACK_SYSTEM_PROMPT,
    FEEDBACK_USER_PROMPT,
)

PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


class LLMError(RuntimeError):
    pass


def _call_openai(system: str, user: str) -> str:
    if not OPENAI_API_KEY:
        raise LLMError("OPENAI_API_KEY not set")
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.7,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_anthropic(system: str, user: str) -> str:
    if not ANTHROPIC_API_KEY:
        raise LLMError("ANTHROPIC_API_KEY not set")
    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 1024,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    blocks = resp.json()["content"]
    return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


def _mock_template(target_role, department, seniority, company_context, difficulty_level) -> str:
    flavor = {
        "easy": ("URGENT: Password Expires Today", "This is urgent, act now or lose access!!"),
        "medium": (f"[Action Required] {department} Portal Access Update",
                   f"As part of a scheduled update to the {department} portal, please confirm your access."),
        "hard": (f"Re: {department} Q-review follow-up",
                 "Following up on this from our sync earlier — can you confirm before EOD?"),
    }.get(difficulty_level, ("Action Required", "Please review and confirm."))
    subject, pretext = flavor
    html = (
        f"<p>Hi there,</p>"
        f"<p>{pretext} This affects {seniority}-level staff in {department} "
        f"at {company_context}.</p>"
        f'<p><a href="{{{{.URL}}}}" style="background:#2563eb;color:#fff;'
        f'padding:10px 18px;border-radius:6px;text-decoration:none;">Confirm Now</a></p>'
        f"<p>Thanks,<br/>IT Support</p>"
    )
    return json.dumps({"subject": subject, "html_body": html})


def _mock_feedback(target_role, department, subject, html_body) -> str:
    return (
        "<h2>You just took part in a phishing simulation</h2>"
        f"<p>This test email (subject: <em>{subject}</em>) was sent to see how "
        f"{department} staff respond to urgency-based requests.</p>"
        "<ul>"
        "<li>The sender created artificial urgency.</li>"
        "<li>The link text didn't show the real destination before clicking.</li>"
        "<li>It asked you to act outside your normal workflow.</li>"
        "</ul>"
        "<p>Next time: hover over links, verify via a separate channel, and "
        "report suspicious emails to security@yourcompany.</p>"
    )


def generate_phishing_template(target_role, department, seniority, company_context, difficulty_level):
    """Returns (subject: str, html_body: str, model_used: str, prompt_used: str)."""
    user_prompt = TEMPLATE_USER_PROMPT.format(
        target_role=target_role, department=department, seniority=seniority,
        company_context=company_context, difficulty_level=difficulty_level,
    )

    if PROVIDER == "openai":
        raw = _call_openai(TEMPLATE_SYSTEM_PROMPT, user_prompt)
        model_used = f"openai:{OPENAI_MODEL}"
    elif PROVIDER == "anthropic":
        raw = _call_anthropic(TEMPLATE_SYSTEM_PROMPT, user_prompt)
        model_used = f"anthropic:{ANTHROPIC_MODEL}"
    else:
        raw = _mock_template(target_role, department, seniority, company_context, difficulty_level)
        model_used = "mock"

    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)
    return data["subject"], data["html_body"], model_used, user_prompt


def generate_feedback_lesson(target_role, department, subject, html_body):
    """Returns (lesson_html: str, model_used: str)."""
    user_prompt = FEEDBACK_USER_PROMPT.format(
        target_role=target_role, department=department, subject=subject, html_body=html_body,
    )

    if PROVIDER == "openai":
        lesson = _call_openai(FEEDBACK_SYSTEM_PROMPT, user_prompt)
        model_used = f"openai:{OPENAI_MODEL}"
    elif PROVIDER == "anthropic":
        lesson = _call_anthropic(FEEDBACK_SYSTEM_PROMPT, user_prompt)
        model_used = f"anthropic:{ANTHROPIC_MODEL}"
    else:
        lesson = _mock_feedback(target_role, department, subject, html_body)
        model_used = "mock"

    return lesson.strip(), model_used
