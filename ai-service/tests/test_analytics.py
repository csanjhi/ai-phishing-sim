def _make_campaign(client, department="HR"):
    tmpl = client.post("/templates/generate", json={
        "target_role": "HR Generalist", "department": department,
    }).json()
    campaign = client.post("/campaigns", json={
        "name": f"{department} Test", "template_id": tmpl["id"], "department": department,
    }).json()
    return campaign


def test_events_and_summary(client):
    campaign = _make_campaign(client, department="HR")
    events = [
        ("sent", "a@x.com"), ("sent", "b@x.com"), ("sent", "c@x.com"), ("sent", "d@x.com"),
        ("opened", "a@x.com"), ("opened", "b@x.com"),
        ("clicked", "a@x.com"),
        ("submitted_data", "a@x.com"),
    ]
    for event_type, email in events:
        resp = client.post("/analytics/events", json={
            "campaign_id": campaign["id"], "target_email": email,
            "department": "HR", "event_type": event_type,
        })
        assert resp.status_code == 200

    summary = client.get("/analytics/summary").json()
    hr_row = next(r for r in summary if r["department"] == "HR")
    assert hr_row["sent"] == 4
    assert hr_row["opened"] == 2
    assert hr_row["clicked"] == 1
    assert hr_row["submitted_data"] == 1
    assert hr_row["click_rate_pct"] == 25.0


def test_insights_mentions_top_department(client):
    insights = client.get("/analytics/insights").json()["insights"]
    assert isinstance(insights, list)
    assert len(insights) >= 1


def test_export_csv(client):
    resp = client.get("/analytics/export")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "department" in resp.text
