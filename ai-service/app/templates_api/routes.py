from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app import models, schemas
from app.llm.client import generate_phishing_template
from app.gophish_client import gophish_client

router = APIRouter(tags=["templates & campaigns"])


@router.post("/templates/generate", response_model=schemas.TemplateOut)
def generate_template(req: schemas.TemplateGenerateRequest, db: Session = Depends(get_db)):
    subject, html_body, model_used, prompt_used = generate_phishing_template(
        req.target_role, req.department, req.seniority, req.company_context, req.difficulty_level,
    )

    name = f"{req.department}-{req.difficulty_level}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    tmpl = models.GeneratedTemplate(
        name=name,
        subject=subject,
        html_body=html_body,
        target_role=req.target_role,
        department=req.department,
        seniority=req.seniority,
        difficulty_level=req.difficulty_level,
        model_used=model_used,
        prompt_used=prompt_used,
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)

    if req.push_to_gophish:
        result = gophish_client.create_template(name, subject, html_body)
        if result and "id" in result:
            tmpl.gophish_template_id = result["id"]
            db.commit()
            db.refresh(tmpl)

    return tmpl


@router.get("/templates", response_model=list[schemas.TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    return db.query(models.GeneratedTemplate).order_by(models.GeneratedTemplate.created_at.desc()).all()


@router.get("/templates/{template_id}", response_model=schemas.TemplateOut)
def get_template(template_id: str, db: Session = Depends(get_db)):
    tmpl = db.get(models.GeneratedTemplate, template_id)
    if not tmpl:
        raise HTTPException(404, "Template not found")
    return tmpl


@router.post("/campaigns", response_model=schemas.CampaignOut)
def create_campaign(req: schemas.CampaignCreateRequest, db: Session = Depends(get_db)):
    tmpl = db.get(models.GeneratedTemplate, req.template_id)
    if not tmpl:
        raise HTTPException(404, "Template not found")
    campaign = models.Campaign(name=req.name, template_id=req.template_id, department=req.department)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("/campaigns", response_model=list[schemas.CampaignOut])
def list_campaigns(db: Session = Depends(get_db)):
    return db.query(models.Campaign).order_by(models.Campaign.created_at.desc()).all()


@router.post("/campaigns/{campaign_id}/approve", response_model=schemas.CampaignOut)
def approve_campaign(campaign_id: str, req: schemas.CampaignApproveRequest, db: Session = Depends(get_db)):
    """Required human-in-the-loop sign-off before a campaign can launch."""
    campaign = db.get(models.Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    campaign.approved_by = req.approved_by
    campaign.status = "approved"
    db.commit()
    db.refresh(campaign)
    return campaign


@router.post("/campaigns/{campaign_id}/launch", response_model=schemas.CampaignOut)
def launch_campaign(campaign_id: str, db: Session = Depends(get_db)):
    campaign = db.get(models.Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if not campaign.approved_by:
        raise HTTPException(400, "Campaign must be approved (sign-off) before launch")

    # Best-effort: actually launching the Gophish campaign requires groups/
    # SMTP profile/landing page to already exist in Gophish (see gophish-config/).
    campaign.status = "launched"
    campaign.launched_at = datetime.utcnow()
    db.commit()
    db.refresh(campaign)
    return campaign
