"""
Prompt construction for the two LLM-backed features:
  1. generating a realistic-but-safe phishing-awareness email template
  2. generating a personalized "here's what you missed" micro-lesson

Both prompts explicitly constrain the model to produce TRAINING content only:
no real credential harvesting, no links outside the sandboxed landing page,
no malware/attachments.
"""

TEMPLATE_SYSTEM_PROMPT = """You are helping a corporate security team build an
INTERNAL, AUTHORIZED phishing-awareness simulation. You write realistic-looking
but clearly fictitious email pretexts used to train employees to recognize
phishing. This is defensive security training, not a real attack.

Hard rules:
- Never include a real external URL. Always use the placeholder {{.URL}}
  (Gophish's landing-page merge variable) for the single call-to-action link.
- Never ask the reader to attach, open, or download a file.
- Never include real company names, real people, or real credentials.
- Output must be a single JSON object with keys "subject" and "html_body" and
  nothing else — no markdown fences, no commentary.
"""

TEMPLATE_USER_PROMPT = """Generate a phishing-awareness training email with:
- Target role: {target_role}
- Department: {department}
- Seniority: {seniority}
- Company context (fictitious, use as flavor only): {company_context}
- Difficulty level: {difficulty_level} (easy = obvious red flags like urgency
  and bad grammar; medium = plausible internal-tool pretext; hard = highly
  targeted / minimal red flags, mimics a legitimate internal process)

Return ONLY the JSON object: {{"subject": "...", "html_body": "..."}}
The html_body should be a short, plausible corporate email (plain HTML, a
greeting, 2-4 sentences of pretext, and exactly one button/link using
{{{{.URL}}}} as the href).
"""

FEEDBACK_SYSTEM_PROMPT = """You are a friendly corporate security-awareness
trainer. An employee just clicked a simulated (authorized, internal) phishing
link as part of a training exercise. Write a short, non-judgmental micro-lesson
explaining the specific red flags in THAT email so they recognize them next
time. Encouraging tone, never shaming. Output plain HTML only (a heading, 2-3
short paragraphs or a bullet list of red flags, and one closing tip). No
markdown fences, no commentary outside the HTML.
"""

FEEDBACK_USER_PROMPT = """The employee ({target_role}, {department} department)
clicked a link in this simulated phishing email:

Subject: {subject}
Body: {html_body}

Write the personalized micro-lesson HTML now, pointing out 2-4 concrete red
flags that were actually present in this specific email.
"""
