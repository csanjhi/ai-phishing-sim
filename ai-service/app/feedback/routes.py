from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app import models, schemas
from app.llm.client import generate_feedback_lesson

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/trigger")
def trigger_feedback(req: schemas.FeedbackTriggerRequest, db: Session = Depends(get_db)):
    """
    Call this when a Gophish 'clicked' webhook fires (or wire it directly into
    the Gophish landing-page redirect). Generates a personalized micro-lesson
    based on the exact template that tricked this person, and logs a
    'clicked' event for analytics at the same time.
    """
    campaign = db.get(models.Campaign, req.campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    template = campaign.template
    if not template:
        raise HTTPException(400, "Campaign has no associated template")

    lesson_html, model_used = generate_feedback_lesson(
        req.target_role, campaign.department or template.department or "general",
        template.subject, template.html_body,
    )

    log = models.FeedbackLog(
        campaign_id=campaign.id,
        target_email=req.target_email,
        lesson_html=lesson_html,
        model_used=model_used,
    )
    db.add(log)

    # Log the click itself so analytics picks it up too.
    db.add(models.ClickEvent(
        campaign_id=campaign.id,
        target_email=req.target_email,
        department=campaign.department or template.department or "general",
        event_type="clicked",
    ))
    db.commit()
    db.refresh(log)

    return {"feedback_id": log.id, "token": log.token, "page_url": f"/feedback/page/{log.token}"}


@router.get("/page/{token}", response_class=HTMLResponse)
def feedback_page(token: str, db: Session = Depends(get_db)):
    """
    This is the page Gophish's landing-page redirect should point employees to
    right after they click — the 'gotcha, here's why' moment.
    """
    log = db.query(models.FeedbackLog).filter(models.FeedbackLog.token == token).first()
    if not log:
        raise HTTPException(404, "Feedback page not found")
    log.delivered = True
    db.commit()

    return f"""
    <html>
    <head>
      <title>Phishing Awareness — You Got Caught (Safely)</title>
      <style>
        body {{ font-family: -apple-system, Arial, sans-serif; max-width: 640px;
                margin: 60px auto; padding: 0 20px; color: #1f2937; }}
        .badge {{ display: inline-block; background: #fef3c7; color: #92400e;
                  padding: 4px 12px; border-radius: 999px; font-size: 13px;
                  margin-bottom: 16px; }}
      </style>
    </head>
    <body>
      <span class="badge">Simulated Phishing Exercise</span>
      {log.lesson_html}
      <hr/>
      <p style="font-size:13px;color:#6b7280;">
        This was an authorized internal security-awareness exercise. No real
        data was collected. Questions? Contact your security team.
      </p>
    </body>
    </html>
    """


@router.get("/logs/{campaign_id}")
def list_feedback_for_campaign(campaign_id: str, db: Session = Depends(get_db)):
    logs = db.query(models.FeedbackLog).filter(models.FeedbackLog.campaign_id == campaign_id).all()
    return [
        {"target_email": l.target_email, "delivered": l.delivered, "model_used": l.model_used,
         "created_at": l.created_at}
        for l in logs
    ]
