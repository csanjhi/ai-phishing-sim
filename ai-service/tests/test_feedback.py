def test_feedback_trigger_and_page(client):
    tmpl = client.post("/templates/generate", json={
        "target_role": "Accountant", "department": "Finance", "difficulty_level": "easy",
    }).json()
    campaign = client.post("/campaigns", json={
        "name": "Finance Test", "template_id": tmpl["id"], "department": "Finance",
    }).json()

    trigger = client.post("/feedback/trigger", json={
        "campaign_id": campaign["id"],
        "target_email": "clicked.user@demo.local",
        "target_role": "Accountant",
    })
    assert trigger.status_code == 200
    body = trigger.json()
    assert "token" in body

    page = client.get(f"/feedback/page/{body['token']}")
    assert page.status_code == 200
    assert "Simulated Phishing Exercise" in page.text

    # The trigger should also have logged a 'clicked' analytics event.
    summary = client.get("/analytics/summary").json()
    finance_row = next(r for r in summary if r["department"] == "Finance")
    assert finance_row["clicked"] >= 1


def test_feedback_page_404_for_unknown_token(client):
    resp = client.get("/feedback/page/does-not-exist")
    assert resp.status_code == 404
