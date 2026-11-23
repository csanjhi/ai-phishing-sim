"""
Seeds a small demo dataset (3 departments, 3 AI-generated templates, 3
campaigns, and mock click events) so the dashboard is populated on first run.
Runs automatically on startup only if the DB is empty — safe to call repeatedly.
"""
from app.db import SessionLocal
from app import models
from app.llm.client import generate_phishing_template

DEMO = [
    ("Finance", "Finance Analyst", "mid", "easy"),
    ("Engineering", "Software Engineer", "senior", "hard"),
    ("Sales", "Account Executive", "junior", "medium"),
]


def run():
    db = SessionLocal()
    try:
        if db.query(models.Department).count() > 0:
            return  # already seeded

        for dept_name, role, seniority, difficulty in DEMO:
            dept = models.Department(name=dept_name, headcount=25)
            db.add(dept)
            db.flush()

            subject, html_body, model_used, prompt_used = generate_phishing_template(
                role, dept_name, seniority, "a mid-size fintech company", difficulty,
            )
            tmpl = models.GeneratedTemplate(
                name=f"{dept_name}-{difficulty}-seed",
                subject=subject, html_body=html_body,
                target_role=role, department=dept_name, seniority=seniority,
                difficulty_level=difficulty, model_used=model_used, prompt_used=prompt_used,
            )
            db.add(tmpl)
            db.flush()

            campaign = models.Campaign(
                name=f"{dept_name} Awareness Test", template_id=tmpl.id,
                department=dept_name, status="launched", approved_by="demo-seed",
            )
            db.add(campaign)
            db.flush()

            # Mock funnel: 20 sent, with decreasing engagement at each stage.
            sent, opened, clicked, submitted = 20, 12, 5, 1
            for i in range(sent):
                db.add(models.ClickEvent(campaign_id=campaign.id, department=dept_name,
                                          target_email=f"user{i}@demo.local", event_type="sent"))
            for i in range(opened):
                db.add(models.ClickEvent(campaign_id=campaign.id, department=dept_name,
                                          target_email=f"user{i}@demo.local", event_type="opened"))
            for i in range(clicked):
                db.add(models.ClickEvent(campaign_id=campaign.id, department=dept_name,
                                          target_email=f"user{i}@demo.local", event_type="clicked"))
            for i in range(submitted):
                db.add(models.ClickEvent(campaign_id=campaign.id, department=dept_name,
                                          target_email=f"user{i}@demo.local", event_type="submitted_data"))

        db.commit()
    finally:
        db.close()
