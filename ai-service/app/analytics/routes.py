import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app import models, schemas

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/events")
def record_event(event: schemas.ClickEventIn, db: Session = Depends(get_db)):
    """
    Receives Gophish webhook-style events (sent / opened / clicked /
    submitted_data). Point Gophish's webhook feature (or a small relay script)
    at this endpoint, or call it directly from the dashboard for demo data.
    """
    row = models.ClickEvent(
        campaign_id=event.campaign_id,
        target_email=event.target_email,
        department=event.department,
        event_type=event.event_type,
    )
    db.add(row)
    db.commit()
    return {"status": "recorded", "id": row.id}


def _aggregate(db: Session):
    rows = db.query(
        models.ClickEvent.department,
        models.ClickEvent.event_type,
        func.count(models.ClickEvent.id),
    ).group_by(models.ClickEvent.department, models.ClickEvent.event_type).all()

    by_dept = {}
    for department, event_type, count in rows:
        d = by_dept.setdefault(department, {"sent": 0, "opened": 0, "clicked": 0, "submitted_data": 0})
        d[event_type] = d.get(event_type, 0) + count

    summary = []
    for department, counts in by_dept.items():
        sent = counts.get("sent", 0)
        clicked = counts.get("clicked", 0)
        click_rate = round((clicked / sent) * 100, 1) if sent else 0.0
        summary.append(schemas.AnalyticsSummaryRow(
            department=department,
            sent=sent,
            opened=counts.get("opened", 0),
            clicked=clicked,
            submitted_data=counts.get("submitted_data", 0),
            click_rate_pct=click_rate,
        ))
    return sorted(summary, key=lambda r: r.click_rate_pct, reverse=True)


@router.get("/summary", response_model=list[schemas.AnalyticsSummaryRow])
def analytics_summary(db: Session = Depends(get_db)):
    return _aggregate(db)


@router.get("/insights")
def analytics_insights(db: Session = Depends(get_db)):
    """
    Simple rule-based vulnerability insights (no ML needed). Swap/extend with
    an LLM-generated narrative summary later if you want prose instead of bullets.
    """
    summary = _aggregate(db)
    if not summary:
        return {"insights": ["No campaign data yet — launch a campaign to see insights."]}

    insights = []
    top = summary[0]
    if top.click_rate_pct > 0:
        insights.append(
            f"{top.department} has the highest click rate at {top.click_rate_pct}% "
            f"({top.clicked}/{top.sent} recipients clicked)."
        )
    if len(summary) > 1:
        gap = top.click_rate_pct - summary[-1].click_rate_pct
        if gap > 0:
            insights.append(
                f"{top.department} clicked at a rate {round(gap, 1)} points higher than "
                f"{summary[-1].department}, the most resilient department."
            )
    submitted = sum(r.submitted_data for r in summary)
    if submitted:
        insights.append(
            f"{submitted} recipient(s) went as far as submitting data on the landing page — "
            "prioritize follow-up training for these individuals."
        )
    return {"insights": insights}


@router.get("/export")
def analytics_export(db: Session = Depends(get_db)):
    summary = _aggregate(db)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["department", "sent", "opened", "clicked", "submitted_data", "click_rate_pct"])
    for r in summary:
        writer.writerow([r.department, r.sent, r.opened, r.clicked, r.submitted_data, r.click_rate_pct])
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analytics_export.csv"},
    )
